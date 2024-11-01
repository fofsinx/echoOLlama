from typing import Optional, Dict, Any
from fastapi import HTTPException


class WebSocketError(Exception):
    """Base WebSocket error"""

    def __init__(
            self,
            message: str,
            code: int = 1000,
            data: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.data = data or {}
        super().__init__(self.message)


class SessionError(WebSocketError):
    """Session-related errors"""
    pass


class AudioError(WebSocketError):
    """Audio processing errors"""
    pass


class LLMError(WebSocketError):
    """LLM-related errors"""
    pass


class RateLimitError(WebSocketError):
    """Rate limiting errors"""
    pass


class AudioProcessingError(WebSocketError):
    """Audio processing errors"""
    pass


def handle_websocket_error(error: Exception) -> Dict[str, Any]:
    """Convert exceptions to WebSocket error responses"""
    if isinstance(error, WebSocketError):
        return {
            "type": "error",
            "code": error.code,
            "message": str(error),
            "data": error.data
        }
    elif isinstance(error, HTTPException):
        return {
            "type": "error",
            "code": error.status_code,
            "message": error.detail
        }
    else:
        return {
            "type": "error",
            "code": 500,
            "message": "Internal server error"
        }
