# minhbeo8/econzonebot/Minhbeo8-econzonebot-b4ca6d7847536c7240ef6a17c68866ffdaf98915/cogs/test_slash_cog.py

import nextcord
from nextcord.ext import commands
import time

from core.icons import Icons
# Sửa đổi quan trọng: Import BOT_VERSION từ file config an toàn
from core.config import BOT_VERSION

class TestCommandsCog(commands.Cog, name="Test Commands"):
    """Cog chứa các lệnh dùng để kiểm tra hoạt động của bot."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Gắn version vào bot object để có thể truy cập từ bất cứ đâu qua self.bot.version
        self.bot.version = BOT_VERSION
        print(f"{Icons.info} [COG] TestCommandsCog đã được tải.")

    @nextcord.slash_command(name="test", description="Lệnh cha cho các lệnh test.")
    async def test(self, interaction: nextcord.Interaction):
        """
        Lệnh này sẽ không bao giờ được thực thi, nó chỉ dùng để nhóm các lệnh con.
        """
        pass

    @test.subcommand(name="ping", description="Kiểm tra độ trễ của bot tới Discord.")
    async def ping(self, interaction: nextcord.Interaction):
        """Hiển thị độ trễ hiện tại của bot."""
        start_time = time.time()
        # Gửi một tin nhắn tạm thời để tính toán độ trễ
        message = await interaction.response.send_message(f"{Icons.loading} Đang đo độ trễ...", ephemeral=True)
        end_time = time.time()

        # Tính toán độ trễ
        latency = (end_time - start_time) * 1000  # Độ trễ API
        ws_latency = self.bot.latency * 1000      # Độ trễ WebSocket

        embed = nextcord.Embed(
            title=f"{Icons.bot} Pong!",
            color=nextcord.Color.green()
        )
        embed.add_field(name="Độ trễ API", value=f"`{latency:.2f}ms`", inline=True)
        embed.add_field(name="Độ trễ WebSocket", value=f"`{ws_latency:.2f}ms`", inline=True)
        
        # Chỉnh sửa tin nhắn ban đầu với kết quả
        await interaction.edit_original_message(content=None, embed=embed)

    @test.subcommand(name="info", description="Hiển thị thông tin chi tiết về bot.")
    async def info(self, interaction: nextcord.Interaction):
        """Hiển thị thông tin về phiên bản, nhà phát triển."""
        embed = nextcord.Embed(
            title=f"{Icons.bot} Thông tin Bot EconZone",
            description="Một bot kinh tế đa năng được xây dựng trên nền tảng Nextcord.",
            color=nextcord.Color.blue()
        )
        # Sử dụng self.bot.version đã được gán lúc khởi tạo
        embed.add_field(name="Phiên bản", value=f"`{self.bot.version}`", inline=True)
        embed.add_field(name="Thư viện", value="`Nextcord`", inline=True)
        embed.add_field(name="Người phát triển", value="`minhbeo`", inline=True)
        embed.set_footer(text=f"Bot được khởi chạy và hoạt động trên {len(self.bot.guilds)} máy chủ.")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


def setup(bot: commands.Bot):
    """Hàm bắt buộc để tải Cog."""
    bot.add_cog(TestCommandsCog(bot))
