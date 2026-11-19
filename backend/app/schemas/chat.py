from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class CreateChatSession(BaseModel):
    repository_id: int
    session_title: str = Field(default="New conversation", max_length=300)


class ChatMessageRequest(BaseModel):
    question: str = Field(min_length=1, max_length=10_000)


class ChatMessageResponse(BaseModel):
    id: int
    role: str
    message: str
    response_metadata: dict[str, Any] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
