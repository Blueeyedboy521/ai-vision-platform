import argparse  # 命令行参数解析（让你可以传入 model/image/video 等参数）
import time  # 计时：统计单次推理耗时、视频整体耗时等
from dataclasses import dataclass  # 用 dataclass 保存 session 元信息，写起来更清晰
from pathlib import Path  # 处理文件路径（拼接、改名、取后缀等）
from typing import Optional, Tuple  # 类型标注：可读性更好

# 引入日志
from loguru import logger

@dataclass(frozen=True)  # frozen=True 表示对象不可变，避免被误改（更安全）
class SessionInfo:  # 保存 ONNX session 的关键信息，避免到处重复读取
    input_name: str  # ONNX 输入 tensor 名字（session.run 时要用）
    input_hw: Tuple[int, int]  # 输入尺寸 (h, w)，用于预处理 resize/letterbox
    output_names: list  # 输出 tensor 名字列表（session.run 会按这些返回）
    providers: list  # 实际启用的执行提供者（CPU/CUDA），用于确认是否用上 GPU


def _require(package: str, import_name: Optional[str] = None):  # 统一的依赖导入：缺啥就给出明确提示
    try:  # 捕获 import 失败并转换成更友好的错误信息
        return __import__(import_name or package)  # __import__ 返回模块对象
    except Exception as e:  # 任意导入异常都统一提示安装方式
        raise RuntimeError(f"缺少依赖 {package}，请先安装：pip install {package}。原始错误：{e}") from e  # 抛出可读错误


def _create_session(model_path: str, device: str) -> tuple:  # 创建 onnxruntime session，并推断输入尺寸
    ort = _require("onnxruntime")  # 延迟导入 onnxruntime（未安装时提示更友好）

    providers = []  # 这里构造 providers 优先级列表：如果有 GPU 就先用 GPU
    if device.lower().startswith("cuda"):  # 只要传入 cuda:0/cuda 等，就尝试启用 CUDA provider
        providers.append("CUDAExecutionProvider")  # GPU 推理（需要 onnxruntime-gpu + CUDA/cuDNN）
    providers.append("CPUExecutionProvider")  # 始终加 CPU：GPU 不可用时自动回退

    sess = ort.InferenceSession(model_path, providers=providers)  # 创建推理会话（会加载/编译模型）
    input_meta = sess.get_inputs()[0]  # 取第一个输入（YOLO 一般只有一个输入：图像）

    # 推断输入尺寸：优先使用静态 shape，否则默认 640x640（多数 YOLO 导出常用 640）
    shape = input_meta.shape  # 常见形态：[1,3,640,640]（固定）或 [1,3,'height','width']（动态）
    h = 640  # 默认输入高（当模型是动态输入、无法从 shape 得到具体数值时使用）
    w = 640  # 默认输入宽
    if isinstance(shape, (list, tuple)) and len(shape) >= 4:  # shape 至少包含 NCHW 四个维度
        maybe_h = shape[-2]  # NCHW 的 H
        maybe_w = shape[-1]  # NCHW 的 W
        if isinstance(maybe_h, int) and isinstance(maybe_w, int) and maybe_h > 0 and maybe_w > 0:  # 如果是静态整数尺寸
            h, w = int(maybe_h), int(maybe_w)  # 使用模型的真实输入尺寸，避免喂错 shape

    info = SessionInfo(  # 把关键信息封装起来，后面用起来更方便
        input_name=input_meta.name,  # 输入名：喂数据时需要这个 key
        input_hw=(h, w),  # 输入高宽：用于 letterbox
        output_names=[o.name for o in sess.get_outputs()],  # 输出名列表：用于 sess.run
        providers=sess.get_providers(),  # 实际启用 provider（比传入 providers 更准确）
    )  # SessionInfo 构造结束
    logger.info(f"创建 ONNX session 成功: {model_path}，输入名: {input_meta.name}，输入高宽: {h}x{w}，输出名: {sess.get_outputs()[0].name}，实际启用 provider: {sess.get_providers()}")
    return sess, info  # 返回 session 和其元信息


def _letterbox(img_bgr, new_shape: Tuple[int, int], color=(114, 114, 114)):  # YOLO 常用 letterbox 预处理：等比例缩放+补边
    """
    Ultralytics 风格 letterbox：保持比例缩放 + padding 到指定尺寸。  # 解释：保持纵横比，避免拉伸导致检测变差
    返回：处理后的图、缩放比 r、padding (dw, dh)  # r 用于坐标反算；padding 用于去掉黑边
    """  # docstring 结束（便于 IDE/帮助文档查看）
    cv2 = _require("opencv-python", "cv2")  # 延迟导入 cv2：只有用到时才需要安装

    new_h, new_w = new_shape  # 目标尺寸（模型输入尺寸）
    h, w = img_bgr.shape[:2]  # 原图尺寸
    r = min(new_w / w, new_h / h)  # 缩放比例：按较小边缩放，保证缩放后能完全塞进目标尺寸
    resized_w = int(round(w * r))  # 缩放后的宽
    resized_h = int(round(h * r))  # 缩放后的高

    resized = cv2.resize(img_bgr, (resized_w, resized_h), interpolation=cv2.INTER_LINEAR)  # 等比例 resize（不改变纵横比）

    dw = new_w - resized_w  # 需要补的总宽度（padding）
    dh = new_h - resized_h  # 需要补的总高度
    dw /= 2  # 左右各补一半
    dh /= 2  # 上下各补一半

    top = int(round(dh - 0.1))  # 上边 padding（-0.1/+0.1 是为了 round 后上下能凑齐总量）
    bottom = int(round(dh + 0.1))  # 下边 padding
    left = int(round(dw - 0.1))  # 左边 padding
    right = int(round(dw + 0.1))  # 右边 padding
    logger.info(f"letterbox: resized_w={resized_w}, resized_h={resized_h}, new_w={new_w}, new_h={new_h}, top={top}, bottom={bottom}, left={left}, right={right}")
    out = cv2.copyMakeBorder(resized, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)  # 用常见的 114 灰色补边
    return out, r, (left, top)  # 返回 padding 的左/上（用于把预测框坐标映射回原图）


def _preprocess_bgr_to_nchw_float(img_bgr, input_hw: Tuple[int, int]):  # 预处理：BGR(HWC uint8) -> NCHW float32(0-1)
    np = _require("numpy", "numpy")  # numpy：做 transpose/expand_dims
    cv2 = _require("opencv-python", "cv2")  # cv2：做颜色转换

    lb, r, (pad_w, pad_h) = _letterbox(img_bgr, input_hw)  # 先 letterbox 到模型输入大小，并得到缩放/补边信息
    rgb = cv2.cvtColor(lb, cv2.COLOR_BGR2RGB)  # YOLO/Ultralytics 通常用 RGB 顺序（而 OpenCV 读入是 BGR）
    x = rgb.astype("float32") / 255.0  # 归一化到 0-1（大多数 YOLO 导出 ONNX 期望这样）
    x = np.transpose(x, (2, 0, 1))  # HWC -> CHW（ONNX 模型一般是 NCHW）
    x = np.expand_dims(x, axis=0)  # CHW -> NCHW（batch=1）
    return x, r, (pad_w, pad_h)  # 返回 input tensor + 坐标反算所需参数


def _xywh_to_xyxy(xywh):  # 把 (center_x,center_y,width,height) 转成 (x1,y1,x2,y2)，NMS/画框更常用后者
    np = _require("numpy", "numpy")  # numpy：用于 stack
    x = xywh[:, 0]  # 中心点 x
    y = xywh[:, 1]  # 中心点 y
    w = xywh[:, 2]  # 宽
    h = xywh[:, 3]  # 高
    x1 = x - w / 2  # 左上角 x
    y1 = y - h / 2  # 左上角 y
    x2 = x + w / 2  # 右下角 x
    y2 = y + h / 2  # 右下角 y
    return np.stack([x1, y1, x2, y2], axis=1)  # 拼成 [N,4]


def _nms_xyxy(boxes, scores, iou_thres: float):  # 标准 NMS：按分数从高到低，移除 IoU 重叠过大的框
    np = _require("numpy", "numpy")  # numpy：做排序/向量化 IoU
    if boxes.size == 0:  # 没有候选框就直接返回空
        return []  # 返回保留索引列表

    x1 = boxes[:, 0]  # 所有框的 x1
    y1 = boxes[:, 1]  # 所有框的 y1
    x2 = boxes[:, 2]  # 所有框的 x2
    y2 = boxes[:, 3]  # 所有框的 y2
    areas = (x2 - x1).clip(min=0) * (y2 - y1).clip(min=0)  # 每个框面积（用于 IoU）
    order = scores.argsort()[::-1]  # 按分数降序排序后的索引

    keep = []  # 最终保留下来的框索引
    while order.size > 0:  # 只要还有候选框就继续
        i = int(order[0])  # 当前最高分框索引
        keep.append(i)  # 保留该框
        if order.size == 1:  # 只剩一个框则结束
            break  # 跳出循环
        xx1 = np.maximum(x1[i], x1[order[1:]])  # 与其余框的交集左上角 x
        yy1 = np.maximum(y1[i], y1[order[1:]])  # 与其余框的交集左上角 y
        xx2 = np.minimum(x2[i], x2[order[1:]])  # 与其余框的交集右下角 x
        yy2 = np.minimum(y2[i], y2[order[1:]])  # 与其余框的交集右下角 y

        w = (xx2 - xx1).clip(min=0)  # 交集宽（小于 0 置 0）
        h = (yy2 - yy1).clip(min=0)  # 交集高
        inter = w * h  # 交集面积
        iou = inter / (areas[i] + areas[order[1:]] - inter + 1e-9)  # IoU = inter/union（+1e-9 防止除 0）
        inds = np.where(iou <= iou_thres)[0]  # 保留 IoU 小于阈值的框（与当前框不算重复）
        order = order[inds + 1]  # +1 是因为 inds 是针对 order[1:] 的偏移

    return keep  # 返回保留索引


def _decode_yolo_onnx_outputs(
    outputs,
    input_hw: Tuple[int, int],
    conf_thres: float = 0.25,
    iou_thres: float = 0.45,
):
    """
    兼容两类常见 YOLO ONNX 输出：
    - 已带 NMS：[..., 6] = (x1,y1,x2,y2,score,class_id)
    - 未带 NMS（Ultralytics 常见）：[1, (4+nc), num] 或 [1, num, (4+nc)] 或 YOLOv5 风格 [1,num,(5+nc)]
    返回：boxes_xyxy(float), scores(float), class_ids(int)
    """
    np = _require("numpy", "numpy")  # numpy：用于把输出转换成数组并做向量化计算

    if not outputs:  # session.run 没有返回任何输出（异常情况）
        return np.zeros((0, 4), dtype=np.float32), np.zeros((0,), dtype=np.float32), np.zeros((0,), dtype=np.int64)  # 返回空检测

    in_h, in_w = input_hw  # 输入尺寸：用于把归一化坐标还原到像素坐标
    out0 = outputs[0]  # 只取第一个输出（大多数 YOLO ONNX 只有一个主输出）
    arr = np.array(out0)  # 转成 numpy 数组，便于统一处理

    # 1) 如果输出已经是 NMS 后的 [N,6] 或 [1,N,6]
    if arr.ndim == 3 and arr.shape[-1] == 6:  # 形如 [1,N,6]（已做 NMS）
        arr = arr[0]  # 去掉 batch 维度
    if arr.ndim == 2 and arr.shape[1] == 6:  # 形如 [N,6]（已做 NMS）
        boxes = arr[:, 0:4].astype(np.float32)  # x1y1x2y2
        scores = arr[:, 4].astype(np.float32)  # 置信度
        class_ids = arr[:, 5].astype(np.int64)  # 类别 id
        m = scores >= conf_thres  # 按置信度过滤
        return boxes[m], scores[m], class_ids[m]  # 直接返回（无需再做 NMS）

    # 2) 处理未 NMS 的输出
    # 统一成 [num, dim]
    if arr.ndim == 3 and arr.shape[0] == 1:  # 形如 [1,dim,num] 或 [1,num,dim]
        arr = arr[0]  # 去掉 batch
    if arr.ndim == 2:  # 已经是 2 维，不需要处理
        pass  # 占位：保持结构清晰
    elif arr.ndim == 3:  # 仍然是 3 维（不常见），做一次展平兜底
        arr = arr.reshape(arr.shape[0], -1)  # 粗暴拉平：只用于兜底，不保证适配所有模型
    else:  # 其它维度说明输出结构不在预期中
        raise RuntimeError(f"无法识别的输出维度: {arr.shape}")  # 提示输出 shape 便于你排查

    # arr 可能是 [dim, num]，也可能是 [num, dim]
    # 常见：dim 很小（例如 84/85/116），num 很大（例如 8400）
    if arr.shape[0] < arr.shape[1] and arr.shape[0] <= 300 and arr.shape[1] >= 300:  # 常见：[dim,num]（dim 小、num 大）
        arr = arr.T  # 转成 [num,dim] 统一处理

    num, dim = arr.shape[0], arr.shape[1]  # num=候选框数量，dim=每个候选的特征维度
    if dim < 6:  # 至少要有 4 个 box + 1 个分数 + 1 个类别（或更多）
        raise RuntimeError(f"输出维度过小，无法解析: {arr.shape}")  # 提示你模型输出格式可能不同

    # YOLOv5: 4 + 1(obj) + nc
    # Ultralytics YOLOv8/11: 4 + nc（无 obj）
    boxes_xywh = arr[:, 0:4].astype(np.float32)  # 前 4 维按惯例认为是 xywh
    rest = arr[:, 4:].astype(np.float32)  # 剩余维度：可能是 cls（v8/v11）或 obj+cls（v5）

    def _decode_as_yolov8():  # Ultralytics YOLOv8/11：输出为 4 + nc（不含 obj）
        cls_probs = rest  # rest 全部当作类别概率/分数
        cls_id = cls_probs.argmax(axis=1)  # 每个候选框取最大类别的 id
        scores = cls_probs.max(axis=1)  # 最大类别对应的分数
        return cls_id.astype(np.int64), scores.astype(np.float32)  # 返回类别 id 和分数

    def _decode_as_yolov5():  # YOLOv5 风格：输出为 4 + 1(obj) + nc
        obj = rest[:, 0]  # objectness（是否有物体）
        cls_probs = rest[:, 1:]  # 各类别分数
        if cls_probs.shape[1] >= 1:  # 确保存在类别维度
            cls_id = cls_probs.argmax(axis=1)  # 最大类别 id
            cls_score = cls_probs.max(axis=1)  # 最大类别分数
            scores = obj * cls_score  # 最终置信度通常按 obj * cls
            return cls_id.astype(np.int64), scores.astype(np.float32)  # 返回类别与分数
        cls_id = np.zeros((num,), dtype=np.int64)  # 没有类别维度时，全部置 0 类
        return cls_id, obj.astype(np.float32)  # 只有 objectness 可用

    # 先分别按 v8/v5 两种方式解码，取“能得到更多候选框”的那种（防止格式误判导致全被过滤）
    cls_id_v8, scores_v8 = _decode_as_yolov8()  # 按 v8/v11 方式解码一份
    cls_id_v5, scores_v5 = _decode_as_yolov5()  # 按 v5 方式解码一份

    def _select(boxes_xywh_all, cls_id_all, scores_all):  # 将某一种解码方式的结果做阈值过滤 + NMS
        mask = scores_all >= conf_thres  # 置信度过滤（先粗过滤，减少 NMS 计算量）
        if mask.sum() == 0:  # 全部被过滤掉则直接返回空
            return np.zeros((0, 4), dtype=np.float32), np.zeros((0,), dtype=np.float32), np.zeros((0,), dtype=np.int64)  # 空结果

        boxes_xyxy = _xywh_to_xyxy(boxes_xywh_all[mask])  # xywh -> xyxy（NMS 需要 xyxy）

        # 某些导出会把坐标归一化到 0~1，这里做一次自动识别并还原到输入尺寸
        if boxes_xyxy.size > 0 and float(boxes_xyxy.max()) <= 2.0:  # 如果最大值很小，认为是归一化坐标
            boxes_xyxy[:, [0, 2]] *= float(in_w)  # x 方向乘以输入宽
            boxes_xyxy[:, [1, 3]] *= float(in_h)  # y 方向乘以输入高

        scores = scores_all[mask]  # 过滤后的分数
        cls_id = cls_id_all[mask].astype(np.int64)  # 过滤后的类别 id
        keep = _nms_xyxy(boxes_xyxy, scores, iou_thres=iou_thres)  # 进行 NMS 去重
        return boxes_xyxy[keep], scores[keep], cls_id[keep]  # 返回 NMS 后的框、分数、类别

    boxes8, scores8, ids8 = _select(boxes_xywh, cls_id_v8, scores_v8)  # v8/v11 解码 + NMS 后的结果
    boxes5, scores5, ids5 = _select(boxes_xywh, cls_id_v5, scores_v5)  # v5 解码 + NMS 后的结果

    if boxes8.shape[0] > boxes5.shape[0]:  # 哪种解码得到的框更多，通常说明那种更匹配模型输出
        return boxes8, scores8, ids8  # 返回 v8/v11 版本
    if boxes5.shape[0] > boxes8.shape[0]:  # v5 得到更多框
        return boxes5, scores5, ids5  # 返回 v5 版本
    # 数量相同则取总分更高的（当两者都能解析出相同数量时，用分数和做启发式选择）
    if float(scores5.sum()) > float(scores8.sum()):  # v5 总分更大
        return boxes5, scores5, ids5  # 返回 v5 结果
    return boxes8, scores8, ids8  # 否则默认返回 v8/v11 结果


def _draw_boxes(img_bgr, boxes_xyxy, scores, class_ids):  # 画框：把检测结果可视化到图片上
    cv2 = _require("opencv-python", "cv2")  # 画图依赖 cv2
    for (x1, y1, x2, y2), score, cid in zip(boxes_xyxy, scores, class_ids):  # 遍历每个检测框
        x1i, y1i, x2i, y2i = int(round(x1)), int(round(y1)), int(round(x2)), int(round(y2))  # float 坐标转 int 像素
        is_person = int(cid) == 0  # COCO 数据集里 person=0（很多 YOLO 默认就是 COCO 类别顺序）
        color = (0, 255, 0) if is_person else (255, 128, 0)  # person 用绿色，其它类别用橙色，便于区分
        cv2.rectangle(img_bgr, (x1i, y1i), (x2i, y2i), color, 2)  # 画矩形框
        label = f"id={int(cid)} {float(score):.2f}"  # 标签：类别 id + 分数（这里不做中文类名映射）
        cv2.putText(img_bgr, label, (x1i, max(0, y1i - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)  # 在框上方写文字
    return img_bgr  # 返回画好框的图


def _imwrite(path: Path, img_bgr) -> bool:  # 保存图片：针对 PNG/JPG 设置合适的编码参数，避免文件变大
    cv2 = _require("opencv-python", "cv2")  # 写文件依赖 cv2
    suffix = path.suffix.lower()  # 后缀名（决定编码参数）
    if suffix == ".png":  # PNG 是无损压缩，压缩级别影响体积/速度
        # 0-9，越大压缩率越高/文件越小/更慢
        return cv2.imwrite(str(path), img_bgr, [cv2.IMWRITE_PNG_COMPRESSION, 9])  # 用最高压缩减小体积
    if suffix in (".jpg", ".jpeg"):  # JPG 是有损压缩，用 quality 控制
        return cv2.imwrite(str(path), img_bgr, [cv2.IMWRITE_JPEG_QUALITY, 95])  # 95 兼顾质量与体积
    return cv2.imwrite(str(path), img_bgr)  # 其它格式用默认参数


def test_image(
    model_path: str,
    image_path: str,
    device: str = "cpu",
    conf_thres: float = 0.25,
    iou_thres: float = 0.45,
):
    """
    测试图片推理：验证 onnxruntime 是否可加载并执行一次推理，并把检测框画到图片保存为 *_result。  # 目的：既验证可跑通，也验证输出解析正确
    """  # docstring 结束
    cv2 = _require("opencv-python", "cv2")  # 读图/写图/画框
    np = _require("numpy", "numpy")  # clip/数组运算等

    sess, info = _create_session(model_path, device=device)  # 创建 ONNX session（并推断输入尺寸）
    logger.info(f"[onnx] providers={info.providers}")  # 打印实际 provider，确认是否走 CPU/GPU
    logger.info(f"[onnx] input_name={info.input_name}, input_hw={info.input_hw}, outputs={info.output_names}")  # 打印输入输出信息，便于排查

    img = cv2.imread(image_path)  # 读取图片（BGR）
    if img is None:  # 读取失败通常是路径错/文件损坏/权限问题
        raise FileNotFoundError(f"读取图片失败：{image_path}")  # 直接抛错，避免后续 None 引发更隐蔽错误

    x, r, (pad_w, pad_h) = _preprocess_bgr_to_nchw_float(img, info.input_hw)  # 预处理得到输入 tensor + 坐标反算参数

    t0 = time.perf_counter()  # 高精度计时起点
    outputs = sess.run(info.output_names, {info.input_name: x})  # 执行推理：输入名 -> 输入 tensor
    dt_ms = (time.perf_counter() - t0) * 1000.0  # 计算推理耗时（毫秒）

    logger.info(f"[image] ok: {image_path}")  # 打印输入图片路径
    logger.info(f"[image] infer_time_ms={dt_ms:.2f}")  # 打印单次推理耗时
    for i, out in enumerate(outputs):  # 逐个输出打印 shape/dtype，方便确认输出结构
        try:  # 某些输出可能不是 numpy array，这里做容错
            shape = tuple(out.shape)  # 输出 shape
            dtype = str(out.dtype)  # 输出 dtype
        except Exception:  # 无法读取 shape/dtype 就用占位符
            shape = "?"  # 占位 shape
            dtype = "?"  # 占位 dtype
        logger.info(f"[image] output[{i}] name={info.output_names[i]} shape={shape} dtype={dtype}")  # 输出元信息

    boxes, scores, class_ids = _decode_yolo_onnx_outputs(  # 解析 YOLO 输出 -> 候选框/分数/类别，并做 NMS
        outputs,  # session.run 的输出列表
        input_hw=info.input_hw,  # 模型输入尺寸（用于坐标反归一化）
        conf_thres=conf_thres,  # 置信度阈值
        iou_thres=iou_thres,  # NMS IoU 阈值
    )  # decode 结束
    logger.info(f"[image] decoded_boxes={int(boxes.shape[0])} (conf>={conf_thres}, iou={iou_thres})")  # 打印最终保留的框数量

    # 将 box 从 letterbox 坐标映射回原图坐标
    if boxes.size > 0:  # 如果有检测框，才需要做坐标映射
        boxes = boxes.copy()  # copy 一份，避免修改原数组（更安全）
        boxes[:, [0, 2]] -= float(pad_w)  # 去掉 letterbox 的左右 padding（把坐标移回到 resize 后图的坐标系）
        boxes[:, [1, 3]] -= float(pad_h)  # 去掉上下 padding
        boxes /= float(r)  # 反除缩放比例，把坐标映射回原图尺寸

        h0, w0 = img.shape[:2]  # 原图高宽
        boxes[:, [0, 2]] = np.clip(boxes[:, [0, 2]], 0, w0 - 1)  # x 坐标裁剪到图像范围内
        boxes[:, [1, 3]] = np.clip(boxes[:, [1, 3]], 0, h0 - 1)  # y 坐标裁剪到图像范围内

    drawn = img.copy()  # 复制一份原图用于绘制（避免破坏原图数据）
    drawn = _draw_boxes(drawn, boxes, scores, class_ids)  # 把框画到图片上

    in_path = Path(image_path)  # 原图路径对象
    out_path = in_path.with_name(f"{in_path.stem}_result{in_path.suffix}")  # 输出路径：同目录，文件名加 _result
    ok = _imwrite(out_path, drawn)  # 保存图片（PNG 用高压缩，减少体积）
    if not ok:  # cv2.imwrite 失败会返回 False
        raise RuntimeError(f"保存结果图片失败：{out_path}")  # 抛错提示具体输出路径
    logger.info(f"[image] saved: {out_path}")  # 打印输出文件位置


def test_video(
    model_path: str,
    video_path: str,
    device: str = "cpu",
    max_frames: int = 30,
    sample_every: int = 1,
):
    """
    测试视频推理：循环读取视频帧并推理，用于验证稳定性与大致性能。  # 这里不画框，只做性能 smoke test
    """  # docstring 结束
    cv2 = _require("opencv-python", "cv2")  # 读取视频帧依赖 OpenCV

    sess, info = _create_session(model_path, device=device)  # 创建 ONNX session
    print(f"[onnx] providers={info.providers}")  # 打印 provider
    print(f"[onnx] input_name={info.input_name}, input_hw={info.input_hw}, outputs={info.output_names}")  # 打印输入输出信息

    cap = cv2.VideoCapture(video_path)  # 打开视频文件/流
    if not cap.isOpened():  # 打开失败说明路径错误或编码/权限问题
        raise FileNotFoundError(f"打开视频失败：{video_path}")  # 抛错便于定位

    infer_ms_total = 0.0  # 累计推理耗时（ms）
    infer_count = 0  # 实际推理的帧数（考虑 sample_every）
    read_count = 0  # 实际读取的帧数（每 read 一次 +1）

    t_start = time.perf_counter()  # 视频测试起始时间
    while True:  # 逐帧读取
        ok, frame = cap.read()  # 读取一帧
        if not ok:  # 读不到帧说明结束或出错
            break  # 退出循环

        read_count += 1  # 记录读取到的帧数
        if sample_every > 1 and (read_count % sample_every) != 0:  # 抽帧：不是要推理的帧就跳过
            continue  # 继续读下一帧

        x, _, _ = _preprocess_bgr_to_nchw_float(frame, info.input_hw)  # 预处理（视频不需要反算坐标，所以忽略 r/pad）

        t0 = time.perf_counter()  # 单帧计时起点
        outputs = sess.run(info.output_names, {info.input_name: x})  # 执行推理（这里只用于耗时统计）
        dt_ms = (time.perf_counter() - t0) * 1000.0  # 单帧推理耗时 ms

        infer_ms_total += dt_ms  # 累加耗时
        infer_count += 1  # 计数 +1

        if infer_count == 1:  # 第一帧额外打印输出信息，确认输出结构
            # 第一帧打印一次输出信息
            for i, out in enumerate(outputs):  # 遍历输出
                try:  # 容错：有些输出类型可能不带 shape/dtype
                    shape = tuple(out.shape)  # 输出 shape
                    dtype = str(out.dtype)  # 输出 dtype
                except Exception:  # 读取失败就用占位
                    shape = "?"  # 占位 shape
                    dtype = "?"  # 占位 dtype
                print(f"[video] output[{i}] name={info.output_names[i]} shape={shape} dtype={dtype}")  # 打印输出信息

        if infer_count >= max_frames:  # 达到最大推理帧数就停止（避免跑太久）
            break  # 退出循环

    cap.release()  # 释放视频句柄
    t_total = time.perf_counter() - t_start  # 整体耗时（秒）

    avg_ms = infer_ms_total / max(infer_count, 1)  # 平均推理耗时（ms），max(...,1) 防止除 0
    fps = 1000.0 / avg_ms if avg_ms > 0 else 0.0  # 近似 FPS（不含解码/预处理/其它开销）
    print(f"[video] ok: {video_path}")  # 视频测试完成
    print(f"[video] frames_infered={infer_count}, frames_read={read_count}, total_time_s={t_total:.2f}")  # 打印帧数与总耗时
    print(f"[video] avg_infer_ms={avg_ms:.2f}, approx_fps={fps:.2f}")  # 打印平均耗时与近似 FPS


def main():  # 程序入口：解析命令行参数并调用图片/视频测试
    parser = argparse.ArgumentParser(description="YOLO ONNX smoke test (image/video) via onnxruntime")  # 创建参数解析器
    parser.add_argument("--model", required=True, help="ONNX 模型路径，例如 G:\\ai\\models\\yolo\\yolo11n.onnx")  # 必选：模型路径
    parser.add_argument("--device", default="cpu", help="cpu 或 cuda:0（如果装了 onnxruntime-gpu）")  # 可选：设备偏好

    group = parser.add_mutually_exclusive_group(required=True)  # image/video 二选一（必须选一个）
    group.add_argument("--image", help="测试图片路径")  # 图片模式：会画框并输出 *_result
    group.add_argument("--video", help="测试视频路径")  # 视频模式：跑若干帧统计性能

    parser.add_argument("--max-frames", type=int, default=30, help="视频最多推理多少帧")  # 防止视频测试跑太久
    parser.add_argument("--sample-every", type=int, default=1, help="视频每隔多少帧推理一次（1=每帧）")  # 抽帧参数
    parser.add_argument("--conf", type=float, default=0.25, help="置信度阈值（仅图片绘框用）")  # conf 阈值
    parser.add_argument("--iou", type=float, default=0.45, help="NMS IoU 阈值（仅图片绘框用）")  # iou 阈值

    args = parser.parse_args()  # 解析命令行

    if args.image:  # 图片模式
        test_image(args.model, args.image, device=args.device, conf_thres=args.conf, iou_thres=args.iou)  # 画框并保存 *_result
    else:  # 视频模式
        test_video(  # 调用视频测试函数
            args.model,  # 模型路径
            args.video,  # 视频路径
            device=args.device,  # 设备偏好
            max_frames=args.max_frames,  # 最多推理帧数
            sample_every=args.sample_every,  # 抽帧间隔
        )  # test_video 调用结束


if __name__ == "__main__":  # 只有直接运行该脚本时才执行（被 import 时不执行）
    main()  # 调用主入口

