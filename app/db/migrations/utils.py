from alembic import command
from alembic.config import Config

from app.utils.logger import logger


class MigrationManager:
    def __init__(self, alembic_cfg_path: str = "alembic.ini"):
        self.alembic_cfg = Config(alembic_cfg_path)

    async def create_migration(self, message: str):
        """Create a new migration"""
        logger.info(f"📝 File: utils.py, Function: create_migration; Creating migration: {message}")
        try:
            await command.revision(self.alembic_cfg, autogenerate=True, message=message)
            logger.info("✅ File: utils.py, Function: create_migration; Migration created successfully")
        except Exception as e:
            logger.error(f"❌ File: utils.py, Function: create_migration; Failed to create migration: {str(e)}")
            raise

    async def upgrade(self, revision: str = "head"):
        """Upgrade to a later version"""
        logger.info(f"⬆️ File: utils.py, Function: upgrade; Upgrading to {revision}")
        try:
            await command.upgrade(self.alembic_cfg, revision)
            logger.info("✅ File: utils.py, Function: upgrade; Upgrade completed successfully")
        except Exception as e:
            logger.error(f"❌ File: utils.py, Function: upgrade; Upgrade failed: {str(e)}")
            raise

    async def downgrade(self, revision: str = "-1"):
        """Revert to a previous version"""
        logger.info(f"⬇️ File: utils.py, Function: downgrade; Downgrading to {revision}")
        try:
            await command.downgrade(self.alembic_cfg, revision)
            logger.info("✅ File: utils.py, Function: downgrade; Downgrade completed successfully")
        except Exception as e:
            logger.error(f"❌ File: utils.py, Function: downgrade; Downgrade failed: {str(e)}")
            raise

    async def show_current(self):
        """Show current revision"""
        logger.info("ℹ️ File: utils.py, Function: show_current; Showing current revision")
        try:
            await command.current(self.alembic_cfg)
        except Exception as e:
            logger.error(f"❌ File: utils.py, Function: show_current; Failed to show current revision: {str(e)}")
            raise


migration_manager = MigrationManager()
