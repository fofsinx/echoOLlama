from app.utils.logger import logger
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Settings
    APP_NAME: str = os.environ.get("APP_NAME", "Pretty Much OpenAI")
    API_VERSION: str = os.environ.get("API_VERSION", "v1")
    DEBUG: bool = os.environ.get("DEBUG", True)
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO").lower()
    
    # Database
    DB_HOST: str = os.environ.get("DB_HOST", "localhost")
    DB_PORT: int = os.environ.get("DB_PORT", 5432)
    DB_USER: str = os.environ.get("DB_USER", "postgres")
    DB_PASSWORD: str = os.environ.get("DB_PASSWORD", "postgres")
    DB_NAME: str = os.environ.get("DB_NAME", "chat_app")
    
    # Redis
    REDIS_HOST: str = os.environ.get("REDIS_HOST", "localhost")
    REDIS_PORT: int = os.environ.get("REDIS_PORT", 6379)
    REDIS_DB: int = os.environ.get("REDIS_DB", 0)
    
    # LLM Settings
    OLLAMA_API_BASE_URL: str = os.environ.get("OLLAMA_API_BASE_URL", "http://localhost:11434")
    OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "sk-default")
    GPT_MODEL: str = os.environ.get("GPT_MODEL", "gpt-4-turbo-preview")
    
    # Audio & Speech Settings
    AUDIO_STORAGE_PATH: str = os.environ.get("AUDIO_STORAGE_PATH", "/tmp/audio_buffers")
    MAX_AUDIO_SIZE_MB: int = os.environ.get("MAX_AUDIO_SIZE_MB", 10)
    DATA_DIR: str = os.environ.get("DATA_DIR", f"{os.getcwd()}/data")
    CACHE_DIR: str = os.path.join(DATA_DIR, "cache")
    SPEECH_CACHE_DIR: str = os.path.join(CACHE_DIR, "audio", "speech")
    
    # Speech-to-Text Settings
    STT_MODEL_CHOICE: str = os.environ.get("STT_MODEL_CHOICE", "whisper")
    WHISPER_MODEL_SIZE: str = os.environ.get("WHISPER_MODEL_SIZE", "base")
    WHISPER_DEVICE: str = os.environ.get("WHISPER_DEVICE", "cpu")
    WHISPER_COMPUTE_TYPE: str = os.environ.get("WHISPER_COMPUTE_TYPE", "float16")
    STT_MODEL: any = None
    USE_CUDA: str = os.environ.get("USE_CUDA_DOCKER", "false")
    
    # Text-to-Speech Settings
    TTS_ENGINE: str = os.environ.get("TTS_ENGINE", "openai")
    TTS_MODEL: str = os.environ.get("OPENAI_API_TTS_MODEL", "tts-1")
    TTS_OPENAI_API_KEY: str = os.environ.get("OPENAI_API_TTS_API_KEY", 'sk-111111111')
    TTS_OPENAI_API_BASE_URL: str = os.environ.get(
        "OPENAI_API_TTS_API_BASE_URL", 
        "http://localhost:8000/v1"
    )
    
    # WebSocket Settings
    WS_HEARTBEAT_INTERVAL: int = os.environ.get("WS_HEARTBEAT_INTERVAL", 30)
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = os.environ.get("RATE_LIMIT_REQUESTS", 1000)
    RATE_LIMIT_TOKENS: int = os.environ.get("RATE_LIMIT_TOKENS", 50000)

    class Config:
        env_file = ".env"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._setup_cuda()
        self.setup_cache_dir()

    def _setup_cuda(self):
        """Setup CUDA if available and requested"""
        if self.USE_CUDA.lower() == "true":
            try:
                import torch
                assert torch.cuda.is_available(), "CUDA not available"
                self.WHISPER_DEVICE = "cuda"
                self.WHISPER_COMPUTE_TYPE = "float16"
                logger.info("🚀 config.py: CUDA enabled successfully")
            except Exception as e:
                cuda_error = (
                    "Error when testing CUDA but USE_CUDA_DOCKER is true. "
                    f"Resetting USE_CUDA_DOCKER to false: {e}"
                )
                logger.warning(f"⚠️ config.py: {cuda_error}")
                os.environ["USE_CUDA_DOCKER"] = "false"
                self.USE_CUDA = "false"
                self.WHISPER_DEVICE = "cpu"
                self.WHISPER_COMPUTE_TYPE = "float32"
        else:
            self.WHISPER_DEVICE = "cpu"
            self.WHISPER_COMPUTE_TYPE = "float32"

    def setup_cache_dir(self):
        """Setup cache directories"""
        try:
            os.makedirs(self.SPEECH_CACHE_DIR, exist_ok=True)
            os.makedirs(self.AUDIO_STORAGE_PATH, exist_ok=True)
            logger.info("📁 config.py: Cache directories setup complete")
        except Exception as e:
            logger.error(f"❌ config.py: Error setting up cache directories: {str(e)}")
            raise e

    @property
    def is_cuda_enabled(self) -> bool:
        """Check if CUDA is enabled"""
        return self.WHISPER_DEVICE == "cuda"

    @property
    def cache_dirs(self) -> dict:
        """Get all cache directories"""
        return {
            "data": self.DATA_DIR,
            "cache": self.CACHE_DIR,
            "speech": self.SPEECH_CACHE_DIR,
            "audio": self.AUDIO_STORAGE_PATH
        }

settings = Settings()