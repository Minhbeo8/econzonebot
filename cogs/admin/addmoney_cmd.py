import nextcord
from nextcord.ext import commands
from core.database_sqlite import Database
from core.checks import is_bot_owner
from core.icons import Icons # SỬA ĐỔI

class AddMoney(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    @commands.command(name="addmoney")
    @is_bot_owner()
    async def add_money(self, ctx, user: nextcord.Member, amount: int, currency_type: str = "ecoin"):
        amount = abs(amount)
        if currency_type.lower() not in ["ecoin", "ecobit"]:
            # SỬA ĐỔI
            await ctx.send(f"{Icons.error} Loại tiền tệ không hợp lệ. Vui lòng chọn `ecoin` hoặc `ecobit`.")
            return

        self.db.update_balance(user.id, amount, currency_type)
        
        # SỬA ĐỔI
        currency_icon = Icons.ecoin if currency_type.lower() == "ecoin" else Icons.ecobit
        
        embed = nextcord.Embed(
            title=f"{Icons.success} Cộng tiền thành công", # SỬA ĐỔI
            description=f"Đã cộng `{amount}` {currency_icon} cho {user.mention}.",
            color=nextcord.Color.green()
        )
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(AddMoney(bot))
