import nextcord
from nextcord.ext import commands, tasks
import logging
import os

from core.config import (
    SURVIVAL_TICK_RATE_MINUTES,
    SURVIVAL_STAT_DECAY,
    SURVIVAL_HEALTH_REGEN
)

logger = logging.getLogger(__name__)

class SurvivalTaskCog(commands.Cog, name="Survival Task"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Chỉ chạy task này nếu bot đang ở chế độ SQLite
        db_type = getattr(bot, 'db_type', 'json')
        if db_type == 'sqlite':
            self.stat_decay_loop.start()
            logger.info("Survival Task has been started (SQLite mode).")
        else:
            logger.info("Survival Task is INACTIVE (not in SQLite mode).")

    def cog_unload(self):
        """Hủy task khi cog được unload."""
        if self.stat_decay_loop.is_running():
            self.stat_decay_loop.cancel()

    @tasks.loop(minutes=SURVIVAL_TICK_RATE_MINUTES)
    async def stat_decay_loop(self):
        """
        Task chạy nền để xử lý giảm chỉ số sinh tồn và hồi máu.
        """
        logger.info("SURVIVAL_TASK: Performing survival stat decay and regen...")
        try:
            # Gọi hàm duy nhất để CSDL tự xử lý mọi thứ
            await self.bot.loop.run_in_executor(
                None, 
                self.bot.db.perform_survival_decay, 
                SURVIVAL_STAT_DECAY, 
                SURVIVAL_HEALTH_REGEN
            )
            logger.info("SURVIVAL_TASK: Stat decay and regen successful.")
        except Exception as e:
            logger.error(f"Error in Survival Decay Task: {e}", exc_info=True)

    @stat_decay_loop.before_loop
    async def before_stat_decay_task(self):
        """Đợi cho đến khi bot sẵn sàng trước khi bắt đầu vòng lặp."""
        await self.bot.wait_until_ready()


def setup(bot: commands.Bot):
    bot.add_cog(SurvivalTaskCog(bot))
