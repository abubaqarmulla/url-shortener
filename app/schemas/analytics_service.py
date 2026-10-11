from sqlalchemy.orm import Session

from app.cache.redis import redis_client
from app.database.models import URL


def get_click_count(
    short_code: str,
    database: Session,
) -> int:

    redis_click_count = redis_client.get(
        f"clicks:{short_code}"
    )

    if redis_click_count is not None:
        return int(redis_click_count)

    url = (
        database.query(URL)
        .filter(URL.short_code == short_code)
        .first()
    )

    if url is None:
        return 0

    return url.click_count
