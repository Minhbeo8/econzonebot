# bot/cogs/earn/beg_cmd.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime
import logging

from core.database import (
    load_economy_data,
    get_or_create_global_user_profile,
    save_economy_data
)
from core.utils import try_send, get_time_left_str
from core.config import CURRENCY_SYMBOL, BEG_COOLDOWN
from core.icons import ICON_LOADING, ICON_GIFT, ICON_MONEY_BAG, ICON_WARNING, ICON_INFO, ICON_ERROR
from core.travel_manager import handle_travel_event

logger = logging.getLogger(__name__)

class BegCommandCog(commands.Cog, name="Beg Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info(f"{ICON_INFO} BegCommandCog initialized.")

    @commands.command(name='beg', aliases=['b'])
    async def beg(self, ctx: commands.Context):
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server.")
            return

        author_id = ctx.author.id
        guild_id = ctx.guild.id

        economy_data = load_economy_data()
        user_profile = get_or_create_global_user_profile(economy_data, author_id)

        # --- Kiểm tra Last Active Guild ---
        if user_profile.get("last_active_guild_id") != guild_id:
            await handle_travel_event(ctx, self.bot)
            logger.info(f"User {author_id} has 'traveled' to guild {guild_id}.")
        user_profile["last_active_guild_id"] = guild_id

        time_left = get_time_left_str(user_profile.get("cooldowns", {}).get("beg", 0), BEG_COOLDOWN)
        if time_left:
            await try_send(ctx, content=f"{ICON_LOADING} Đừng xin liên tục thế chứ! Lệnh `beg` chờ: **{time_left}**.")
            return

        user_profile.setdefault("cooldowns", {})["beg"] = datetime.now().timestamp()

        if random.random() < 0.7: 
            earnings = random.randint(10, 100)
            user_profile["global_balance"] = user_profile.get("global_balance", 0) + earnings

            await try_send(ctx, content=f"{ICON_GIFT} Một người tốt bụng đã cho {ctx.author.mention} **{earnings:,}** {CURRENCY_SYMBOL}! {ICON_MONEY_BAG} Ví Toàn Cục: **{user_profile['global_balance']:,}**")
        else:
            await try_send(ctx, content=f"{ICON_WARNING} Không ai cho {ctx.author.mention} tiền cả. Thử lại vận may sau nhé! 😢")
            
        save_economy_data(economy_data)

def setup(bot: commands.Bot):
    bot.add_cog(BegCommandCog(bot))
