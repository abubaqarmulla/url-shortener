
import json

import redis

from app.core.config import settings


redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
)


RATE_LIMIT_SCRIPT = """
local count = redis.call("INCR", KEYS[1])

if count == 1 then
    redis.call("EXPIRE", KEYS[1], ARGV[1])
end

return count
"""


def get_cached_url(short_code: str):
    cached_url = redis_client.get(f"url:{short_code}")

    if cached_url is None:
        return None

    return json.loads(cached_url)


def cache_url(
    short_code: str,
    url_data: dict,
    expiration_seconds: int = 3600,
):
    if expiration_seconds <= 0:
        return

    redis_client.setex(
        f"url:{short_code}",
        expiration_seconds,
        json.dumps(url_data),
    )


def delete_cached_url(short_code: str):
    redis_client.delete(f"url:{short_code}")


def increment_click_count(short_code: str):
    return redis_client.incr(f"clicks:{short_code}")


def check_rate_limit(
    identifier: str,
    limit: int,
    window_seconds: int,
) -> bool:
    if limit < 1 or window_seconds < 1:
        raise ValueError(
            "Rate limit and window must both be positive"
        )

    key = f"rate_limit:{identifier}"

    current_count = int(
        redis_client.eval(
            RATE_LIMIT_SCRIPT,
            1,
            key,
            window_seconds,
        )
    )

    return current_count <= limit


def get_all_click_counters():
    click_counters = {}

    for key in redis_client.scan_iter(match="clicks:*"):
        short_code = key.removeprefix("clicks:")
        click_count = redis_client.get(key)

        if click_count is not None:
            click_counters[short_code] = int(click_count)

    return click_counters
