from typing import Optional
from fastapi import File, UploadFile, APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse, StreamingResponse
from app.services.audio import AudioService
from app.dependencies import get_audio_service
from app.utils.logger import logger

router = APIRouter()


@router.post("/transcribe")
async def transcribe_audio(
        file: UploadFile = File(...),
        language: str = 'en',
        task: str = "transcribe",
        beam_size: int = 5,
        vad_filter: bool = True,
        audio_service: AudioService = Depends(get_audio_service)
) -> StreamingResponse:
    """
    Transcribe audio file to text using Faster Whisper and stream the results
    📝 File: voice.py, Line: 20, Function: transcribe_audio
    """
    try:
        # Read file content and encode to base64
        content = await file.read()
        event_id = f"transcribe_{file.filename}"

        logger.info(f"🎤 voice.py: Starting transcription for file {file.filename}")

        return StreamingResponse(
            audio_service.transcribe_audio(
                audio_data=content,
                event_id=event_id,
                language=language,
                task=task,
                beam_size=beam_size,
                vad_filter=vad_filter
            ),
            media_type="text/event-stream"
        )
    except Exception as e:
        logger.error(f"❌ voice.py: Error in transcription generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/speech")
async def speech(
        input: str,
        voice: Optional[str] = 'alloy',
        model: Optional[str] = 'tts-1',
        response_format: Optional[str] = 'mp3',
        audio_service: AudioService = Depends(get_audio_service)
):
    """
    Generate speech from text using TTS service
    📝 File: voice.py, Line: 50, Function: speech
    """
    try:
        logger.info(f"🎤 voice.py: Starting speech generation for text: {input[:30]}...")

        file_path, cache_key = await audio_service.generate_speech(
            text=input,
            voice=voice,
            model=model,
            response_format=response_format
        )

        return FileResponse(
            file_path,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"attachment; filename={cache_key}.mp3",
                "Accept-Ranges": "bytes",
                "Cache-Control": "no-cache",
            }
        )

    except Exception as e:
        logger.error(f"❌ voice.py: Error in speech generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
