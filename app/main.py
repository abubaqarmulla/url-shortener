
import asyncio
import math
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.analytics import router as analytics_router
from app.api.auth import router as auth_router
from app.api.urls import router as urls_router

from app.cache.redis import (
    cache_url,
    delete_cached_url,
    get_cached_url,
    increment_click_count,
)

from app.core.exceptions import (
    URLNotFoundException,
    UnauthorizedException,
    ResourceNotFoundException,
    url_not_found_handler,
    unauthorized_handler,
    resource_not_found_handler,
)

from app.database import models
from app.database.database import (
    Base,
    engine,
    get_database,
)
from app.database.models import URL
from app.services.analytics_sync import synchronize_click_counts


Base.metadata.create_all(bind=engine)


def is_url_expired(expires_at) -> bool:
    if expires_at is None:
        return False

    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    return expires_at <= datetime.now(timezone.utc)


async def analytics_sync_loop():
    while True:
        try:
            await asyncio.to_thread(
                synchronize_click_counts
            )
        except asyncio.CancelledError:
            raise
        except Exception as exception:
            print(
                f"Analytics synchronization failed: {exception}"
            )

        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    sync_task = asyncio.create_task(
        analytics_sync_loop()
    )

    try:
        yield
    finally:
        sync_task.cancel()

        try:
            await sync_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="Production-Grade URL Shortener",
    description="Scalable URL shortening service built with FastAPI",
    version="1.0.0",
    lifespan=lifespan,
)


app.add_exception_handler(
    URLNotFoundException,
    url_not_found_handler,
)

app.add_exception_handler(
    UnauthorizedException,
    unauthorized_handler,
)

app.add_exception_handler(
    ResourceNotFoundException,
    resource_not_found_handler,
)


app.include_router(auth_router)
app.include_router(urls_router)
app.include_router(analytics_router)


@app.get("/")
def root():
    return {
        "message": "URL Shortener API is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


@app.get("/{short_code}")
def redirect_to_original_url(
    short_code: str,
    database: Session = Depends(get_database),
):
    # Redis cache HIT
    cached_url = get_cached_url(short_code)

    if cached_url is not None:
        if is_url_expired(cached_url.get("expires_at")):
            delete_cached_url(short_code)

            raise HTTPException(
                status_code=410,
                detail="Short URL has expired",
            )

        increment_click_count(short_code)

        return RedirectResponse(
            url=cached_url["original_url"],
            status_code=307,
        )

    # Redis cache MISS: retrieve from PostgreSQL
    url = (
        database.query(URL)
        .filter(URL.short_code == short_code)
        .first()
    )

    if url is None:
        raise URLNotFoundException()

    if is_url_expired(url.expires_at):
        raise HTTPException(
            status_code=410,
            detail="Short URL has expired",
        )

    cache_expiration_seconds = 3600

    if url.expires_at is not None:
        remaining_seconds = (
            url.expires_at - datetime.now(timezone.utc).replace(
                tzinfo=None
            )
        ).total_seconds()

        cache_expiration_seconds = math.floor(
            remaining_seconds
        )

    cache_url(
        short_code=url.short_code,
        url_data={
            "id": url.id,
            "original_url": url.original_url,
            "expires_at": (
                url.expires_at.isoformat()
                if url.expires_at
                else None
            ),
        },
        expiration_seconds=cache_expiration_seconds,
    )

    increment_click_count(short_code)

    return RedirectResponse(
        url=url.original_url,
        status_code=307,
    )
