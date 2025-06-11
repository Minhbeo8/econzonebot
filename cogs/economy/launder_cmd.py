import nextcord
from nextcord.ext import commands
import logging

# SỬA: Đổi 'core.checks' thành 'core.travel_manager'
from core.travel_manager import require_travel_check 
from core.config import LAUNDER_TAX_RATE
from core.utils import format_large_number
from core.icons import ICON_ECOIN, ICON_ECOBIT, ICON_SUCCESS, ICON_ERROR

logger = logging.getLogger(__name__)

class LaunderCommandCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="launder", aliases=["ruatien"])
    @commands.guild_only()
    @require_travel_check
    async def launder(self, ctx: commands.Context, *, amount_str: str):
        """Rửa tiền Ecobit bẩn thành Ecoin sạch, có mất phí."""
        user_id = ctx.author.id
        guild_id = ctx.guild.id

        local_data = self.bot.db.get_or_create_user_local_data(user_id, guild_id)
        ecobit_balance = local_data['local_balance_adadd']
        
        try:
            if amount_str.lower() == 'all':
                amount_to_launder = ecobit_balance
            else:
                amount_to_launder = int(amount_str)
        except ValueError:
            await ctx.send(f"{ICON_ERROR} Vui lòng nhập một số tiền hợp lệ hoặc 'all'.")
            return

        if ecobit_balance <= 0:
            await ctx.send(f"{ICON_ERROR} Bạn không có {ICON_ECOBIT} **Ecobit** nào để rửa.")
            return

        if amount_to_launder <= 0:
            await ctx.send(f"{ICON_ERROR} Số tiền cần rửa phải lớn hơn 0.")
            return

        if amount_to_launder > ecobit_balance:
            await ctx.send(f"{ICON_ERROR} Bạn không có đủ **{format_large_number(amount_to_launder)}** {ICON_ECOBIT} **Ecobit** để rửa. Bạn chỉ có **{format_large_number(ecobit_balance)}**.")
            return

        tax = int(amount_to_launder * LAUNDER_TAX_RATE)
        amount_received = amount_to_launder - tax

        self.bot.db.update_local_balance(user_id, guild_id, 'local_balance_adadd', -amount_to_launder)
        self.bot.db.update_local_balance(user_id, guild_id, 'local_balance_earned', amount_received)
        
        logger.info(f"User {user_id} in guild {guild_id} laundered {amount_to_launder} ecobits, paid {tax} tax, received {amount_received} ecoins.")

        embed = nextcord.Embed(
            title="✅ Giao Dịch Rửa Tiền Thành Công",
            description=(
                f"Bạn đã rửa thành công **{format_large_number(amount_to_launder)}** {ICON_ECOBIT} **Ecobit**.\n"
                f"Sau khi trừ đi **{LAUNDER_TAX_RATE * 100:.0f}%** phí, bạn nhận được **{format_large_number(amount_received)}** {ICON_ECOIN} **Ecoin**."
            ),
            color=nextcord.Color.green()
        )
        await ctx.send(embed=embed)

    @launder.error
    async def launder_error(self, ctx: commands.Context, error):
        """Xử lý lỗi riêng cho lệnh launder."""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"{ICON_ERROR} Bạn chưa nhập số tiền cần rửa. \n**Cách dùng:** `{self.bot.command_prefix}launder <số_tiền|all>`")
        else:
            logger.error(f"Lỗi không xác định trong lệnh launder: {error}", exc_info=True)
            await ctx.send(f"{ICON_ERROR} Đã có lỗi xảy ra. Vui lòng thử lại sau.")


def setup(bot: commands.Bot):
    bot.add_cog(LaunderCommandCog(bot))
