import nextcord
from nextcord.ext import commands
import random
import asyncio
from core.database_sqlite import Database
from core.utils import require_travel_check
from core.utils import format_time_long, load_activities_data
from core.icons import Icons

class CrimeCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.cooldowns = {}
        # Sửa đổi: Tải dữ liệu hoạt động khi cog khởi chạy
        self.activities_data = load_activities_data()

    @nextcord.slash_command(name="crime", description="Thực hiện một phi vụ phạm pháp để kiếm Ecobit.")
    @require_travel_check
    async def crime(self, interaction: nextcord.Interaction):
        user_id = interaction.user.id

        cooldown_time = self.db.get_cooldown('crime')
        if user_id in self.cooldowns and (asyncio.get_event_loop().time() - self.cooldowns[user_id]) < cooldown_time:
            remaining_time = cooldown_time - (asyncio.get_event_loop().time() - self.cooldowns[user_id])
            await interaction.response.send_message(f"{Icons.clock} Bạn vừa mới đi tù về, hãy chờ {format_time_long(int(remaining_time))} nữa.", ephemeral=True)
            return

        self.cooldowns[user_id] = asyncio.get_event_loop().time()

        # Sửa đổi: Lấy dữ liệu các phi vụ từ file JSON
        if not self.activities_data or 'crime' not in self.activities_data:
            await interaction.response.send_message(f"{Icons.error} Lỗi: Không thể tải dữ liệu phạm tội.", ephemeral=True)
            return

        scenarios = self.activities_data['crime']['scenarios']
        selected_scenario = random.choice(scenarios)
        
        scenario_name = selected_scenario['name']
        success_chance = selected_scenario['success_chance']

        if random.random() < success_chance:
            min_earn = selected_scenario['min_earn']
            max_earn = selected_scenario['max_earn']
            amount = random.randint(min_earn, max_earn)
            
            self.db.update_balance(user_id, amount, 'ecobit')
            embed = nextcord.Embed(
                title=f"{Icons.crime} Phi vụ thành công",
                description=f"Bạn đã thực hiện '{scenario_name}' trót lọt và kiếm được `{amount}` {Icons.ecobit}.",
                color=nextcord.Color.dark_purple()
            )
        else:
            min_fine = self.activities_data['crime']['failure_fine']['min']
            max_fine = self.activities_data['crime']['failure_fine']['max']
            fine = random.randint(min_fine, max_fine)

            self.db.update_balance(user_id, -fine, 'ecoin')
            embed = nextcord.Embed(
                title=f"{Icons.error} Bị cảnh sát tóm",
                description=f"Bạn đã thất bại trong phi vụ '{scenario_name}' và bị phạt `{fine}` {Icons.ecoin}.",
                color=nextcord.Color.red()
            )

        await interaction.response.send_message(embed=embed)

def setup(bot):
    bot.add_cog(CrimeCommand(bot))
