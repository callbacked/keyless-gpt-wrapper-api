from pydantic import BaseModel, validator
from typing import List, Dict, Optional, Union, Any
import time

class AudioConfig(BaseModel):
    voice: str = "alloy"
    format: str = "wav"

class AudioData(BaseModel):
    id: Optional[str] = None
    expires_at: Optional[int] = None
    data: Optional[str] = None
    transcript: Optional[str] = None


class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int = int(time.time())
    owned_by: str = "organization"
    root: Optional[str] = None
    parent: Optional[str] = None
    permission: List[Dict[str, Any]] = [{"id": "modelperm-default", "object": "model_permission", "created": int(time.time()), "allow_create_engine": False, "allow_sampling": True, "allow_logprobs": True, "allow_search_indices": False, "allow_view": True, "allow_fine_tuning": False, "organization": "*", "group": None, "is_blocking": False}]

class ChatMessage(BaseModel):
    role: str
    content: Optional[Union[str, List[Dict[str, str]]]] = None
    audio: Optional[AudioData] = None

    @validator('content')
    def validate_content(cls, v):
        if isinstance(v, list):
            # Extract text from structured content
            return ' '.join(item.get('text', '') for item in v if isinstance(item, dict) and 'text' in item)
        return v

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    conversation_id: Optional[str] = None
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None
    modalities: Optional[List[str]] = None
    audio: Optional[AudioConfig] = None

class ChatCompletionResponseChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: Optional[str] = None

class ChatCompletionResponseUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionResponseChoice]
    usage: Optional[Dict[str, int]] = None

class DeltaMessage(BaseModel):
    role: Optional[str] = None
    content: Optional[str] = None

class ChatCompletionStreamResponseChoice(BaseModel):
    index: int
    delta: DeltaMessage
    finish_reason: Optional[str] = None

class ChatCompletionStreamResponse(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[ChatCompletionStreamResponseChoice]

class ErrorResponse(BaseModel):
    message: str
    type: str
    param: Optional[str] = None
    code: Optional[str] = None

class APIError(BaseModel):
    error: ErrorResponse

