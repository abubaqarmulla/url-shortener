
from app.cache.redis import get_all_click_counters
from app.database.database import SessionLocal
from app.database.models import URL


def synchronize_click_counts():
    database = SessionLocal()

    try:
        click_counters = get_all_click_counters()

        if not click_counters:
            return

        urls = (
            database.query(URL)
            .filter(URL.short_code.in_(click_counters.keys()))
            .all()
        )

        for url in urls:
            redis_count = click_counters[url.short_code]
            database_count = url.click_count or 0

            url.click_count = max(
                database_count,
                redis_count,
            )

        database.commit()

    except Exception:
        database.rollback()
        raise

    finally:
        database.close()
