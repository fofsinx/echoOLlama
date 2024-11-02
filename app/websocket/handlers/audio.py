from typing import Dict, Any
from fastapi import HTTPException

from app.services.audio import AudioService
from app.websocket.types import MessageType
from app.websocket.base_handler import BaseHandler
from app.utils.errors import AudioProcessingError

from app.utils.logger import logger


class AudioHandler(BaseHandler):
    """Handles audio-related WebSocket events"""

    def __init__(self, audio_service: AudioService, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.audio_service = audio_service

    async def handle_audio_append(self, message: Dict[str, Any]) -> None:
        """
        Handle audio buffer append with transcription
        📝 File: audio.py, Line: 20, Function: handle_audio_append
        """
        try:
            audio_data = message.get("audio")
            event_id = message.get("event_id", "default")

            if not audio_data:
                raise ValueError("No audio data provided")

            # Process audio through service
            async for transcription in self.audio_service.transcribe_audio(
                    audio_data=audio_data,
                    event_id=event_id
            ):
                if isinstance(transcription, dict) and "error" in transcription:
                    raise AudioProcessingError(transcription["error"])

                await self.redis.rpush(
                    f"transcriptions:{event_id}",
                    transcription
                )

            await self.send_event(MessageType.AUDIO_TRANSCRIBED.value, {
                "event_id": event_id,
                "status": "completed"
            })

        except Exception as e:
            logger.error(f"❌ audio.py: Audio processing failed: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

    async def handle_speech_generate(self, message: Dict[str, Any]) -> None:
        """
        Handle speech generation request
        📝 File: audio.py, Line: 54, Function: handle_speech_generate
        """
        try:
            text = message.get("text")
            voice = message.get("voice", "alloy")
            event_id = message.get("event_id", "default")

            if not text:
                raise ValueError("No text provided")

            # Generate speech
            file_path, cache_key = await self.audio_service.generate_speech(
                text=text,
                voice=voice
            )

            # Send response with file path
            await self.send_event(MessageType.SPEECH_GENERATED.value, {
                "event_id": event_id,
                "file_path": file_path,
                "cache_key": cache_key
            })

        except Exception as e:
            logger.error(f"❌ audio.py: Speech generation failed: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

    async def handle_audio_commit(self, message: Dict[str, Any]) -> None:
        """
        Handle audio buffer commit
        📝 File: audio.py, Line: 74, Function: handle_audio_commit
        """
        try:
            event_id = message.get("event_id", "default")

            # Commit audio buffer
            await self.audio_service.commit_audio(event_id)

        except Exception as e:
            logger.error(f"❌ audio.py: Audio commit failed: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

    async def cleanup(self) -> None:
        """
        Cleanup audio service resources
        📝 File: audio.py, Line: 82, Function: cleanup
        """
        try:
            await self.audio_service.cleanup()
            logger.info("🧹 audio.py: Audio handler cleanup completed")
        except Exception as e:
            logger.error(f"❌ audio.py: Cleanup failed: {str(e)}")
