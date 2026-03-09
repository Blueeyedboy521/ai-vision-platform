# -*- coding: utf-8 -*-
"""
为 camera_algorithms 表添加 inference_interval_sec、alarm_interval_sec 字段（若不存在）

用法（在 backend 目录）:
  python -m scripts.add_camera_algorithm_interval_columns
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from app.core.database import get_engine


async def add_column_if_not_exists(conn, table: str, col_def: str, col_name: str):
    """尝试添加列，若已存在则跳过"""
    try:
        await conn.execute(text(f"""
            ALTER TABLE {table}
            ADD COLUMN {col_def}
        """))
        print(f"已添加 {table}.{col_name} 列")
    except Exception as e:
        err = str(e)
        if "Duplicate column" in err or "1060" in err:
            print(f"{table}.{col_name} 已存在，跳过")
        else:
            raise


async def main():
    engine = get_engine()
    async with engine.begin() as conn:
        await add_column_if_not_exists(
            conn,
            "camera_algorithms",
            "inference_interval_sec INT NOT NULL DEFAULT 5 COMMENT '识别间隔(秒)' AFTER regions",
            "inference_interval_sec",
        )
        await add_column_if_not_exists(
            conn,
            "camera_algorithms",
            "alarm_interval_sec INT NOT NULL DEFAULT 30 COMMENT '告警间隔(秒)' AFTER inference_interval_sec",
            "alarm_interval_sec",
        )
    print("迁移完成")


if __name__ == "__main__":
    asyncio.run(main())
