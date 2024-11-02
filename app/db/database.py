from typing import Optional, List, Dict
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.future import select
from app.config import settings
from app.db.models import Session, Conversation, ConversationItem, Response, MessageRole, ResponseStatus, Base, \
    RateLimit
from app.utils.logger import logger
import uuid


class Database:
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._session: Optional[AsyncSession] = None

    async def connect(self):
        """Initialize database connection"""
        if not self.engine:
            logger.info("🔌 File: database.py, Function: connect; Connecting to database")
            print(
                f'postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}')
            self.engine: AsyncEngine = create_async_engine(
                f'postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}',
                echo=True,
                pool_size=20,
                max_overflow=0
            )
            self.SessionLocal = sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)

    async def disconnect(self):
        """Close database connection"""
        if self.engine:
            logger.info("🔌 File: database.py, Function: disconnect; Disconnecting from database")
            await self.engine.dispose()

    async def create_session(self, session_data: Dict) -> Session:
        """Create a new realtime session"""
        async with self.SessionLocal() as session:
            logger.info("📝 File: database.py, Function: create_session; Creating new session")
            new_session = Session(**session_data)
            session.add(new_session)
            await session.commit()
            await session.refresh(new_session)
            return new_session

    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        async with self.SessionLocal() as session:
            logger.info(f"🔍 File: database.py, Function: get_session; Fetching session {session_id}")
            result = await session.execute(select(Session).where(Session.id == session_id))
            return result.scalar_one_or_none()

    async def create_conversation(self, session_id: str) -> Conversation:
        """Create a new conversation for a session"""
        async with self.SessionLocal() as session:
            logger.info(
                f"💬 File: database.py, Function: create_conversation; Creating conversation for session {session_id}")
            conversation = Conversation(session_id=session_id)
            session.add(conversation)
            await session.commit()
            await session.refresh(conversation)
            return conversation

    async def create_conversation_item(self, conversation_id: str, role: MessageRole,
                                       content: Dict, audio_start_ms: int = None,
                                       audio_end_ms: int = None) -> ConversationItem:
        """Create a new conversation item"""
        async with self.SessionLocal() as session:
            logger.info(
                f"📝 File: database.py, Function: create_conversation_item; Adding item to conversation {conversation_id}")
            item = ConversationItem(
                conversation_id=conversation_id,
                role=role,
                content=content,
                audio_start_ms=audio_start_ms,
                audio_end_ms=audio_end_ms
            )
            session.add(item)
            await session.commit()
            await session.refresh(item)
            return item

    async def create_response(self, conversation_id: str) -> Response:
        """Create a new response"""
        async with self.SessionLocal() as session:
            logger.info(
                f"🤖 File: database.py, Function: create_response; Creating response for conversation {conversation_id}")
            response = Response(
                conversation_id=conversation_id,
                status=ResponseStatus.IN_PROGRESS
            )
            session.add(response)
            await session.commit()
            await session.refresh(response)
            return response

    async def update_response(self, response_id: str,
                              status: ResponseStatus = None,
                              usage_stats: Dict = None,
                              status_details: Dict = None) -> Response:
        """Update response status and usage statistics"""
        async with self.SessionLocal() as session:
            logger.info(f"📊 File: database.py, Function: update_response; Updating response {response_id}")
            result = await session.execute(select(Response).where(Response.id == response_id))
            response = result.scalar_one_or_none()

            if response:
                if status:
                    response.status = status
                if usage_stats:
                    response.total_tokens = usage_stats.get('total_tokens')
                    response.input_tokens = usage_stats.get('input_tokens')
                    response.output_tokens = usage_stats.get('output_tokens')
                    response.input_token_details = usage_stats.get('input_token_details')
                    response.output_token_details = usage_stats.get('output_token_details')
                if status_details:
                    response.status_details = status_details

                await session.commit()
                await session.refresh(response)

            return response

    async def get_conversation_items(self, conversation_id: str) -> List[ConversationItem]:
        """Get all items in a conversation"""
        async with self.SessionLocal() as session:
            logger.info(
                f"📜 File: database.py, Function: get_conversation_items; Fetching items for conversation {conversation_id}")
            result = await session.execute(
                select(ConversationItem)
                .where(ConversationItem.conversation_id == conversation_id)
                .order_by(ConversationItem.id)
            )
            return result.scalars().all()

    async def create_rate_limit(self, session_id: str, name: str, limit: int,
                                remaining: int, reset_seconds: float) -> RateLimit:
        """Create or update a rate limit for a session"""
        async with self.SessionLocal() as session:
            logger.info(
                f"⚡ File: database.py, Function: create_rate_limit; Creating/updating rate limit for session {session_id}")

            # Check if rate limit exists
            result = await session.execute(
                select(RateLimit)
                .where(RateLimit.session_id == session_id)
                .where(RateLimit.name == name)
            )
            rate_limit = result.scalar_one_or_none()

            if rate_limit:
                # Update existing rate limit
                rate_limit.limit = limit
                rate_limit.remaining = remaining
                rate_limit.reset_seconds = reset_seconds
            else:
                # Create new rate limit
                rate_limit = RateLimit(
                    id=f"rl_{uuid.uuid4().hex}",
                    session_id=session_id,
                    name=name,
                    limit=limit,
                    remaining=remaining,
                    reset_seconds=reset_seconds
                )
                session.add(rate_limit)

            await session.commit()
            await session.refresh(rate_limit)
            return rate_limit

    async def get_session_rate_limits(self, session_id: str) -> List[RateLimit]:
        """Get all rate limits for a session"""
        async with self.SessionLocal() as session:
            logger.info(
                f"📊 File: database.py, Function: get_session_rate_limits; Fetching rate limits for session {session_id}")
            result = await session.execute(
                select(RateLimit)
                .where(RateLimit.session_id == session_id)
                .order_by(RateLimit.name)
            )
            return result.scalars().all()

    async def reset_rate_limits(self, session_id: str, name: str) -> None:
        """Reset rate limits for a session"""
        async with self.SessionLocal() as session:
            logger.info(
                f"📊 File: database.py, Function: reset_rate_limits; Resetting rate limits for session {session_id}")
            await session.execute(await session.update(RateLimit).where(RateLimit.session_id == session_id).where(RateLimit.name == name).values(remaining=0))
            await session.commit()

    async def update_rate_limits(self, session_id: str, rate_limits: List[Dict]) -> List[RateLimit]:
        """Update rate limits from server event"""
        async with self.SessionLocal() as session:
            logger.info(
                f"📈 File: database.py, Function: update_rate_limits; Updating rate limits for session {session_id}")
            
            updated_limits = []

            for limit_data in rate_limits:
                rate_limit = await self.create_rate_limit(
                    session_id=session_id,
                    name=limit_data['name'],
                    limit=limit_data['limit'],
                    remaining=limit_data['remaining'],
                    reset_seconds=limit_data['reset_seconds']
                )
                updated_limits.append(rate_limit)

            return updated_limits


db = Database()
