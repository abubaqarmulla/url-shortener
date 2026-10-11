from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.database.database import get_database
from app.database.models import URL, User
from app.schemas.analytics import URLAnalyticsResponse
from app.services.analytics_service import get_click_count


router = APIRouter(
    prefix="/urls",
    tags=["Analytics"],
)


@router.get(
    "/{url_id}/analytics",
    response_model=URLAnalyticsResponse,
)
def get_url_analytics(
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
            status_code=404,
            detail="URL not found",
        )

    click_count = get_click_count(
        short_code=url.short_code,
        database=database,
    )

    return URLAnalyticsResponse(
        url_id=url.id,
        short_code=url.short_code,
        original_url=url.original_url,
        click_count=click_count,
    )

@router.post("/{url_id}/analytics/sync")
def sync_analytics(
    url_id: int,
    database: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
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
        raise ResourceNotFoundException()

    click_count = sync_click_count(
        short_code=url.short_code,
        database=database,
    )

    return {
        "url_id": url.id,
        "short_code": url.short_code,
        "click_count": click_count,
        "message": "Click count synchronized successfully.",
    }
