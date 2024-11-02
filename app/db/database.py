from typing import Optional, List, Dict, Any
import asyncpg
import json
from app.config import settings


class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Initialize database connection pool"""
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                database=settings.DB_NAME,
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                min_size=5,
                max_size=20
            )

    async def disconnect(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()

    async def get_session(self, session_id: str) -> Dict:
        """Get session by ID"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """
                SELECT * FROM sessions 
                WHERE id = $1 AND status = 'active'
                """,
                session_id
            )

    async def create_message(self, session_id: str, role: str,
                             content: str, content_type: str,
                             metadata: Dict = None) -> Dict:
        """Create a new message"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """
                INSERT INTO messages 
                (session_id, role, content, content_type, metadata)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING *
                """,
                session_id, role, content, content_type,
                json.dumps(metadata or {})
            )

    async def get_messages(self, session_id: str) -> List[Dict]:
        """Get messages by session ID"""
        async with self.pool.acquire() as conn:
            return await conn.fetch(
                "SELECT * FROM messages WHERE session_id = $1", session_id
            )

    async def get_session_by_user_id(self, user_id: str) -> Dict:
        """Get session by user ID"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                "SELECT * FROM sessions WHERE user_id = $1", user_id
            )

    async def get_session_by_id(self, session_id: str) -> Dict:
        """Get session by ID"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                "SELECT * FROM sessions WHERE id = $1", session_id
            )

    async def update_session(self, session_id: str, status: str) -> Dict:
        """Update session status"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                "UPDATE sessions SET status = $1 WHERE id = $2 RETURNING *", status, session_id
            )

    async def get_user_by_id(self, user_id: str) -> Dict:
        """Get user by ID"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                "SELECT * FROM users WHERE id = $1", user_id
            )

    async def get_user_by_email(self, email: str) -> Dict:
        """Get user by email"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                "SELECT * FROM users WHERE email = $1", email
            )

    async def create_user(self, email: str, password: str) -> Dict:
        """Create a new user"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                "INSERT INTO users (email, password) VALUES ($1, $2) RETURNING *", email, password
            )

    async def create_session(self, session_data: Dict) -> Dict:
        """Create a new session"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow("INSERT INTO sessions (data) VALUES ($1) RETURNING *", session_data)

    async def get_rate_limits(self, client_id):
        pass

    async def update_rate_limits(self, client_id, current_session_id):
        pass

    async def update_session_activity(self, current_session_id, current_time):
        pass


db = Database()
