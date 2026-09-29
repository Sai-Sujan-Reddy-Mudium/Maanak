from pydantic import BaseModel, Field
from typing import List, Optional

class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the message sender")
    content: str = Field(..., max_length=10000)

class ChatRequest(BaseModel):
    input_type: str = Field(default="text", description="Type of input: text or audio")
    data: str = Field(..., description="The query string or base64 audio data")
    source_lang: str = Field(default="en", description="ISO language code of input")
    session_id: str = Field(..., min_length=1, max_length=255, description="Unique session identifier")
    chat_history: Optional[List[ChatMessage]] = Field(default_factory=list)

class TTSRequest(BaseModel):
    text: str = Field(..., description="Text to synthesize")
    target_lang: str = Field(..., description="Language code")
