import nextcord
from nextcord.ext import commands
import random
import asyncio
from core.database_sqlite import Database
# Sửa đổi: import thêm hàm load_activities_data và format_time_long
from core.utils import format_time_long, load_activities_data
from core.icons import Icons

class WorkCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.cooldowns = {}
        # Sửa đổi: Tải dữ liệu hoạt động khi cog khởi chạy
        self.activities_data = load_activities_data()

    @nextcord.slash_command(name="work", description="Làm việc để kiếm Ecoin.")
    async def work(self, interaction: nextcord.Interaction):
        user_id = interaction.user.id
        
        cooldown_time = self.db.get_cooldown('work')
        if user_id in self.cooldowns and (asyncio.get_event_loop().time() - self.cooldowns[user_id]) < cooldown_time:
            remaining_time = cooldown_time - (asyncio.get_event_loop().time() - self.cooldowns[user_id])
            await interaction.response.send_message(f"{Icons.clock} Bạn vừa mới tan ca. Hãy nghỉ ngơi {format_time_long(int(remaining_time))} nữa.", ephemeral=True)
            return

        self.cooldowns[user_id] = asyncio.get_event_loop().time()

        # Sửa đổi: Lấy dữ liệu công việc từ file JSON
        if not self.activities_data or 'work' not in self.activities_data:
            await interaction.response.send_message(f"{Icons.error} Lỗi: Không thể tải dữ liệu công việc.", ephemeral=True)
            return
            
        jobs = self.activities_data['work']['jobs']
        selected_job = random.choice(jobs)
        
        job_name = selected_job['name']
        amount = random.randint(selected_job['min_earn'], selected_job['max_earn'])
        
        self.db.update_balance(user_id, amount, 'ecoin')
        
        embed = nextcord.Embed(
            title=f"{Icons.work} Làm việc chăm chỉ",
            description=f"Bạn đã làm công việc '{job_name}' và kiếm được `{amount}` {Icons.ecoin}.",
            color=nextcord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

def setup(bot):
    bot.add_cog(WorkCommand(bot))
