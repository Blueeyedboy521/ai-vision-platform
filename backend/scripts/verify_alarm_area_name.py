from __future__ import annotations

from sqlalchemy import text

from app.core.database import get_sync_db_session


def main() -> None:
    with get_sync_db_session() as s:
        empty_cnt = s.execute(
            text("SELECT COUNT(1) FROM alarms WHERE area_name IS NULL OR area_name = ''")
        ).scalar()
        no_slash_cnt = s.execute(
            text(
                "SELECT COUNT(1) FROM alarms "
                "WHERE area_name IS NOT NULL AND area_name != '' AND area_name NOT LIKE '%/%'"
            )
        ).scalar()
        latest = s.execute(
            text(
                "SELECT id, camera_name, area_name, alarm_time "
                "FROM alarms ORDER BY alarm_time DESC LIMIT 5"
            )
        ).fetchall()

    print(f"alarms area_name empty: {empty_cnt}")
    print(f"alarms area_name no_slash: {no_slash_cnt}")
    print("latest 5:")
    for r in latest:
        print(r[0], r[1], r[2], r[3])


if __name__ == "__main__":
    main()

