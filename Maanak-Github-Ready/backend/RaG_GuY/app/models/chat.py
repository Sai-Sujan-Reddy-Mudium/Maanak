from pydantic import BaseModel, Field
from typing import List

class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the message sender (user or assistant)")
    content: str = Field(..., max_length=10000, description="Content of the message")

class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=255, description="Unique session identifier")
    query: str = Field(..., min_length=1, max_length=4000, description="User search or chat query")
    chat_history: List[ChatMessage] = Field(default_factory=list, description="Previous chat conversation history")
