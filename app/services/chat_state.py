from typing import Dict, Any, Optional
from redis import Redis
from app.db.database import Database
import json
from app.utils.logger import logger

class ChatStateManager:
    def __init__(self, redis: Redis, db: Database):
        self.redis = redis
        self.db = db
        
    async def get_chat_state(self, session_id: str) -> Dict[str, Any]:
        """
        Get chat state from Redis and DB
        📝 File: chat_state.py, Line: 15, Function: get_chat_state
        """
        try:
            # Try Redis first
            state = await self.redis.hgetall(f"chat_state:{session_id}")
            
            if not state:
                # Fallback to DB
                session = await self.db.get_session(session_id)
                if session:
                    state = {
                        "id": session["id"],
                        "status": session["status"],
                        "model": session["model"],
                        "modalities": session["modalities"],
                        "metadata": session["metadata"]
                    }
                    # Cache in Redis
                    await self.redis.hmset(
                        f"chat_state:{session_id}",
                        state
                    )
                    await self.redis.expire(
                        f"chat_state:{session_id}",
                        3600
                    )
            
            return state
            
        except Exception as e:
            logger.error(f"❌ chat_state.py: Failed to get chat state: {str(e)}")
            raise

    async def update_chat_state(
        self,
        session_id: str,
        updates: Dict[str, Any]
    ) -> None:
        """
        Update chat state in Redis and DB
        📝 File: chat_state.py, Line: 54, Function: update_chat_state
        """
        try:
            # Update Redis
            await self.redis.hmset(
                f"chat_state:{session_id}",
                updates
            )
            
            # Update DB
            await self.db.update_session(
                session_id=session_id,
                updates=updates
            )
            
            logger.info(f"✅ chat_state.py: Updated chat state for {session_id}")
            
        except Exception as e:
            logger.error(f"❌ chat_state.py: Failed to update chat state: {str(e)}")
            raise