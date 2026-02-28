"""
YOLO11 ONNX 测试脚本（优先面向 Ultralytics YOLO11 的导出格式）

目标：
- 只考虑 YOLO11 常见 ONNX 输出（4 + nc，不含 objectness）
- 支持图片推理：解析输出 + NMS + 绘框 + 保存 *_result
- 支持视频推理：跑若干帧做 smoke test（默认不绘框）

可插拔：
- 预留 YOLOv5 decoder 的“插拔式”入口（实现一个 Decoder 并注册即可）
"""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Protocol, Tuple


def _require(package: str, import_name: Optional[str] = None):
    """延迟导入依赖，缺失时给出清晰提示。"""
    try:
        return __import__(import_name or package)
    except Exception as e:
        raise RuntimeError(f"缺少依赖 {package}，请先安装：pip install {package}。原始错误：{e}") from e


@dataclass(frozen=True)
class SessionInfo:
    input_name: str
    input_hw: Tuple[int, int]  # (h, w)
    output_names: List[str]
    providers: List[str]


def create_onnx_session(model_path: str, device: str) -> tuple:
    """创建 onnxruntime session，并推断模型输入尺寸。"""
    ort = _require("onnxruntime")

    providers: List[str] = []
    if device.lower().startswith("cuda"):
        providers.append("CUDAExecutionProvider")
    providers.append("CPUExecutionProvider")

    sess = ort.InferenceSession(model_path, providers=providers)
    input_meta = sess.get_inputs()[0]

    # 推断输入尺寸：优先使用静态 shape，否则默认 640x640
    shape = input_meta.shape
    h, w = 640, 640
    if isinstance(shape, (list, tuple)) and len(shape) >= 4:
        maybe_h, maybe_w = shape[-2], shape[-1]
        if isinstance(maybe_h, int) and isinstance(maybe_w, int) and maybe_h > 0 and maybe_w > 0:
            h, w = int(maybe_h), int(maybe_w)

    info = SessionInfo(
        input_name=input_meta.name,
        input_hw=(h, w),
        output_names=[o.name for o in sess.get_outputs()],
        providers=sess.get_providers(),
    )
    return sess, info


def letterbox(img_bgr, new_shape: Tuple[int, int], color=(114, 114, 114)):
    """保持比例缩放 + padding 到指定尺寸。返回：(image, r, (pad_w, pad_h))"""
    cv2 = _require("opencv-python", "cv2")
    new_h, new_w = new_shape
    h, w = img_bgr.shape[:2]
    r = min(new_w / w, new_h / h)
    resized_w = int(round(w * r))
    resized_h = int(round(h * r))
    resized = cv2.resize(img_bgr, (resized_w, resized_h), interpolation=cv2.INTER_LINEAR)

    dw = (new_w - resized_w) / 2
    dh = (new_h - resized_h) / 2
    top = int(round(dh - 0.1))
    bottom = int(round(dh + 0.1))
    left = int(round(dw - 0.1))
    right = int(round(dw + 0.1))

    out = cv2.copyMakeBorder(resized, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
    return out, r, (left, top)


def preprocess_bgr_to_nchw_float(img_bgr, input_hw: Tuple[int, int]):
    """BGR(HWC uint8) -> NCHW float32(0-1)，并返回坐标反算参数。"""
    np = _require("numpy", "numpy")
    cv2 = _require("opencv-python", "cv2")

    lb, r, (pad_w, pad_h) = letterbox(img_bgr, input_hw)
    rgb = cv2.cvtColor(lb, cv2.COLOR_BGR2RGB)
    x = rgb.astype("float32") / 255.0
    x = np.transpose(x, (2, 0, 1))
    x = np.expand_dims(x, axis=0)
    return x, r, (pad_w, pad_h)


def xywh_to_xyxy(xywh):
    np = _require("numpy", "numpy")
    x, y, w, h = xywh[:, 0], xywh[:, 1], xywh[:, 2], xywh[:, 3]
    return np.stack([x - w / 2, y - h / 2, x + w / 2, y + h / 2], axis=1)


def nms_xyxy(boxes, scores, iou_thres: float):
    """纯 numpy NMS，返回保留索引。"""
    np = _require("numpy", "numpy")
    if boxes.size == 0:
        return []

    x1, y1, x2, y2 = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
    areas = (x2 - x1).clip(min=0) * (y2 - y1).clip(min=0)
    order = scores.argsort()[::-1]

    keep = []
    while order.size > 0:
        i = int(order[0])
        keep.append(i)
        if order.size == 1:
            break
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        w = (xx2 - xx1).clip(min=0)
        h = (yy2 - yy1).clip(min=0)
        inter = w * h
        iou = inter / (areas[i] + areas[order[1:]] - inter + 1e-9)
        inds = np.where(iou <= iou_thres)[0]
        order = order[inds + 1]

    return keep


@dataclass(frozen=True)
class Detections:
    boxes_xyxy: "object"  # np.ndarray [N,4]
    scores: "object"  # np.ndarray [N]
    class_ids: "object"  # np.ndarray [N]


class Decoder(Protocol):
    """输出解码器接口：把 onnx 输出 -> (boxes,scores,class_ids)。"""

    def decode(self, outputs, input_hw: Tuple[int, int], conf_thres: float, iou_thres: float) -> Detections: ...


class Yolo11Decoder:
    """
    YOLO11（Ultralytics）常见 ONNX 输出解码：
    - 输出通常是 [1, (4+nc), num] 或 [1, num, (4+nc)]
    - 其中前 4 维是 xywh，其余是每类分数（无 objectness）
    """

    def decode(self, outputs, input_hw: Tuple[int, int], conf_thres: float, iou_thres: float) -> Detections:
        np = _require("numpy", "numpy")
        in_h, in_w = input_hw

        if not outputs:
            return Detections(np.zeros((0, 4), np.float32), np.zeros((0,), np.float32), np.zeros((0,), np.int64))

        arr = np.array(outputs[0])
        if arr.ndim == 3 and arr.shape[0] == 1:
            arr = arr[0]

        # 统一成 [num, dim]
        if arr.ndim != 2:
            raise RuntimeError(f"YOLO11 输出维度不符合预期: {arr.shape}")
        if arr.shape[0] < arr.shape[1] and arr.shape[0] <= 300 and arr.shape[1] >= 300:
            arr = arr.T

        num, dim = arr.shape
        if dim <= 4:
            raise RuntimeError(f"YOLO11 输出 dim 太小: {arr.shape}")

        boxes_xywh = arr[:, 0:4].astype(np.float32)
        cls_scores = arr[:, 4:].astype(np.float32)  # [num, nc]

        class_ids = cls_scores.argmax(axis=1).astype(np.int64)
        scores = cls_scores.max(axis=1).astype(np.float32)

        mask = scores >= conf_thres
        if mask.sum() == 0:
            return Detections(np.zeros((0, 4), np.float32), np.zeros((0,), np.float32), np.zeros((0,), np.int64))

        boxes_xyxy = xywh_to_xyxy(boxes_xywh[mask])
        scores = scores[mask]
        class_ids = class_ids[mask]

        # 有些导出会输出归一化坐标（0~1），这里自动识别并还原
        if boxes_xyxy.size > 0 and float(boxes_xyxy.max()) <= 2.0:
            boxes_xyxy[:, [0, 2]] *= float(in_w)
            boxes_xyxy[:, [1, 3]] *= float(in_h)

        keep = nms_xyxy(boxes_xyxy, scores, iou_thres=iou_thres)
        return Detections(boxes_xyxy[keep], scores[keep], class_ids[keep])


class Yolo5Decoder:
    """预留：YOLOv5 输出解码器（目前不实现，后续可插拔添加）。"""

    def decode(self, outputs, input_hw: Tuple[int, int], conf_thres: float, iou_thres: float) -> Detections:
        raise NotImplementedError("YOLOv5 decoder 尚未实现（已预留插拔式接口）。")


DECODERS: Dict[str, Decoder] = {
    "yolo11": Yolo11Decoder(),
    # "yolo5": Yolo5Decoder(),  # 预留：未来实现后取消注释即可
}


def draw_boxes(img_bgr, det: Detections):
    cv2 = _require("opencv-python", "cv2")
    for (x1, y1, x2, y2), score, cid in zip(det.boxes_xyxy, det.scores, det.class_ids):
        x1i, y1i, x2i, y2i = int(round(x1)), int(round(y1)), int(round(x2)), int(round(y2))
        color = (0, 255, 0) if int(cid) == 0 else (255, 128, 0)
        cv2.rectangle(img_bgr, (x1i, y1i), (x2i, y2i), color, 2)
        cv2.putText(
            img_bgr,
            f"id={int(cid)} {float(score):.2f}",
            (x1i, max(0, y1i - 6)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2,
        )
    return img_bgr


def imwrite(path: Path, img_bgr) -> bool:
    cv2 = _require("opencv-python", "cv2")
    suffix = path.suffix.lower()
    if suffix == ".png":
        return cv2.imwrite(str(path), img_bgr, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    if suffix in (".jpg", ".jpeg"):
        return cv2.imwrite(str(path), img_bgr, [cv2.IMWRITE_JPEG_QUALITY, 95])
    return cv2.imwrite(str(path), img_bgr)


def test_image(
    model_path: str,
    image_path: str,
    decoder_name: str = "yolo11",
    device: str = "cpu",
    conf_thres: float = 0.25,
    iou_thres: float = 0.45,
):
    cv2 = _require("opencv-python", "cv2")
    np = _require("numpy", "numpy")

    sess, info = create_onnx_session(model_path, device=device)
    print(f"[onnx] providers={info.providers}")
    print(f"[onnx] input_name={info.input_name}, input_hw={info.input_hw}, outputs={info.output_names}")
    print(f"[decode] decoder={decoder_name}")

    dec = DECODERS.get(decoder_name)
    if dec is None:
        raise ValueError(f"未知 decoder: {decoder_name}，可选：{list(DECODERS.keys())}")

    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"读取图片失败：{image_path}")

    x, r, (pad_w, pad_h) = preprocess_bgr_to_nchw_float(img, info.input_hw)

    t0 = time.perf_counter()
    outputs = sess.run(info.output_names, {info.input_name: x})
    dt_ms = (time.perf_counter() - t0) * 1000.0
    print(f"[image] infer_time_ms={dt_ms:.2f}")

    for i, out in enumerate(outputs):
        try:
            shape = tuple(out.shape)
            dtype = str(out.dtype)
        except Exception:
            shape = "?"
            dtype = "?"
        print(f"[image] output[{i}] name={info.output_names[i]} shape={shape} dtype={dtype}")

    det = dec.decode(outputs, input_hw=info.input_hw, conf_thres=conf_thres, iou_thres=iou_thres)
    print(f"[image] decoded_boxes={int(det.boxes_xyxy.shape[0])} (conf>={conf_thres}, iou={iou_thres})")

    # 坐标从输入尺度映射回原图尺度（去 padding、除缩放）
    boxes = det.boxes_xyxy
    if boxes.size > 0:
        boxes = boxes.copy()
        boxes[:, [0, 2]] -= float(pad_w)
        boxes[:, [1, 3]] -= float(pad_h)
        boxes /= float(r)

        h0, w0 = img.shape[:2]
        boxes[:, [0, 2]] = np.clip(boxes[:, [0, 2]], 0, w0 - 1)
        boxes[:, [1, 3]] = np.clip(boxes[:, [1, 3]], 0, h0 - 1)

        det = Detections(boxes, det.scores, det.class_ids)

    out_img = draw_boxes(img.copy(), det)

    in_path = Path(image_path)
    out_path = in_path.with_name(f"{in_path.stem}_result{in_path.suffix}")
    if not imwrite(out_path, out_img):
        raise RuntimeError(f"保存结果图片失败：{out_path}")
    print(f"[image] saved: {out_path}")


def test_video(
    model_path: str,
    video_path: str,
    decoder_name: str = "yolo11",
    device: str = "cpu",
    max_frames: int = 30,
    sample_every: int = 1,
):
    cv2 = _require("opencv-python", "cv2")

    sess, info = create_onnx_session(model_path, device=device)
    print(f"[onnx] providers={info.providers}")
    print(f"[onnx] input_name={info.input_name}, input_hw={info.input_hw}, outputs={info.output_names}")
    print(f"[decode] decoder={decoder_name} (video mode: smoke test only)")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"打开视频失败：{video_path}")

    infer_ms_total = 0.0
    infer_count = 0
    read_count = 0
    t_start = time.perf_counter()

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        read_count += 1
        if sample_every > 1 and (read_count % sample_every) != 0:
            continue

        x, _, _ = preprocess_bgr_to_nchw_float(frame, info.input_hw)
        t0 = time.perf_counter()
        outputs = sess.run(info.output_names, {info.input_name: x})
        dt_ms = (time.perf_counter() - t0) * 1000.0

        infer_ms_total += dt_ms
        infer_count += 1

        if infer_count == 1:
            for i, out in enumerate(outputs):
                try:
                    shape = tuple(out.shape)
                    dtype = str(out.dtype)
                except Exception:
                    shape = "?"
                    dtype = "?"
                print(f"[video] output[{i}] name={info.output_names[i]} shape={shape} dtype={dtype}")

        if infer_count >= max_frames:
            break

    cap.release()
    t_total = time.perf_counter() - t_start
    avg_ms = infer_ms_total / max(infer_count, 1)
    fps = 1000.0 / avg_ms if avg_ms > 0 else 0.0
    print(f"[video] ok: {video_path}")
    print(f"[video] frames_infered={infer_count}, frames_read={read_count}, total_time_s={t_total:.2f}")
    print(f"[video] avg_infer_ms={avg_ms:.2f}, approx_fps={fps:.2f}")


def main():
    parser = argparse.ArgumentParser(description="YOLO11 ONNX test (image/video) via onnxruntime")
    parser.add_argument("--model", required=True, help="ONNX 模型路径，例如 G:\\ai\\models\\yolo\\yolo11n.onnx")
    parser.add_argument("--device", default="cpu", help="cpu 或 cuda:0（如果装了 onnxruntime-gpu）")
    parser.add_argument("--decoder", default="yolo11", choices=list(DECODERS.keys()), help="输出解码器（默认 yolo11）")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--image", help="测试图片路径（会输出 *_result）")
    group.add_argument("--video", help="测试视频路径（性能 smoke test）")

    parser.add_argument("--conf", type=float, default=0.25, help="置信度阈值（图片模式）")
    parser.add_argument("--iou", type=float, default=0.45, help="NMS IoU 阈值（图片模式）")
    parser.add_argument("--max-frames", type=int, default=30, help="视频最多推理多少帧")
    parser.add_argument("--sample-every", type=int, default=1, help="视频每隔多少帧推理一次（1=每帧）")

    args = parser.parse_args()
    if args.image:
        test_image(
            args.model,
            args.image,
            decoder_name=args.decoder,
            device=args.device,
            conf_thres=args.conf,
            iou_thres=args.iou,
        )
    else:
        test_video(
            args.model,
            args.video,
            decoder_name=args.decoder,
            device=args.device,
            max_frames=args.max_frames,
            sample_every=args.sample_every,
        )


if __name__ == "__main__":
    main()

