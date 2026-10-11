from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.cache.redis import delete_cached_url
from app.cache.redis import get_cached_url, redis_client
from app.api.auth import get_current_user
from app.core.security import create_url_rate_limit

from app.database.database import get_database
from app.database.models import URL, User
from app.schemas.url import URLCreate, URLResponse
from app.services.url_service import generate_unique_short_code


router = APIRouter(
    prefix="/urls",
    tags=["URLs"],
)


@router.post(
    "",
    response_model=URLResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(create_url_rate_limit)],
)
@router.post(
    "/",
    response_model=URLResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(create_url_rate_limit)],
    include_in_schema=False,
)
def create_url(
    url_data: URLCreate,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_database),
):
    short_code = generate_unique_short_code(database)

    new_url = URL(
        original_url=str(url_data.original_url),
        short_code=short_code,
        expires_at=url_data.expires_at,
        user_id=current_user.id,
    )

    database.add(new_url)
    database.commit()
    database.refresh(new_url)

    return new_url


@router.get(
    "",
    response_model=list[URLResponse],
)
@router.get(
    "/",
    response_model=list[URLResponse],
    include_in_schema=False,
)
def get_urls(
    page: int = 1,
    page_size: int = 10,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_database),
):
    if page < 1:
        raise HTTPException(
            status_code=400,
            detail="Page must be greater than or equal to 1",
        )

    if page_size < 1 or page_size > 100:
        raise HTTPException(
            status_code=400,
            detail="Page size must be between 1 and 100",
        )

    offset = (page - 1) * page_size

    urls = (
        database.query(URL)
        .filter(URL.user_id == current_user.id)
        .order_by(URL.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return urls


@router.delete(
    "/{url_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_url(
    url_id: int,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_database),
):
    url = (
        database.query(URL)
        .filter(
            URL.id == url_id,
            URL.user_id == current_user.id,
        )
        .first()
    )

    if url is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="URL not found",
        )

    short_code = url.short_code

    database.delete(url)
    database.commit()

    delete_cached_url(short_code)

    redis_client.delete(f"clicks:{short_code}")

    return None
