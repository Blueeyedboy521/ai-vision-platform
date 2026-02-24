# 脚本说明

## 数据库：摄像头抓拍字段

若数据库已存在，需为 `cameras` 表增加抓拍路径字段（MySQL）:

```sql
ALTER TABLE cameras ADD COLUMN last_snapshot_path VARCHAR(500) NULL COMMENT '最新抓拍图片相对路径' AFTER resolution;
```

## 一键配置 YOLO11 + 摄像头

使用本机已转换的 `yolo11n.onnx` 上架模型、创建「人员检测」算法，并为指定摄像头绑定（置信度≥0.9 告警）:

```bash
cd backend
python -m scripts.setup_yolo11_camera
```

默认摄像头 ID: `926001bb83db48bcb62cf3ebf0eb1e72`  
默认模型路径: `G:\ai\models\yolo\yolo11n.onnx`

可在 `scripts/setup_yolo11_camera.py` 顶部修改 `MODEL_PATH`、`CAMERA_ID` 等常量。
