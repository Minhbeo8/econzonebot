import nextcord
from nextcord.ext import commands
import random
from datetime import datetime
import logging

from core.utils import try_send, format_relative_timestamp
# SỬA: Import các biến cấu hình mới và đầy đủ
from core.config import (
    DAILY_COOLDOWN, DAILY_REWARD_MIN, DAILY_REWARD_MAX,
    DAILY_XP_LOCAL_MIN, DAILY_XP_LOCAL_MAX, DAILY_XP_GLOBAL_MIN, DAILY_XP_GLOBAL_MAX
)
from core.leveling import check_and_process_levelup
from core.icons import ICON_LOADING, ICON_GIFT, ICON_MONEY_BAG, ICON_ERROR, ICON_TIEN_SACH, ICON_XP

logger = logging.getLogger(__name__)

class DailyCommandCog(commands.Cog, name="Daily Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("DailyCommandCog (SQLite Ready) initialized.")

    @commands.command(name='daily', aliases=['d'])
    @commands.guild_only()
    async def daily(self, ctx: commands.Context):
        author_id = ctx.author.id
        guild_id = ctx.guild.id
        
        try:
            now = datetime.now().timestamp()
            last_daily = self.bot.db.get_cooldown(author_id, 'daily')
            
            if last_daily and now < last_daily + DAILY_COOLDOWN:
                cooldown_end_timestamp = last_daily + DAILY_COOLDOWN             
                relative_time_str = format_relative_timestamp(cooldown_end_timestamp)
                
                await try_send(ctx, content=f"{ICON_LOADING} Bạn đã nhận thưởng ngày hôm nay rồi! Hãy quay lại sau ({relative_time_str}).")
                return
            
            local_data = self.bot.db.get_or_create_user_local_data(author_id, guild_id)
            
            # SỬA: Lấy giá trị ngẫu nhiên từ config
            bonus = random.randint(DAILY_REWARD_MIN, DAILY_REWARD_MAX)
            xp_earned_local = random.randint(DAILY_XP_LOCAL_MIN, DAILY_XP_LOCAL_MAX)
            xp_earned_global = random.randint(DAILY_XP_GLOBAL_MIN, DAILY_XP_GLOBAL_MAX)

            self.bot.db.update_local_balance(author_id, guild_id, 'local_balance_earned', local_data['local_balance_earned'] + bonus)
            self.bot.db.update_xp(author_id, guild_id, xp_earned_local, xp_earned_global)
            self.bot.db.set_cooldown(author_id, 'daily', now)
            
            updated_local_data = self.bot.db.get_or_create_user_local_data(author_id, guild_id)
            total_local_balance = updated_local_data['local_balance_earned'] + updated_local_data['local_balance_adadd']
            
            await try_send(
                ctx, 
                content=(
                    f"{ICON_GIFT} {ctx.author.mention}, bạn đã nhận phần thưởng hàng ngày:\n"
                    f"  {ICON_TIEN_SACH} **{bonus:,}** Tiền Sạch\n"
                    f"  {ICON_XP} **{xp_earned_local}** XP (Server) & **{xp_earned_global}** XP (Global)\n"
                    f"Tổng Ví Local của bạn giờ là: **{total_local_balance:,}** {ICON_MONEY_BAG}"
                )
            )

            global_profile = self.bot.db.get_or_create_global_user_profile(author_id)
            await check_and_process_levelup(ctx, dict(updated_local_data), 'local')
            await check_and_process_levelup(ctx, dict(global_profile), 'global')

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'daily' cho user {author_id}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi khi bạn nhận thưởng hàng ngày.")

def setup(bot: commands.Bot):
    bot.add_cog(DailyCommandCog(bot))
