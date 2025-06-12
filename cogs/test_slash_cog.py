# minhbeo8/econzonebot/Minhbeo8-econzonebot-b4ca6d7847536c7240ef6a17c68866ffdaf98915/cogs/test_slash_cog.py

import nextcord
from nextcord.ext import commands
# Sửa lại import: Lấy BOT_VERSION từ core.config thay vì core.bot
from core.config import BOT_VERSION
from core.icons import Icons 

class TestSlashCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="test", description="Test bot functionality.")
    async def test_slash(self, interaction: nextcord.Interaction):
        """Lệnh test chính."""
        pass

    @test_slash.subcommand(name="ping", description="Kiểm tra độ trễ của bot.")
    async def ping(self, interaction: nextcord.Interaction):
        latency = self.bot.latency * 1000  # Convert to ms
        embed = nextcord.Embed(
            title=f"{Icons.bot} Pong!",
            description=f"Độ trễ của bot là: `{latency:.2f}ms`",
            color=nextcord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    @test_slash.subcommand(name="info", description="Hiển thị thông tin về bot.")
    async def info(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(
            title=f"{Icons.admin} Thông tin Bot",
            description="Đây là bot kinh tế cho EconZone.",
            color=nextcord.Color.blue()
        )
        embed.add_field(name="Phiên bản", value=f"`{BOT_VERSION}`", inline=True)
        embed.add_field(name="Thư viện", value="`Nextcord`", inline=True)
        embed.add_field(name="Người phát triển", value="`minhbeo`", inline=True)
        
        await interaction.response.send_message(embed=embed)

def setup(bot):
    bot.add_cog(TestSlashCog(bot))
