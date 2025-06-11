import nextcord
from nextcord.ext import commands
import logging
import random # Thêm thư viện random

from core.travel_manager import require_travel_check 
# SỬA: Import 2 biến mới
from core.config import LAUNDER_TAX_RATE_MIN, LAUNDER_TAX_RATE_MAX
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

        # SỬA: Tính toán tỉ lệ thuế ngẫu nhiên cho mỗi lần giao dịch
        actual_tax_rate = random.uniform(LAUNDER_TAX_RATE_MIN, LAUNDER_TAX_RATE_MAX)
        tax = int(amount_to_launder * actual_tax_rate)
        amount_received = amount_to_launder - tax

        self.bot.db.update_local_balance(user_id, guild_id, 'local_balance_adadd', -amount_to_launder)
        self.bot.db.update_local_balance(user_id, guild_id, 'local_balance_earned', amount_received)
        
        logger.info(f"User {user_id} laundered {amount_to_launder} ecobits with tax rate {actual_tax_rate:.2%}, paid {tax} tax, received {amount_received} ecoins.")

        embed = nextcord.Embed(
            title="✅ Giao Dịch Rửa Tiền Thành Công",
            # SỬA: Hiển thị tỉ lệ thuế ngẫu nhiên đã áp dụng
            description=(
                f"Bạn đã đưa **{format_large_number(amount_to_launder)}** {ICON_ECOBIT} **Ecobit** vào máy giặt.\n"
                f"Tỉ lệ thuế ngẫu nhiên lần này là **{actual_tax_rate:.1%}**.\n"
                f"Kết quả, bạn nhận về **{format_large_number(amount_received)}** {ICON_ECOIN} **Ecoin** sạch."
            ),
            color=nextcord.Color.green()
        )
        await ctx.send(embed=embed)

    @launder.error
    async def launder_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"{ICON_ERROR} Bạn chưa nhập số tiền cần rửa. \n**Cách dùng:** `{self.bot.command_prefix}launder <số_tiền|all>`")
        else:
            logger.error(f"Lỗi không xác định trong lệnh launder: {error}", exc_info=True)
            await ctx.send(f"{ICON_ERROR} Đã có lỗi xảy ra. Vui lòng thử lại sau.")

def setup(bot: commands.Bot):
    bot.add_cog(LaunderCommandCog(bot))
