# bot/cogs/misc/dashboard_cmd.py
import nextcord
from nextcord.ext import commands, application_checks
import logging

from core.database import get_or_create_global_user_profile, get_or_create_user_local_data, load_economy_data
from core.utils import get_player_title, format_large_number, is_guild_owner_interaction
from core.icons import * # Import tất cả icon

logger = logging.getLogger(__name__)

class DashboardView(nextcord.ui.View):
    """View động chứa các nút bấm hành động theo vai trò."""
    def __init__(self, interaction: nextcord.Interaction, local_data: dict, is_owner: bool):
        super().__init__(timeout=None)
        self.interaction_user = interaction.user

        # Thêm các nút dựa trên vai trò/trạng thái
        if local_data.get("is_mafia", False):
            self.add_item(nextcord.ui.Button(label="🏛️ Chợ Đen", style=nextcord.ButtonStyle.grey, custom_id="dash_blackmarket"))
            self.add_item(nextcord.ui.Button(label="🔫 Đe dọa", style=nextcord.ButtonStyle.red, custom_id="dash_extort"))
        
        if local_data.get("is_police", False):
            self.add_item(nextcord.ui.Button(label="⚖️ Bắt giữ", style=nextcord.ButtonStyle.primary, custom_id="dash_arrest"))
            self.add_item(nextcord.ui.Button(label="🔎 Điều tra", style=nextcord.ButtonStyle.secondary, custom_id="dash_investigate"))

        if is_owner:
            self.add_item(nextcord.ui.Button(label="👑 Thưởng Ecobit", style=nextcord.ButtonStyle.blurple, custom_id="dash_addmoney"))
        
        # (Thêm các nút khác cho Bác sĩ, Trợ lý... ở đây)

    async def interaction_check(self, interaction: nextcord.Interaction) -> bool:
        return interaction.user.id == self.interaction_user.id
        # Logic callback cho các nút này sẽ gọi các lệnh tương ứng

class DashboardCommandCog(commands.Cog, name="Dashboard Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("DashboardCommandCog initialized.")

    @nextcord.slash_command(name="dashboard", description="Xem bảng thông tin cá nhân và các hành động của bạn.")
    async def dashboard(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)

        if not interaction.guild:
            await interaction.followup.send(f"{ICON_ERROR} Lệnh này chỉ hoạt động trong server.", ephemeral=True)
            return

        user = interaction.user
        economy_data = load_economy_data()
        global_profile = get_or_create_global_user_profile(economy_data, user.id)
        local_data = get_or_create_user_local_data(global_profile, interaction.guild.id)
        
        # Tạo Embed thông tin
        embed = nextcord.Embed(title=f"Bảng điều khiển của {user.name}", color=user.color)
        embed.set_thumbnail(url=user.display_avatar.url)
        
        # Chức danh động
        title = get_player_title(local_data['level_local'], global_profile['wanted_level'])
        embed.add_field(name="Chức danh tại Server", value=title, inline=False)
        
        # Tài chính
        embed.add_field(
            name="Tài chính",
            value=f"{ICON_ECOIN} **Ecoin:** `{format_large_number(local_data['local_balance']['earned'])}`\n"
                  f"{ICON_ECOBIT} **Ecobit:** `{format_large_number(local_data['local_balance']['adadd'])}`\n"
                  f"{ICON_BANK_MAIN} **Bank:** `{format_large_number(global_profile['bank_balance'])}`",
            inline=True
        )

        # Sinh tồn
        stats = local_data['survival_stats']
        embed.add_field(
            name="Sinh tồn",
            value=f"❤️ **Máu:** `{stats['health']}/100`\n"
                  f"🍔 **Độ no:** `{stats['hunger']}/100`\n"
                  f"⚡ **Năng lượng:** `{stats['energy']}/100`",
            inline=True
        )
        
        # Trạng thái
        embed.add_field(
            name="Trạng thái",
            value=f"🕵️ **Điểm Nghi ngờ:** `{global_profile['wanted_level']:.2f}`\n"
                  f"🎟️ **Tickets:** `{len(local_data['tickets'])}`",
            inline=True
        )

        # Tạo View với các nút bấm động
        is_owner = await is_guild_owner_interaction(interaction)
        view = DashboardView(interaction, local_data, is_owner)

        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

def setup(bot: commands.Bot):
    bot.add_cog(DashboardCommandCog(bot))
