import nextcord
from nextcord.ext import commands, tasks
import logging
import os
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)
DB_SYNC_INTERVAL_MINUTES = 15
REPO_PATH = "./data"
COMMIT_MSG = "Automatic DB sync"

class DatabaseSyncTaskCog(commands.Cog, name="Database Sync Task"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_type = os.getenv("DATABASE_TYPE", "json").lower()
        if self.db_type == 'sqlite':
            # Tạo một task riêng để chạy setup, vì __init__ không phải là async
            self.setup_task = self.bot.loop.create_task(self.setup_repository())
        else:
            logger.info("Database Sync Task is INACTIVE (not in SQLite mode).")

    def cog_unload(self):
        if hasattr(self, 'sync_database_task') and self.sync_database_task.is_running():
            self.sync_database_task.cancel()
        if hasattr(self, 'setup_task') and not self.setup_task.done():
            self.setup_task.cancel()

    async def run_shell_command(self, command: str, cwd: str = REPO_PATH):
        """Chạy một lệnh shell và trả về kết quả."""
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_message = stderr.decode().strip()
            if "nothing to commit" not in error_message and "up-to-date" not in error_message:
                 logger.error(f"Shell command failed: {command}\nStderr: {error_message}")
                 return False
            else:
                 logger.info(f"Shell command info: {command}\nStderr: {error_message}")

        stdout_message = stdout.decode().strip()
        if stdout_message:
            logger.info(f"Shell command stdout: {stdout_message}")
        return True

    async def force_sync(self):
        """Hàm thực hiện logic sao lưu, có thể được gọi từ bất cứ đâu."""
        if not os.path.exists(os.path.join(REPO_PATH, 'econzone.sqlite')):
            logger.warning("DB_SYNC_TASK: econzone.sqlite not found. Skipping sync.")
            return False

        logger.info("DB_SYNC_TASK: Forcing database sync...")
        
        await self.run_shell_command("git add econzone.sqlite")
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await self.run_shell_command(f"git commit --allow-empty -m \"{COMMIT_MSG} at {current_time}\"")
        
        if await self.run_shell_command("git push origin main -f"):
             logger.info("DB_SYNC_TASK: Force sync to GitHub successful.")
             return True
        else:
             logger.error("DB_SYNC_TASK: Force sync to GitHub failed.")
             return False

    @tasks.loop(minutes=DB_SYNC_INTERVAL_MINUTES)
    async def sync_database_task(self):
        logger.info("DB_SYNC_TASK: Running scheduled sync...")
        await self.force_sync() # Vòng lặp giờ chỉ cần gọi hàm force_sync

    @sync_database_task.before_loop
    async def before_sync(self):
        await self.bot.wait_until_ready()

def setup(bot: commands.Bot):
    bot.add_cog(DatabaseSyncTaskCog(bot))
