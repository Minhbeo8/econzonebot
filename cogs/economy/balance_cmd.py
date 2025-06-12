import nextcord
from nextcord.ext import commands
from core.database_sqlite import Database
from core.icons import Icons # Sửa đổi

class BalanceCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    @nextcord.slash_command(name="balance", description="Kiểm tra số dư tài khoản của bạn hoặc người khác.")
    async def balance(self, interaction: nextcord.Interaction, user: nextcord.Member = None):
        target_user = user or interaction.user
        
        user_balance = self.db.get_balance(target_user.id)
        
        if not user_balance:
            # Sửa đổi
            await interaction.response.send_message(f"{Icons.error} Không tìm thấy dữ liệu cho người dùng này.", ephemeral=True)
            return

        embed = nextcord.Embed(
            title=f"Số dư của {target_user.display_name}",
            color=nextcord.Color.gold()
        )
        embed.set_thumbnail(url=target_user.display_avatar.url)
        
        # Sửa đổi
        embed.add_field(name=f"{Icons.wallet} Ví (Local)", value=f"`{user_balance['ecoin']:,}` {Icons.ecoin}\n`{user_balance['ecobit']:,}` {Icons.ecobit}", inline=True)
        embed.add_field(name=f"{Icons.bank} Ngân hàng (Global)", value=f"`{user_balance['bank']:,}` {Icons.ecoin}", inline=True)
        
        await interaction.response.send_message(embed=embed)

def setup(bot):
    bot.add_cog(BalanceCommand(bot))
