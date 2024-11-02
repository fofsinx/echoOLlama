import json
from typing import Dict, Any
from redis import Redis
from app.db.database import Database
from app.db.models import to_pydantic
from app.schemas.models import SessionSchema
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
            state = json.loads(self.redis.get(f"chat_state:{session_id}") or "{}")

            logger.info(f"📨 chat_state.py: Chat state: {state}")

            if not state or state == {}:
                # Fallback to DB
                session = await self.db.get_session(session_id)
                logger.info(f"📨 chat_state.py: Session: {session}")
                if session:
                    state = to_pydantic(session, SessionSchema).model_dump()
                    logger.info(f"📨 chat_state.py: Chat state from DB: {state}")
                    # Cache in Redis
                    self.redis.set(
                        f"chat_state:{session_id}",
                        json.dumps(state)
                    )
                    self.redis.expire(
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
            self.redis.hmset(
                f"chat_state:{session_id}",
                json.dumps(updates)
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

    async def persist_state(self, session_id: str) -> None:
        """
        Persist chat state to database
        📝 File: chat_state.py, Line: 72, Function: persist_state
        """
        try:
            # Get chat state from Redis
            state = await self.redis.hgetall(f"chat_state:{session_id}")

            # Update database
            await self.db.update_session(
                session_id=session_id,
                updates=state
            )

            logger.info(f"✅ chat_state.py: Persisted chat state for {session_id}")

        except Exception as e:
            logger.error(f"❌ chat_state.py: Failed to persist chat state: {str(e)}")
            raise
