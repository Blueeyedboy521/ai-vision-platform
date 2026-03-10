"""
一次性数据修复脚本（可重复运行）

用法：
  在 backend 目录下执行：
    python -m scripts.fix_area_hierarchy_and_alarm_denorm
或：
    python scripts/fix_area_hierarchy_and_alarm_denorm.py
"""

import asyncio

from app.core.database import get_db_session
from app.core.database import close_db
from app.services.data_fix import run_startup_data_fix


async def main() -> None:
    async with get_db_session() as session:
        await run_startup_data_fix(session)
    # 避免 Windows 下 event loop 关闭时报 aiomysql 连接析构警告
    await close_db()


if __name__ == "__main__":
    asyncio.run(main())

