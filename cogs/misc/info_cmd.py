import nextcord
from nextcord.ext import commands
import logging
from core.utils import get_player_title, format_large_number, try_send
from core.checks import is_guild_owner_check
from core.icons import *
from core.leveling import xp_for_level

logger = logging.getLogger(__name__)

def create_progress_bar(value: int, max_value: int, length: int = 10) -> str:
    """Tạo một thanh tiến trình bằng text."""
    if max_value == 0:
        return "N/A"
    percent = value / max_value
    filled_length = int(length * percent)
    bar = '█' * filled_length + '░' * (length - filled_length)
    return f"[{bar}]"

async def is_guild_owner_interaction(interaction: nextcord.Interaction) -> bool:
    if not interaction.guild:
        return False
    return interaction.user.id == interaction.guild.owner_id

class InfoView(nextcord.ui.View):
    def __init__(self, interaction: nextcord.Interaction, is_mafia: bool, is_police: bool, is_owner: bool):
        super().__init__(timeout=None)
        self.interaction_user = interaction.user
        if is_mafia:
            self.add_item(nextcord.ui.Button(label="🏛️ Chợ Đen", style=nextcord.ButtonStyle.grey, custom_id="dash_blackmarket"))
        if is_police:
            self.add_item(nextcord.ui.Button(label="⚖️ Bắt giữ", style=nextcord.ButtonStyle.primary, custom_id="dash_arrest"))
        if is_owner:
            self.add_item(nextcord.ui.Button(label="👑 Thưởng Ecobit", style=nextcord.ButtonStyle.blurple, custom_id="dash_addmoney"))
    
    async def interaction_check(self, interaction: nextcord.Interaction) -> bool:
        if interaction.data.get("custom_id") == "dash_addmoney":
            if not await is_guild_owner_interaction(interaction):
                await interaction.response.send_message("Chỉ chủ server mới có thể dùng nút này!", ephemeral=True)
                return False
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("Đây không phải là bảng thông tin của bạn!", ephemeral=True)
            return False
        return True

class InfoCommandCog(commands.Cog, name="Info Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("InfoCommandCog initialized.")

    @nextcord.slash_command(name="info", description="Xem bảng thông tin cá nhân của bạn.")
    async def info(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)

        if not interaction.guild:
            await interaction.followup.send(f"{ICON_ERROR} Lệnh này chỉ hoạt động trong server.", ephemeral=True)
            return

        user = interaction.user
        global_profile = self.bot.db.get_or_create_global_user_profile(user.id)
        local_data = self.bot.db.get_or_create_user_local_data(user.id, interaction.guild.id)
        
        is_owner = await is_guild_owner_interaction(interaction)
        
        title_text = get_player_title(local_data['level_local'], global_profile['wanted_level'])
        embed = nextcord.Embed(
            title=f"{ICON_PROFILE} Hồ Sơ Kinh Tế của {user.display_name}",
            description=f"**Chức danh:** {title_text}",
            color=user.color
        )
        embed.set_thumbnail(url=user.display_avatar.url)

        # --- CỘT 1: THÔNG TIN ---
        xp_local_needed = xp_for_level(local_data['level_local'])
        info_column_text = (
            f"**Tài sản**\n"
            f"{ICON_ECOIN} Ecoin: `{format_large_number(local_data['local_balance_earned'])}`\n"
            f"{ICON_ECOBIT} Ecobit: `{format_large_number(local_data['local_balance_adadd'])}`\n"
            f"{ICON_BANK_MAIN} Bank: `{format_large_number(global_profile['bank_balance'])}`\n\n"
            f"**Cấp độ Server (Lv.{local_data['level_local']})**\n"
            f"`{format_large_number(local_data['xp_local'])}/{format_large_number(xp_local_needed)}` {create_progress_bar(local_data['xp_local'], xp_local_needed)}\n\n"
            f"**Sinh tồn**\n"
            f"{ICON_HEALTH} Máu: `{local_data['health']}/100`\n"
            f"{ICON_HUNGER} Độ no: `{local_data['hunger']}/100`\n"
            f"{ICON_ENERGY} Năng lượng: `{local_data['energy']}/100`"
        )
        embed.add_field(name="Thông Tin", value=info_column_text, inline=True)

        # --- CỘT 2: THÀNH TỰU ---
        achievements_text = ""
        if is_owner:
            achievements_text += "👑 **Nhà Sáng Lập**\n*Người tạo ra thế giới này.*\n\n"
        
        # (Trong tương lai, chúng ta có thể thêm các thành tựu khác vào đây)

        if not achievements_text:
            achievements_text = "_Chưa có thành tựu nào._"

        embed.add_field(name="Thành Tựu", value=achievements_text, inline=True)

        embed.set_footer(text=f"ID: {user.id} • Dữ liệu tại server {interaction.guild.name}")

        view = InfoView(interaction, is_mafia=False, is_police=False, is_owner=is_owner)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

def setup(bot: commands.Bot):
    bot.add_cog(InfoCommandCog(bot))
