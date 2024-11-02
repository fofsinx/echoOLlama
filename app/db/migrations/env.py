import asyncio
from logging.config import fileConfig
from sqlalchemy.engine import Connection
from alembic import context

from app.config import settings
from app.db.models import Base
from app.db.database import db
from app.utils.logger import logger

# this is the Alembic Config object
config = context.config

# Setup logging
fileConfig(config.config_file_name)

# Set target metadata
target_metadata = Base.metadata


# Override sqlalchemy.url with our async database URL
def get_url():
    return f'postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}'


config.set_main_option("sqlalchemy.url", get_url())


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode using the Database instance."""
    logger.info("🔄 File: env.py, Function: run_migrations_online; Running migrations")

    # Use the engine from our Database instance
    await db.connect()

    async with db.engine.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await db.disconnect()


def do_run_migrations(connection: Connection) -> None:
    """Execute migrations"""
    logger.info("🔄 File: env.py, Function: do_run_migrations; Executing migrations")

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        include_schemas=True,
        # Add transaction support
        transaction_per_migration=True,
        # Add retry logic for better reliability
        retry_on_errors=True
    )

    try:
        with context.begin_transaction():
            context.run_migrations()
        logger.info("✅ File: env.py, Function: do_run_migrations; Migrations completed successfully")
    except Exception as e:
        logger.error(f"❌ File: env.py, Function: do_run_migrations; Migration failed: {str(e)}")
        raise


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    logger.info("🔄 File: env.py, Function: run_migrations_offline; Running offline migrations")

    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        include_schemas=True
    )

    try:
        with context.begin_transaction():
            context.run_migrations()
        logger.info("✅ File: env.py, Function: run_migrations_offline; Offline migrations completed successfully")
    except Exception as e:
        logger.error(f"❌ File: env.py, Function: run_migrations_offline; Offline migration failed: {str(e)}")
        raise


print(
    "🔧 File: env.py; Alembic configuration loaded. Running in offline mode:", context.is_offline_mode()
)
if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
