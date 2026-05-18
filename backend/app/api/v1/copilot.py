from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.copilot import copilot_chat
from app.services.llm import ChatMessage, LLMUnavailableError

router = APIRouter()


class CopilotMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str


class CopilotChatRequest(BaseModel):
    messages: list[CopilotMessage]
    focused_crisis_id: str | None = None


class CopilotChatResponse(BaseModel):
    reply: str


@router.post("/chat", response_model=CopilotChatResponse)
async def chat_endpoint(payload: CopilotChatRequest, db: AsyncSession = Depends(get_db)):
    if not payload.messages:
        raise HTTPException(status_code=400, detail="messages cannot be empty")
    msgs = [ChatMessage(role=m.role, content=m.content) for m in payload.messages]
    try:
        reply = await copilot_chat(db, msgs, focused_crisis_id=payload.focused_crisis_id)
    except LLMUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return CopilotChatResponse(reply=reply)
