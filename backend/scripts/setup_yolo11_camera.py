# -*- coding: utf-8 -*-
"""
一键：上架 YOLO11n 模型、创建人员检测算法、并为指定摄像头绑定（置信度>0.9 告警）

用法（在 backend 目录）:
  python -m scripts.setup_yolo11_camera

默认摄像头 ID: 926001bb83db48bcb62cf3ebf0eb1e72
默认模型路径: G:\\ai\\models\\yolo\\yolo11n.onnx（可按需修改下方常量）
"""
import asyncio
import sys
from pathlib import Path

# 项目根
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.models import Model, Algorithm, Camera, CameraAlgorithm
from app.models.base import generate_uuid


# 可修改常量
MODEL_PATH = r"G:\ai\models\yolo\yolo11n.onnx"
MODEL_CODE = "yolo11n"
MODEL_NAME = "YOLO11n"
# YOLO11 常见类别（可按需缩减；人员检测只需 person）
CLASSES = ["person", "bicycle", "car", "motorcycle", "bus", "truck", "cat", "dog"]
ALGORITHM_NAME = "人员检测"
ALGORITHM_CODE = "person_detection_yolo11"
TARGET_CLASSES = ["person"]
CONFIDENCE = 0.9
CAMERA_ID = "926001bb83db48bcb62cf3ebf0eb1e72"


async def main():
    async with get_db_session() as session:
        # 1) 模型已存在则用，否则创建
        r = await session.execute(select(Model).where(Model.code == MODEL_CODE))
        model = r.scalar_one_or_none()
        if not model:
            model = Model(
                id=generate_uuid(),
                name=MODEL_NAME,
                code=MODEL_CODE,
                model_type="onnx",
                model_path=MODEL_PATH,
                version="1.0",
                classes=CLASSES,
                is_enabled=True,
                created_by=None,
                updated_by=None,
            )
            session.add(model)
            await session.flush()
            print(f"已创建模型: {model.id} - {model.name} ({model.code})")
        else:
            print(f"使用已有模型: {model.id} - {model.name}")

        # 2) 算法已存在则用，否则创建
        r = await session.execute(select(Algorithm).where(Algorithm.code == ALGORITHM_CODE))
        algo = r.scalar_one_or_none()
        if not algo:
            algo = Algorithm(
                id=generate_uuid(),
                name=ALGORITHM_NAME,
                code=ALGORITHM_CODE,
                model_id=model.id,
                default_confidence=CONFIDENCE,
                is_enabled=True,
                created_by=None,
                updated_by=None,
            )
            algo.target_classes = TARGET_CLASSES
            algo.alert_config = {
                "trigger_type": "instant",
                "duration_seconds": 0,
                "count_threshold": 0,
                "cooldown_seconds": 30,
                "alert_level": "danger",
            }
            session.add(algo)
            await session.flush()
            print(f"已创建算法: {algo.id} - {algo.name} (置信度>={CONFIDENCE} 告警)")
        else:
            print(f"使用已有算法: {algo.id} - {algo.name}")

        # 3) 摄像头存在检查
        r = await session.execute(select(Camera).where(Camera.id == CAMERA_ID))
        cam = r.scalar_one_or_none()
        if not cam:
            print(f"摄像头不存在: {CAMERA_ID}，请先创建该摄像头或修改脚本中的 CAMERA_ID")
            return

        # 4) 已绑定则跳过
        r = await session.execute(
            select(CameraAlgorithm).where(
                CameraAlgorithm.camera_id == CAMERA_ID,
                CameraAlgorithm.algorithm_id == algo.id,
            )
        )
        if r.scalar_one_or_none():
            print(f"摄像头已配置该算法，无需重复绑定")
            await session.commit()
            return

        # 5) 绑定摄像头-算法（置信度 0.9）
        ca = CameraAlgorithm(
            id=generate_uuid(),
            camera_id=CAMERA_ID,
            algorithm_id=algo.id,
            model_id=model.id,
            confidence=CONFIDENCE,
            is_enabled=True,
            created_by=None,
            updated_by=None,
        )
        session.add(ca)
        await session.commit()
        print(f"已为摄像头 {CAMERA_ID} 配置算法 {algo.name}，置信度 {CONFIDENCE}，超过即告警。")


if __name__ == "__main__":
    asyncio.run(main())
