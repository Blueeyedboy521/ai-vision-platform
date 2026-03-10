# -*- coding: utf-8 -*-
"""
启动时同步配置到 Redis 并初始化摄像头流
"""
import json
from typing import List

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db_session
from app.core.redis import get_redis
from app.models import Model, Algorithm, Camera, CameraAlgorithm
from common.logging import logger
from common.redis import RedisKeys
from common.media import get_stream_manager
from app.core.redis import write_model_to_redis
from app.services.data_fix import run_startup_data_fix

async def sync_configs_to_redis_and_streams() -> None:
  """
  在应用启动时：
  - 将数据库中的模型、算法、摄像头及摄像头-算法配置刷新到 Redis
  - 使用 StreamManager 为每个摄像头预注册流信息
  """
  redis = get_redis()
  stream_manager = get_stream_manager()

  async with get_db_session() as session:
    # 启动期数据修复（幂等）：补齐区域层级与告警冗余字段
    try:
      await run_startup_data_fix(session)
    except Exception as e:
      logger.warning(f"启动期数据修复失败(可忽略): {e}")

    # 同步模型配置
    result = await session.execute(select(Model))
    models: List[Model] = result.scalars().all()
    for model in models:
      try:
        # 调用 write_model_to_redis同步模型配置到 Redis
        await write_model_to_redis(model.id, session)
      except Exception as e:
        logger.error(f"启动同步模型配置到 Redis 失败: {model.id}, 错误: {e}")

    # 同步算法配置
    result = await session.execute(select(Algorithm))
    algos: List[Algorithm] = result.scalars().all()
    for algo in algos:
      try:
        await redis.client.set(
          RedisKeys.algorithm_config(algo.id),
          json.dumps(
            {
              "id": algo.id,
              "code": algo.code,
              "name": algo.name,
              "model_id": algo.model_id,
              "target_classes": list(algo.target_classes or []),
              "default_confidence": algo.default_confidence,
              "alert_config": algo.alert_config,
              "is_enabled": algo.is_enabled,
            },
            ensure_ascii=False,
          ),
        )
      except Exception as e:
        logger.error(f"启动同步算法配置到 Redis 失败: {algo.id}, 错误: {e}")

    # 同步摄像头配置并初始化流
    result = await session.execute(select(Camera))
    cameras: List[Camera] = result.scalars().all()
    for camera in cameras:
      try:
        await redis.client.set(
          RedisKeys.camera_config(camera.id),
          json.dumps(
            {
              "id": camera.id,
              "name": camera.name,
              "rtsp_url": camera.full_rtsp_url,
              "fps": camera.fps,
              "inference_interval_sec": getattr(camera, "inference_interval_sec", 5),
              "is_enabled": camera.is_enabled,
            },
            ensure_ascii=False,
          ),
        )
      except Exception as e:
        logger.error(f"启动同步摄像头配置到 Redis 失败: {camera.id}, 错误: {e}")

      # 初始化流管理的播放/推流地址
      try:
        stream_manager.register_stream(camera.id, camera.full_rtsp_url)
      except Exception as e:
        logger.error(f"注册摄像头流失败: {camera.id}, 错误: {e}")

    # 同步摄像头-算法绑定配置
    result = await session.execute(
      select(CameraAlgorithm).options(
        selectinload(CameraAlgorithm.algorithm),
        selectinload(CameraAlgorithm.camera),
      )
    )
    configs: List[CameraAlgorithm] = result.scalars().all()
    for cfg in configs:
      try:
        key = RedisKeys.camera_algorithm_config(cfg.camera_id, cfg.algorithm_id)
        await redis.client.set(
          key,
          json.dumps(
            {
              "camera_id": cfg.camera_id,
              "algorithm_id": cfg.algorithm_id,
              "model_id": cfg.model_id,
              "confidence": cfg.get_effective_confidence(),
              "alert_config": cfg.get_effective_alert_config(),
              "regions": cfg.regions or [],
              "inference_interval_sec": getattr(cfg, "inference_interval_sec", 5),
              "alarm_interval_sec": getattr(cfg, "alarm_interval_sec", 30),
              "is_enabled": cfg.is_enabled,
            },
            ensure_ascii=False,
          ),
        )
      except Exception as e:
        logger.error(
          f"启动同步摄像头算法配置到 Redis 失败: camera={cfg.camera_id}, algo={cfg.algorithm_id}, 错误: {e}"
        )

  logger.info("启动同步 Redis 配置与流信息完成")

