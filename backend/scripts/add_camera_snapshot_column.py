# -*- coding: utf-8 -*-
"""
为 cameras 表添加 last_snapshot_path 字段（若不存在）

用法（在 backend 目录）:
  python -m scripts.add_camera_snapshot_column
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from app.core.database import get_engine


async def main():
    engine = get_engine()
    async with engine.begin() as conn:
        # MySQL: 检查列是否存在后添加
        try:
            await conn.execute(text("""
                ALTER TABLE cameras 
                ADD COLUMN last_snapshot_path VARCHAR(500) NULL 
                COMMENT '最新抓拍图片相对路径' 
                AFTER resolution
            """))
            print("已添加 cameras.last_snapshot_path 列")
        except Exception as e:
            if "Duplicate column" in str(e) or "1060" in str(e):
                print("cameras.last_snapshot_path 已存在，跳过")
            else:
                raise


if __name__ == "__main__":
    asyncio.run(main())
