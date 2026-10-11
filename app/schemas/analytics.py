from pydantic import BaseModel


class URLAnalyticsResponse(BaseModel):
    url_id: int
    short_code: str
    original_url: str
    click_count: int
