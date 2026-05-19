from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

Sentiment = Literal["positive", "neutral", "negative", "mixed"]


class MediaMentionBase(BaseModel):
    outlet: str
    url: str | None = None
    headline: str | None = None
    snippet: str
    author: str | None = None
    crisis_id: str | None = None


class MediaMentionCreate(MediaMentionBase):
    mentioned_at: datetime | None = None
    auto_analyze: bool = True


class MediaMentionUpdate(BaseModel):
    crisis_id: str | None = None


class MediaMentionResponse(MediaMentionBase):
    id: str
    sentiment: Sentiment | None
    sentiment_score: float | None
    key_themes: list[str]
    analyzed_at: datetime | None
    mentioned_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
