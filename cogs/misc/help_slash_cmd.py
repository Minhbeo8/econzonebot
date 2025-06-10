import nextcord
from nextcord.ext import commands
import logging
from typing import List, Dict, Any

from core.config import COMMAND_PREFIX
from core.icons import ICON_HELP, ICON_COMMAND_DETAIL, ICON_BANK, ICON_MONEY_BAG, ICON_GAME, ICON_SHOP, ICON_ADMIN, ICON_INFO, ICON_WARNING, ICON_ERROR
from core.utils import try_send

logger = logging.getLogger(__name__)

# --- View cho Menu ---
class HelpMenuView(nextcord.ui.View):
    def __init__(self, cogs_data: List[Dict[str, Any]], original_author: nextcord.User, bot: commands.Bot):
        super().__init__(timeout=180)
        self.cogs_data = cogs_data
        self.original_author = original_author
        self.bot = bot
        self.message = None

        options = [
            nextcord.SelectOption(label="Trang chính", description="Quay về menu trợ giúp chính.", emoji="🏠", value="main_menu")
        ]
        for cog in cogs_data:
            options.append(
                nextcord.SelectOption(label=cog["name"], description=cog["description"], emoji=cog["emoji"], value=cog["id"])
            )
        
        self.add_item(nextcord.ui.Select(placeholder="Chọn một mục để xem...", options=options, custom_id="help_menu_select"))

    async def interaction_check(self, interaction: nextcord.Interaction) -> bool:
        if interaction.user.id != self.original_author.id:
            await interaction.response.send_message("Đây không phải là menu của bạn!", ephemeral=True)
            return False
        return True

    async def callback(self, interaction: nextcord.Interaction):
        # Callback cho Select Menu
        try:
            await interaction.response.defer(ephemeral=True) # Defer để có thời gian xử lý
            
            selected_value = interaction.data['values'][0]
            new_embed = None

            if selected_value == "main_menu":
                new_embed = self._create_main_embed()
            else:
                for cog in self.cogs_data:
                    if cog["id"] == selected_value:
                        new_embed = self._create_cog_embed(cog)
                        break
            
            if new_embed and self.message:
                await self.message.edit(embed=new_embed, view=self)

        except Exception as e:
            logger.error(f"Lỗi trong callback của HelpMenuView: {e}", exc_info=True)


    def _create_main_embed(self) -> nextcord.Embed:
        return nextcord.Embed(
            title=f"{ICON_HELP} Menu Trợ giúp",
            description="Chào mừng đến với EconZone! Vui lòng chọn một mục từ menu bên dưới để xem chi tiết các lệnh.",
            color=nextcord.Color.blue()
        ).set_footer(text="Bot được phát triển bởi minhbeo8")

    def _create_cog_embed(self, cog_info: Dict[str, Any]) -> nextcord.Embed:
        embed = nextcord.Embed(title=f"{cog_info['emoji']} {cog_info['name']}", description=cog_info["description"], color=nextcord.Color.blue())
        for cmd in cog_info["commands"]:
            command_obj = self.bot.get_command(cmd)
            if command_obj:
                usage = f"`{COMMAND_PREFIX}{command_obj.name} {command_obj.signature}`".strip()
                help_text = command_obj.short_doc or "Chưa có mô tả."
                embed.add_field(name=f"`{COMMAND_PREFIX}{command_obj.name}`", value=f"{help_text}\n*Cách dùng: {usage}*", inline=False)
        return embed


# --- Cog chính ---
class HelpSlashCommandCog(commands.Cog, name="Help Slash Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Dữ liệu cho menu, bạn có thể dễ dàng thêm/bớt mục ở đây
        self.cogs_data = [
            {"id": "economy", "name": "Lệnh Kinh tế", "description": "Các lệnh liên quan đến tiền tệ, tài khoản.", "emoji": ICON_MONEY_BAG, "commands": ["balance", "deposit", "withdraw", "transfer"]},
            {"id": "earning", "name": "Lệnh Kiếm tiền", "description": "Các cách để kiếm thêm thu nhập.", "emoji": "💼", "commands": ["work", "daily", "crime", "fish", "rob", "beg"]},
            {"id": "games", "name": "Lệnh Trò chơi", "description": "Các trò chơi may rủi.", "emoji": ICON_GAME, "commands": ["coinflip", "dice", "slots"]},
            {"id": "shop", "name": "Lệnh Cửa hàng", "description": "Các lệnh liên quan đến mua, bán và túi đồ.", "emoji": ICON_SHOP, "commands": ["shop", "buy", "sell", "inventory"]},
        ]

    @nextcord.slash_command(name="menu", description="Mở menu trợ giúp chính của bot.")
    async def menu_slash_command(self, interaction: nextcord.Interaction):
        # [SỬA] Bọc toàn bộ logic trong try...except
        try:
            # Defer ngay lập tức để báo cho Discord rằng "tôi đã nhận được lệnh"
            await interaction.response.defer(ephemeral=True)

            initial_embed = nextcord.Embed(
                title=f"{ICON_INFO} Menu Trợ giúp",
                description="Chào mừng đến với EconZone! Vui lòng chọn một mục từ menu bên dưới để xem chi tiết các lệnh.",
                color=nextcord.Color.blue()
            )
            initial_embed.set_footer(text="Bot được phát triển bởi minhbeo8")
            
            view = HelpMenuView(self.cogs_data, interaction.user, self.bot)

            # Gửi tin nhắn trả lời bằng followup vì đã defer
            await interaction.followup.send(embed=initial_embed, view=view, ephemeral=True)
            view.message = await interaction.original_message()

        except nextcord.errors.HTTPException as e:
            # Ghi lại log khi có lỗi timeout hoặc double-ack, thay vì làm sập chương trình
            logger.warning(f"Lỗi khi phản hồi tương tác /menu (có thể do timeout): {e}")
            pass # Bỏ qua lỗi và không làm gì cả, bot vẫn chạy tiếp
        except Exception as e:
            # Bắt các lỗi không lường trước khác
            logger.error(f"Lỗi không xác định trong /menu: {e}", exc_info=True)

def setup(bot: commands.Bot):
    bot.add_cog(HelpSlashCommandCog(bot))
