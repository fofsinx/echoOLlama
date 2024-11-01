from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class GenerateRequest(BaseModel):
    model: str
    prompt: str
    system: Optional[str] = None
    template: Optional[str] = None
    context: Optional[List[int]] = None
    options: Optional[Dict[str, Any]] = None
    format: Optional[str] = None
    tools: Optional[List[str]] = None
    stream: bool = False

class GenerateResponse(BaseModel):
    model: str
    created_at: str = Field(..., alias="created_at")
    response: str
    done: bool
    context: Optional[List[int]] = None
    total_duration: Optional[int] = Field(None, alias="total_duration")
    load_duration: Optional[int] = Field(None, alias="load_duration")
    prompt_eval_duration: Optional[int] = Field(None, alias="prompt_eval_duration")
    eval_duration: Optional[int] = Field(None, alias="eval_duration")
    prompt_eval_count: Optional[int] = Field(None, alias="prompt_eval_count")
    eval_count: Optional[int] = Field(None, alias="eval_count")

class ChatMessage(BaseModel):
    role: str
    content: str
    images: Optional[List[str]] = None

class ChatRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    system: Optional[str] = None
    format: Optional[str] = None
    options: Optional[Dict[str, Any]] = None
    template: Optional[str] = None
    stream: bool = False
    tools: Optional[List[str]] = None


class ChatResponse(BaseModel):
    model: str
    created_at: str = Field(..., alias="created_at")
    message: ChatMessage
    done: bool
    total_duration: Optional[int] = Field(None, alias="total_duration")
    load_duration: Optional[int] = Field(None, alias="load_duration")
    prompt_eval_duration: Optional[int] = Field(None, alias="prompt_eval_duration")
    eval_duration: Optional[int] = Field(None, alias="eval_duration")
    prompt_eval_count: Optional[int] = Field(None, alias="prompt_eval_count")
    eval_count: Optional[int] = Field(None, alias="eval_count")
    encode: Optional[str] = Field(None, alias="encode")

class ModelInfo(BaseModel):
    name: str
    modified_at: str = Field(..., alias="modified_at")
    size: int
    digest: str
    details: Dict[str, Any]

class PullRequest(BaseModel):
    name: str
    insecure: Optional[bool] = None
    stream: Optional[bool] = None

class PullResponse(BaseModel):
    status: str
    digest: Optional[str] = None
    total: Optional[int] = None
    completed: Optional[int] = None

class CreateRequest(BaseModel):
    name: str
    modelfile: str
    stream: Optional[bool] = None

class CreateResponse(BaseModel):
    status: str

class DeleteRequest(BaseModel):
    name: str

class SpeechRequest(BaseModel):
    model: Optional[str] = Field('tts-1', alias="model")
    input: str = Field(..., alias="input")
    voice: Optional[str] = Field('airley', alias="voice")
    response_format: Optional[str] = Field('mp3', alias="response_format")
