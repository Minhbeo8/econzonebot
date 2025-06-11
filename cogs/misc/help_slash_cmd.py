import nextcord
from nextcord.ext import commands
import logging
from typing import List, Dict, Any

from core.config import COMMAND_PREFIX
from core.icons import *
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

        # Tạo các lựa chọn cho menu dropdown
        options = [
            nextcord.SelectOption(label="Trang chính", description="Quay về menu trợ giúp chính.", emoji="🏠", value="main_menu")
        ]
        for cog in cogs_data:
            options.append(
                nextcord.SelectOption(label=cog["name"], description=cog["description"], emoji=cog["emoji"], value=cog["id"])
            )
        
        self.add_item(nextcord.ui.Select(placeholder="🔎 Chọn một danh mục để xem...", options=options, custom_id="help_menu_select"))

    async def interaction_check(self, interaction: nextcord.Interaction) -> bool:
        if interaction.user.id != self.original_author.id:
            await interaction.response.send_message("Đây không phải là menu của bạn!", ephemeral=True)
            return False
        return True
    
    # Hàm này sẽ được gọi khi người dùng chọn một mục trong dropdown
    @nextcord.ui.select(custom_id="help_menu_select")
    async def select_callback(self, select: nextcord.ui.Select, interaction: nextcord.Interaction):
        try:
            # Không cần defer vì edit_message là một dạng phản hồi
            
            selected_value = select.values[0]
            new_embed = None

            if selected_value == "main_menu":
                new_embed = self._create_main_embed()
            else:
                for cog in self.cogs_data:
                    if cog["id"] == selected_value:
                        new_embed = self._create_cog_embed(cog)
                        break
            
            if new_embed and self.message:
                # Cập nhật lại tin nhắn với nội dung mới
                await self.message.edit(embed=new_embed, view=self)
                # Phản hồi rỗng để Discord biết tương tác đã được xử lý
                await interaction.response.send_message("Đã cập nhật menu.", ephemeral=True, delete_after=0.1)


        except Exception as e:
            logger.error(f"Lỗi trong callback của HelpMenuView: {e}", exc_info=True)

    def _create_main_embed(self) -> nextcord.Embed:
        """Tạo embed cho trang chính."""
        return nextcord.Embed(
            title=f"{ICON_HELP} Menu Trợ giúp",
            description="Chào mừng đến với EconZone! Vui lòng chọn một mục từ menu bên dưới để xem chi tiết các lệnh.",
            color=nextcord.Color.blue()
        ).set_footer(text="Bot được phát triển bởi minhbeo8")

    def _create_cog_embed(self, cog_info: Dict[str, Any]) -> nextcord.Embed:
        """Tạo embed chi tiết cho một danh mục lệnh."""
        embed = nextcord.Embed(title=f"{cog_info['emoji']} {cog_info['name']}", description=cog_info["description"], color=nextcord.Color.blue())
        for cmd_name in cog_info["commands"]:
            command_obj = self.bot.get_command(cmd_name)
            if command_obj:
                usage = f"`{COMMAND_PREFIX}{command_obj.name} {command_obj.signature}`".strip()
                help_text = command_obj.short_doc or "Chưa có mô tả."
                embed.add_field(name=f"`{COMMAND_PREFIX}{command_obj.name}`", value=f"```{help_text}```", inline=False)
        return embed

# --- Cog chính ---
class HelpSlashCommandCog(commands.Cog, name="Help Slash Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Dữ liệu cho menu, bạn có thể dễ dàng thêm/bớt mục ở đây
        self.cogs_data = [
            {"id": "economy", "name": "Kinh tế & Tài khoản", "description": "Các lệnh liên quan đến tiền tệ, tài khoản.", "emoji": ICON_MONEY_BAG, "commands": ["balance", "deposit", "withdraw", "transfer", "bank"]},
            {"id": "earning", "name": "Kiếm tiền & Cơ hội", "description": "Các cách để kiếm thêm thu nhập.", "emoji": "💼", "commands": ["work", "daily", "crime", "fish", "rob", "beg"]},
            {"id": "games", "name": "Giải trí & Trò chơi", "description": "Các trò chơi may rủi.", "emoji": ICON_GAME, "commands": ["coinflip", "dice", "slots"]},
            {"id": "shop", "name": "Cửa hàng & Vật phẩm", "description": "Các lệnh liên quan đến mua, bán và túi đồ.", "emoji": ICON_SHOP, "commands": ["shop", "buy", "sell", "inventory", "use"]},
            {"id": "admin", "name": "Quản trị Server", "description": "Các lệnh dành cho Admin/Owner server.", "emoji": ICON_ADMIN, "commands": ["addmoney", "removemoney", "auto", "mutebot", "unmutebot"]},
        ]

    @nextcord.slash_command(name="menu", description="Mở menu trợ giúp chính của bot.")
    async def menu_slash_command(self, interaction: nextcord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)

            initial_embed = nextcord.Embed(
                title=f"{ICON_HELP} Menu Trợ giúp",
                description="Chào mừng đến với EconZone! Vui lòng chọn một mục từ menu bên dưới để xem chi tiết các lệnh.",
                color=nextcord.Color.blue()
            )
            initial_embed.set_footer(text="Bot được phát triển bởi minhbeo8")
            
            view = HelpMenuView(self.cogs_data, interaction.user, self.bot)

            await interaction.followup.send(embed=initial_embed, view=view, ephemeral=True)
            sent_message = await interaction.original_message()
            view.message = sent_message

        except nextcord.errors.HTTPException as e:
            logger.warning(f"Lỗi khi phản hồi tương tác /menu (có thể do timeout): {e}")
            pass
        except Exception as e:
            logger.error(f"Lỗi không xác định trong /menu: {e}", exc_info=True)

def setup(bot: commands.Bot):
    bot.add_cog(HelpSlashCommandCog(bot))
