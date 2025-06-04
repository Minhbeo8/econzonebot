# bot/cogs/misc/help_slash_cmd.py
import nextcord
from nextcord.ext import commands

# Import các thành phần cần thiết từ package 'core'
from core.utils import try_send
from core.config import (
    COMMAND_PREFIX, # Cần COMMAND_PREFIX để hiển thị trong help
    WORK_COOLDOWN, DAILY_COOLDOWN, BEG_COOLDOWN, ROB_COOLDOWN, 
    CRIME_COOLDOWN, FISH_COOLDOWN, SLOTS_COOLDOWN, CF_COOLDOWN, DICE_COOLDOWN
)
from core.icons import ( # Import các icon bạn muốn dùng
    ICON_HELP, ICON_COMMAND_DETAIL, ICON_BANK, ICON_MONEY_BAG, 
    ICON_GAME, ICON_SHOP, ICON_ADMIN, ICON_INFO, ICON_WARNING, ICON_ERROR
)


class HelpSlashCommandCog(commands.Cog, name="Help Slash Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="help", description=f"{ICON_INFO} Hiển thị thông tin trợ giúp cho các lệnh của bot.")
    async def help_slash_command(self,
                                 interaction: nextcord.Interaction,
                                 command_name: str = nextcord.SlashOption(
                                     name="lệnh", 
                                     description="Tên lệnh prefix bạn muốn xem chi tiết (ví dụ: work, balance).",
                                     required=False,
                                     default=None
                                 )):
        """Hiển thị danh sách các lệnh hoặc thông tin chi tiết về một lệnh (prefix) cụ thể."""
        
        await interaction.response.defer(ephemeral=True) # Quan trọng: Defer trước khi xử lý
        prefix = COMMAND_PREFIX
        
        if not command_name: # Hiển thị menu trợ giúp chung
            embed = nextcord.Embed(
                title=f"{ICON_HELP} Menu Trợ Giúp - Bot Kinh Tế",
                description=(
                    f"Chào mừng bạn đến với Bot Kinh Tế! Dưới đây là các lệnh bạn có thể sử dụng.\n"
                    f"Để xem chi tiết một lệnh, dùng `/help lệnh <tên_lệnh>` (ví dụ: `/help lệnh work`).\n"
                    f"*Lưu ý: Hầu hết các lệnh đều có tên gọi tắt (alias) được liệt kê trong chi tiết lệnh.*\n"
                    f"Quản trị viên có thể dùng `{prefix}auto` để bật/tắt lệnh không cần prefix trong một kênh."
                ),
                color=nextcord.Color.dark_theme(),
            )
            
            embed.add_field(name=f"{ICON_BANK} Tài Khoản & Tổng Quan",
                            value="`balance` `bank` `deposit` `withdraw` `transfer` `leaderboard` `richest` `inventory`",
                            inline=False)
            embed.add_field(name=f"{ICON_MONEY_BAG} Kiếm Tiền & Cơ Hội", # Dùng ICON_MONEY_BAG ví dụ
                            value="`work` `daily` `beg` `crime` `fish` `rob`",
                            inline=False)
            embed.add_field(name=f"{ICON_GAME} Giải Trí & Cờ Bạc",
                            value="`slots` `coinflip` `dice`",
                            inline=False)
            embed.add_field(name=f"{ICON_SHOP} Cửa Hàng Vật Phẩm",
                            value="`shop` `buy` `sell`",
                            inline=False)
            embed.add_field(name=f"{ICON_ADMIN} Quản Trị Server (Lệnh Prefix)",
                            value=f"`{prefix}addmoney` `{prefix}removemoney` `{prefix}auto` `{prefix}mutebot` `{prefix}unmutebot`",
                            inline=False)
            
            embed.set_footer(text=f"Bot được phát triển bởi MinhBeo8. Gõ /help lệnh <tên_lệnh> để biết thêm chi tiết.")
            await try_send(interaction, embed=embed, ephemeral=True) 
        else:
            cmd_name_to_find = command_name.lower().lstrip(prefix) 
            command_obj = self.bot.get_command(cmd_name_to_find)
            
            if not command_obj:
                await try_send(interaction, content=f"{ICON_WARNING} Không tìm thấy lệnh prefix nào có tên là `{command_name}`. Hãy chắc chắn bạn nhập đúng tên lệnh (ví dụ: `work`, `balance` hoặc tên gọi tắt của nó).", ephemeral=True)
                return

            embed = nextcord.Embed(title=f"{ICON_COMMAND_DETAIL} Chi tiết lệnh: {prefix}{command_obj.name}", color=nextcord.Color.green())
            
            help_text = command_obj.help 
            if not help_text:
                help_text = command_obj.short_doc or "Lệnh này chưa có mô tả chi tiết." 
            embed.description = help_text

            usage = f"`{prefix}{command_obj.name} {command_obj.signature}`".strip()
            embed.add_field(name="📝 Cách sử dụng", value=usage, inline=False)

            if command_obj.aliases:
                aliases_str = ", ".join([f"`{prefix}{alias}`" for alias in command_obj.aliases])
                embed.add_field(name="🏷️ Tên gọi khác (Aliases)", value=aliases_str, inline=False)
            else:
                embed.add_field(name="🏷️ Tên gọi khác (Aliases)", value="Lệnh này không có tên gọi tắt.", inline=False)

            manual_cooldown_commands = {
                "work": WORK_COOLDOWN, "daily": DAILY_COOLDOWN, "beg": BEG_COOLDOWN,
                "rob": ROB_COOLDOWN, "crime": CRIME_COOLDOWN, "fish": FISH_COOLDOWN,
                "slots": SLOTS_COOLDOWN, "coinflip": CF_COOLDOWN, "dice": DICE_COOLDOWN
            }
            if command_obj.name in manual_cooldown_commands:
                cd_seconds = manual_cooldown_commands[command_obj.name]
                if cd_seconds >= 3600 and cd_seconds % 3600 == 0: cd_text = f"{cd_seconds // 3600} giờ"
                elif cd_seconds >= 60 and cd_seconds % 60 == 0: cd_text = f"{cd_seconds // 60} phút"
                else: cd_text = f"{cd_seconds} giây"
                embed.add_field(name="⏳ Thời gian chờ (Cooldown)", value=cd_text, inline=False)

            if command_obj.name in ["addmoney", "removemoney"]:
                embed.add_field(name="🔑 Yêu cầu", value="Chỉ Chủ Server (Người tạo server).", inline=False)
            elif command_obj.name in ["auto", "mutebot", "unmutebot"]:
                embed.add_field(name="🔑 Yêu cầu", value="Quyền `Administrator` trong server.", inline=False)
            
            await try_send(interaction, embed=embed, ephemeral=True)

def setup(bot: commands.Bot):
    bot.add_cog(HelpSlashCommandCog(bot))
