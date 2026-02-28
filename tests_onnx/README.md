# ONNX / YOLO 可用性测试

这个目录用于**独立验证**本机 `onnxruntime`（CPU 或 GPU）是否能正常加载并跑通 YOLO 的 ONNX 模型。

## 准备

- 安装依赖（一般项目里已经有）：
  - `onnxruntime`
  - `numpy`
  - `opencv-python`

## 运行（图片）

```bash
python tests_onnx/yolo_onnx_smoke_test.py --model "G:\ai\models\yolo\yolo11n.onnx" --image "G:\ai\sources\images\test1.png"
python tests_onnx/yolo_onnx_smoke_test.py --model "G:\ai\models\yolo\yolo11n.onnx" --image "G:\ai\sources\images\test1.jpg"
```

## 运行（视频）

```bash
python tests_onnx/yolo_onnx_smoke_test.py --model "G:\ai\models\yolo\yolo11n.onnx" --video "tests_onnx/assets/test.mp4" --max-frames 30
```

## 输出说明

- 成功标志：能打印出 `providers=...`、输入输出张量信息，并且每帧推理返回输出张量（会打印 shape/dtype）。
- 这个脚本是 smoke test：**不做检测框解析**，主要验证 ONNX Runtime 跑通与性能大致情况。

