from typing import Dict, Any
from fastapi import HTTPException
from app.websocket.types import SessionConfig, MessageType, WebSocketEvent
from app.websocket.base_handler import BaseHandler

from app.utils.logger import logger


class SessionHandler(BaseHandler):
    """Handles session-related events"""

    async def handle_session_update(self, event: WebSocketEvent) -> None:
        """
        Handle session.update event
        📝 File: session.py, Line: 13, Function: handle_session_update
        """
        try:
            session_data = event.data.get("state", {})
            event_id = event.data.get("event_id", "default")

            # Validate and create session config
            config = SessionConfig(**session_data)

            logger.info(f"🔄 session.py: Updating session {config.id}")

            # Store session config with TTL
            session_key = f"session:{config.id}"
            await self.redis.set(session_key, config.__dict__)
            await self.redis.expire(session_key, 3600)  # 1 hour TTL

            await self.send_event(MessageType.SESSION_UPDATED.value, {
                "event_id": event_id,
                "type": MessageType.SESSION_UPDATED.value,
                "session": config.__dict__
            })

            self.db.update_session(config.__dict__)

        except Exception as e:
            logger.error(f"❌ session.py: Session update failed: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
