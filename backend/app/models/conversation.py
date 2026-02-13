from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import uuid4

class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ConversationBase(BaseModel):
    title: str
    messages: List[Message] = []

class ConversationCreate(ConversationBase):
    pass

class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    messages: Optional[List[Message]] = None

class Conversation(ConversationBase):
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True

class ConversationList(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int
