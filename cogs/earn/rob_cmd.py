# bot/cogs/earn/rob_cmd.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime
import logging

from core.database import get_or_create_global_user_profile, get_or_create_user_local_data
from core.utils import try_send, require_travel_check
from core.config import ROB_COOLDOWN, ROB_SUCCESS_RATE, ROB_FINE_RATE, ROB_ENERGY_COST, ROB_HUNGER_COST
from core.icons import ICON_LOADING, ICON_ERROR, ICON_INFO, ICON_ROB, ICON_MONEY_BAG, ICON_SURVIVAL

logger = logging.getLogger(__name__)

class RobCommandCog(commands.Cog, name="Rob Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("RobCommandCog (v4 - Refactored) initialized.")

    @commands.command(name='rob', aliases=['steal'])
    @commands.guild_only()
    @require_travel_check
    async def rob(self, ctx: commands.Context, target: nextcord.Member):
        if target.bot or target.id == ctx.author.id:
            await try_send(ctx, content=f"{ICON_ERROR} Không thể cướp người chơi này.")
            return

        author_id = ctx.author.id
        target_id = target.id
        guild_id = ctx.guild.id

        try:
            # [SỬA] Sử dụng cache
            economy_data = self.bot.economy_data
            author_global_profile = get_or_create_global_user_profile(economy_data, author_id)
            target_global_profile = get_or_create_global_user_profile(economy_data, target_id)
            author_local_data = get_or_create_user_local_data(author_global_profile, guild_id)
            target_local_data = get_or_create_user_local_data(target_global_profile, guild_id)

            # Kiểm tra chỉ số sinh tồn
            stats = author_local_data.get("survival_stats")
            if stats["energy"] < ROB_ENERGY_COST:
                await try_send(ctx, content=f"{ICON_SURVIVAL} Bạn quá mệt để cướp!")
                return
            if stats["hunger"] < ROB_HUNGER_COST:
                await try_send(ctx, content=f"{ICON_SURVIVAL} Đói quá, không chạy nổi để cướp!")
                return

            # Kiểm tra Cooldown
            now = datetime.now().timestamp()
            last_rob = author_global_profile.get("cooldowns", {}).get("rob", 0)
            if now - last_rob < ROB_COOLDOWN:
                time_left = str(datetime.fromtimestamp(last_rob + ROB_COOLDOWN) - datetime.now()).split('.')[0]
                await try_send(ctx, content=f"{ICON_LOADING} Cảnh sát đang rình! Lệnh `rob` còn chờ: **{time_left}**.")
                return

            # Trừ chỉ số, đặt cooldown
            stats["energy"] = max(0, stats["energy"] - ROB_ENERGY_COST)
            stats["hunger"] = max(0, stats["hunger"] - ROB_HUNGER_COST)
            author_global_profile.setdefault("cooldowns", {})["rob"] = now

            victim_balance = target_local_data["local_balance"]["earned"] + target_local_data["local_balance"]["adadd"]
            if victim_balance < 200:
                await try_send(ctx, content=f"{ICON_INFO} {target.mention} quá nghèo để cướp.")
                return

            if random.random() < ROB_SUCCESS_RATE:
                robbed_amount = random.randint(int(victim_balance * 0.1), int(victim_balance * 0.3))
                robbed_amount = min(robbed_amount, victim_balance)
                author_local_data["local_balance"]["earned"] += robbed_amount

                earned_deducted = min(target_local_data["local_balance"]["earned"], robbed_amount)
                adadd_deducted = robbed_amount - earned_deducted
                target_local_data["local_balance"]["earned"] -= earned_deducted
                target_local_data["local_balance"]["adadd"] -= adadd_deducted

                await try_send(ctx, content=f"{ICON_ROB} Bạn đã cướp được **{robbed_amount:,}** {ICON_MONEY_BAG} từ {target.mention}!")
            else:
                fine_amount = int(author_local_data["local_balance"]["earned"] * ROB_FINE_RATE)
                fine_amount = min(fine_amount, author_local_data["local_balance"]["earned"])
                author_local_data["local_balance"]["earned"] -= fine_amount

                await try_send(ctx, content=f"👮 {ICON_ERROR} Bạn đã bị bắt và bị phạt **{fine_amount:,}** {ICON_MONEY_BAG} từ Ví Local của bạn.")

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'rob' cho user {author_id}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi khi thực hiện hành vi cướp.")

def setup(bot: commands.Bot):
    bot.add_cog(RobCommandCog(bot))
