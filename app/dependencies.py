from app.services.llm import LLMService
from app.services.audio import AudioService

_llm_service = None
_audio_service = None

def get_llm_service() -> LLMService:
    """
    Get or create LLM service instance
    📝 File: dependencies.py, Line: 9, Function: get_llm_service
    """
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service

def get_audio_service() -> AudioService:
    """
    Get or create Audio service instance
    📝 File: dependencies.py, Line: 19, Function: get_audio_service
    """
    global _audio_service
    if _audio_service is None:
        _audio_service = AudioService()
    return _audio_service