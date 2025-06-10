import nextcord
from nextcord.ext import commands, application_checks
import logging

# [SỬA] Xóa bỏ import từ core.database
from core.checks import check_is_bot_moderator_interaction
from core.utils import format_large_number
from core.icons import *

logger = logging.getLogger(__name__)

class ModToolsSlashCog(commands.Cog, name="Moderator Slash Tools"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("ModToolsSlashCog (SQLite Ready) initialized.")

    @nextcord.slash_command(name="mod", description="Các công cụ dành cho Moderator của Bot")
    async def mod(self, interaction: nextcord.Interaction):
        pass

    @mod.subcommand(name="set", description="Thiết lập một giá trị dữ liệu cụ thể cho người dùng.")
    async def set_group(self, interaction: nextcord.Interaction):
        pass

    @mod.subcommand(name="ping", description="Kiểm tra xem bạn có quyền Moderator của bot không.")
    @application_checks.check(check_is_bot_moderator_interaction)
    async def mod_ping(self, interaction: nextcord.Interaction):
        logger.info(f"MODERATOR ACTION: {interaction.user.id} đã sử dụng '/mod ping' thành công.")
        await interaction.response.send_message(
            f"{ICON_SUCCESS} {interaction.user.mention}, bạn có quyền Moderator/Owner!",
            ephemeral=True
        )

    @mod.subcommand(name="view_user", description="Xem chi tiết toàn bộ dữ liệu kinh tế của một người dùng.")
    @application_checks.check(check_is_bot_moderator_interaction)
    async def view_user(
        self, 
        interaction: nextcord.Interaction,
        user: nextcord.User = nextcord.SlashOption(
            name="user",
            description="Người dùng bạn muốn xem thông tin.",
            required=True
        )
    ):
        await interaction.response.defer(ephemeral=True)

        if not interaction.guild:
            await interaction.followup.send(f"{ICON_ERROR} Vui lòng dùng lệnh này trong một server.", ephemeral=True)
            return

        try:
            # [SỬA] Sử dụng self.bot.db để truy vấn CSDL SQLite
            global_profile = self.bot.db.get_or_create_global_user_profile(user.id)
            local_data = self.bot.db.get_or_create_user_local_data(user.id, interaction.guild.id)

            # [SỬA] Truy cập dữ liệu từ đối tượng sqlite3.Row
            bank_balance = global_profile['bank_balance']
            wanted_level = global_profile['wanted_level']
            level_global = global_profile['level_global']
            xp_global = global_profile['xp_global']

            earned = local_data['local_balance_earned']
            adadd = local_data['local_balance_adadd']
            level_local = local_data['level_local']
            xp_local = local_data['xp_local']

            embed = nextcord.Embed(
                title=f"{ICON_PROFILE} Dữ liệu Kinh tế của {user.name}",
                color=nextcord.Color.orange()
            )
            embed.set_thumbnail(url=user.display_avatar.url)
            embed.add_field(name="User ID", value=f"`{user.id}`", inline=False)

            embed.add_field(
                name=f"{ICON_LOCAL} Dữ liệu tại Server: {interaction.guild.name}",
                value=(
                    f"  {ICON_TIEN_SACH} Earned: `{format_large_number(earned)}`\n"
                    f"  {ICON_TIEN_LAU} Admin-add: `{format_large_number(adadd)}`\n"
                    f"  ✨ Level/XP Local: `{level_local}` / `{format_large_number(xp_local)}`"
                ),
                inline=True
            )

            embed.add_field(
                name=f"{ICON_GLOBAL} Dữ liệu Toàn cục",
                value=(
                    f"  {ICON_BANK} Bank: `{format_large_number(bank_balance)}`\n"
                    f"  🕵️ Wanted Level: `{wanted_level:.2f}`\n"
                    f"  ✨ Level/XP Global: `{level_global}` / `{format_large_number(xp_global)}`"
                ),
                inline=True
            )

            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.info(f"MODERATOR ACTION: {interaction.user.id} đã xem dữ liệu của user {user.id}.")

        except Exception as e:
            logger.error(f"Lỗi trong lệnh /mod view_user: {e}", exc_info=True)
            await interaction.followup.send(f"{ICON_ERROR} Đã xảy ra lỗi khi truy xuất dữ liệu.", ephemeral=True)

    @set_group.subcommand(name="balance", description="Thiết lập số dư tiền tệ cho một người dùng.")
    @application_checks.check(check_is_bot_moderator_interaction)
    async def set_balance(
        self,
        interaction: nextcord.Interaction,
        user: nextcord.User = nextcord.SlashOption(name="user", description="Người dùng cần chỉnh sửa.", required=True),
        balance_type: str = nextcord.SlashOption(name="type", description="Loại số dư muốn thay đổi.", required=True, choices={"Tiền Sạch (earned)": "earned", "Tiền Lậu (adadd)": "adadd", "Bank (global)": "bank"}),
        amount: int = nextcord.SlashOption(name="amount", description="Số tiền muốn thiết lập (số âm sẽ được đặt về 0).", required=True)
    ):
        await interaction.response.defer(ephemeral=True)
        final_amount = max(0, amount)

        try:
            original_value = 0
            db_balance_type = ""
            icon = ""
            
            # [SỬA] Sử dụng self.bot.db để cập nhật, không sửa dict nữa
            if balance_type == "bank":
                profile = self.bot.db.get_or_create_global_user_profile(user.id)
                original_value = profile['bank_balance']
                db_balance_type = 'bank_balance'
                icon = ICON_BANK
                self.bot.db.update_balance(user.id, None, db_balance_type, final_amount)
            else:
                if not interaction.guild:
                    await interaction.followup.send(f"{ICON_ERROR} Cần dùng lệnh trong server để set balance Local.", ephemeral=True)
                    return
                
                profile = self.bot.db.get_or_create_user_local_data(user.id, interaction.guild.id)
                if balance_type == "earned":
                    original_value = profile['local_balance_earned']
                    db_balance_type = 'local_balance_earned'
                    icon = ICON_TIEN_SACH
                else: # adadd
                    original_value = profile['local_balance_adadd']
                    db_balance_type = 'local_balance_adadd'
                    icon = ICON_TIEN_LAU
                self.bot.db.update_balance(user.id, interaction.guild.id, db_balance_type, final_amount)

            logger.info(f"MODERATOR ACTION: {interaction.user.id} đã set balance '{balance_type}' của {user.id} thành {final_amount}.")
            await interaction.followup.send(
                f"{ICON_SUCCESS} Đã cập nhật thành công!\n"
                f"  - **Người dùng:** {user.mention}\n"
                f"  - **Loại số dư:** `{balance_type.capitalize()}` {icon}\n"
                f"  - **Giá trị cũ:** `{format_large_number(original_value)}`\n"
                f"  - **Giá trị mới:** `{format_large_number(final_amount)}`",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Lỗi trong lệnh /mod set balance: {e}", exc_info=True)
            await interaction.followup.send(f"{ICON_ERROR} Đã xảy ra lỗi khi cập nhật dữ liệu.", ephemeral=True)

def setup(bot: commands.Bot):
    bot.add_cog(ModToolsSlashCog(bot))
