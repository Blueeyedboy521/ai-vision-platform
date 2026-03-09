# -*- coding: utf-8 -*-
"""
从 cameras 表删除 rtsp_username、rtsp_password 列（认证改由 rtsp_url 内携带）

用法（在 backend 目录）:
  python -m scripts.drop_camera_rtsp_auth_columns
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from app.core.database import get_engine


async def drop_column_if_exists(conn, table: str, col: str):
    """尝试删除列，若不存在则忽略"""
    try:
        await conn.execute(text(f"ALTER TABLE {table} DROP COLUMN {col}"))
        print(f"已删除 {table}.{col}")
    except Exception as e:
        err = str(e)
        if "1091" in err or "Can't DROP" in err or "check that column" in err.lower():
            print(f"{table}.{col} 不存在，跳过")
        else:
            raise


async def main():
    engine = get_engine()
    async with engine.begin() as conn:
        await drop_column_if_exists(conn, "cameras", "rtsp_username")
        await drop_column_if_exists(conn, "cameras", "rtsp_password")
        # 兼容旧 schema 中列名为 username / password 的情况
        await drop_column_if_exists(conn, "cameras", "username")
        await drop_column_if_exists(conn, "cameras", "password")
    print("迁移完成")


if __name__ == "__main__":
    asyncio.run(main())
