import nextcord
from nextcord.ext import commands
import random
from datetime import datetime
import logging

from core.utils import try_send, require_travel_check
# SỬA: Import các biến cấu hình mới và đầy đủ
from core.config import (
    WORK_COOLDOWN, WORK_ENERGY_COST, WORK_HUNGER_COST,
    WORK_PAYOUT_MIN, WORK_PAYOUT_MAX, WORK_XP_LOCAL_MIN, WORK_XP_LOCAL_MAX,
    WORK_XP_GLOBAL_MIN, WORK_XP_GLOBAL_MAX
)
from core.leveling import check_and_process_levelup
from core.icons import (
    ICON_LOADING, ICON_WORK, ICON_MONEY_BAG, ICON_ERROR, 
    ICON_ECOIN, ICON_SURVIVAL, ICON_XP
)

logger = logging.getLogger(__name__)

class WorkCommandCog(commands.Cog, name="Work Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("WorkCommandCog (SQLite Ready) initialized.")

    @commands.command(name='work', aliases=['w'])
    @commands.guild_only()
    @require_travel_check
    async def work(self, ctx: commands.Context):
        author_id = ctx.author.id
        guild_id = ctx.guild.id
        
        try:
            local_data = self.bot.db.get_or_create_user_local_data(author_id, guild_id)

            if local_data['energy'] < WORK_ENERGY_COST:
                await try_send(ctx, content=f"{ICON_SURVIVAL} Bạn quá mệt mỏi để làm việc!")
                return
            if local_data['hunger'] < WORK_HUNGER_COST:
                await try_send(ctx, content=f"{ICON_SURVIVAL} Bạn quá đói để làm việc!")
                return

            now = datetime.now().timestamp()
            last_work = self.bot.db.get_cooldown(author_id, 'work')
            if last_work and now - last_work < WORK_COOLDOWN:
                time_left = str(datetime.fromtimestamp(last_work + WORK_COOLDOWN) - datetime.now()).split('.')[0]
                await try_send(ctx, content=f"{ICON_LOADING} Bạn cần nghỉ ngơi! Chờ: **{time_left}**.")
                return
            
            # SỬA: Lấy giá trị ngẫu nhiên từ config
            earnings = random.randint(WORK_PAYOUT_MIN, WORK_PAYOUT_MAX)
            xp_earned_local = random.randint(WORK_XP_LOCAL_MIN, WORK_XP_LOCAL_MAX)
            xp_earned_global = random.randint(WORK_XP_GLOBAL_MIN, WORK_XP_GLOBAL_MAX)
            
            self.bot.db.update_local_balance(author_id, guild_id, 'local_balance_earned', local_data['local_balance_earned'] + earnings)
            self.bot.db.update_xp(author_id, guild_id, xp_earned_local, xp_earned_global)
            self.bot.db.set_cooldown(author_id, 'work', now)
            self.bot.db.update_user_stats(author_id, guild_id, energy=local_data['energy'] - WORK_ENERGY_COST, hunger=local_data['hunger'] - WORK_HUNGER_COST)
            
            await try_send(
                ctx, 
                content=(
                    f"{ICON_WORK} {ctx.author.mention}, bạn làm việc chăm chỉ và nhận được:\n"
                    f"  {ICON_ECOIN} **{earnings:,}** Ecoin\n"
                    f"  {ICON_XP} **{xp_earned_local}** XP (Server) & **{xp_earned_global}** XP (Global)"
                )
            )

            updated_local = self.bot.db.get_or_create_user_local_data(author_id, guild_id)
            updated_global = self.bot.db.get_or_create_global_user_profile(author_id)
            await check_and_process_levelup(ctx, dict(updated_local), 'local')
            await check_and_process_levelup(ctx, dict(updated_global), 'global')

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'work' cho user {author_id}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi bạn đang làm việc.")

def setup(bot: commands.Bot):
    bot.add_cog(WorkCommandCog(bot))
