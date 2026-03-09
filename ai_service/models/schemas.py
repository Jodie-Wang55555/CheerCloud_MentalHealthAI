from pydantic import BaseModel
from typing import Optional, List


class Message(BaseModel):
    role: str   # "user" | "model"
    text: str


class ChatRequest(BaseModel):
    user_id: str
    message: str
    history: Optional[List[Message]] = []
    image_base64: Optional[str] = None
    image_mime_type: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    intent: str
    strategy: str
    retrieved_context: Optional[List[str]] = []
    is_crisis: bool = False
    citations: Optional[List[str]] = []


class SaveEmotionRequest(BaseModel):
    user_id: str
    conversation: List[Message]


class SaveEmotionResponse(BaseModel):
    success: bool
    summary: str
