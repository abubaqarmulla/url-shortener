from datetime import datetime

from pydantic import AnyHttpUrl, BaseModel


class URLCreate(BaseModel):
    original_url: AnyHttpUrl
    expires_at: datetime | None = None


class URLResponse(BaseModel):
    id: int
    original_url: str
    short_code: str
    expires_at: datetime | None
    click_count: int
    created_at: datetime

    class Config:
        from_attributes = True
