import nextcord
from nextcord.ext import commands
import random
import asyncio
from core.database_sqlite import Database
# Sửa đổi: import thêm hàm load_activities_data
from core.utils import format_time_long, load_activities_data
from core.icons import Icons

class FishCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.cooldowns = {}
        # Sửa đổi: Tải dữ liệu hoạt động khi cog khởi chạy
        self.activities_data = load_activities_data()

    @nextcord.slash_command(name="fish", description="Đi câu cá để kiếm thêm thu nhập.")
    async def fish(self, interaction: nextcord.Interaction):
        user_id = interaction.user.id

        cooldown_time = self.db.get_cooldown('fish')
        if user_id in self.cooldowns and (asyncio.get_event_loop().time() - self.cooldowns[user_id]) < cooldown_time:
            remaining_time = cooldown_time - (asyncio.get_event_loop().time() - self.cooldowns[user_id])
            await interaction.response.send_message(f"{Icons.clock} Cá chưa kịp lớn, hãy chờ {format_time_long(int(remaining_time))} nữa.", ephemeral=True)
            return

        self.cooldowns[user_id] = asyncio.get_event_loop().time()

        # Sửa đổi: Lấy dữ liệu các loại cá từ file JSON
        if not self.activities_data or 'fish' not in self.activities_data:
            await interaction.response.send_message(f"{Icons.error} Lỗi: Không thể tải dữ liệu câu cá.", ephemeral=True)
            return

        fishes = self.activities_data['fish']['fishes']
        caught_fish = random.choice(fishes)
        
        fish_name = caught_fish['name']
        value = caught_fish['value']
        
        self.db.update_balance(user_id, value, 'ecoin')

        embed = nextcord.Embed(
            title=f"{Icons.fish} Câu cá thành công!",
            description=f"Bạn đã câu được một con **{fish_name}** và bán được `{value}` {Icons.ecoin}.",
            color=nextcord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)

def setup(bot):
    bot.add_cog(FishCommand(bot))
