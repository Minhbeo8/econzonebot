import nextcord
from nextcord.ext import commands
import logging
import math
from typing import List, Dict, Any

from core.config import COMMAND_PREFIX
from core.icons import ICON_HELP, ICON_MONEY_BAG, ICON_GAME, ICON_SHOP, ICON_INFO
from core.utils import try_send

logger = logging.getLogger(__name__)

# Số danh mục lệnh hiển thị trên mỗi trang của dropdown
CATEGORIES_PER_PAGE = 20

class HelpMenuView(nextcord.ui.View):
    def __init__(self, cogs_data: List[Dict[str, Any]], original_author: nextcord.User, bot: commands.Bot):
        super().__init__(timeout=180)
        self.cogs_data = cogs_data
        self.original_author = original_author
        self.bot = bot
        self.message = None
        
        self.current_category_page = 0
        self.total_category_pages = math.ceil(len(self.cogs_data) / CATEGORIES_PER_PAGE)

        self.update_view_components()

    def update_view_components(self):
        """Tạo lại các thành phần của View (dropdown, nút) dựa trên trang danh mục hiện tại."""
        self.clear_items()

        # --- Tạo Dropdown Menu ---
        start_index = self.current_category_page * CATEGORIES_PER_PAGE
        end_index = start_index + CATEGORIES_PER_PAGE
        page_cogs = self.cogs_data[start_index:end_index]

        options = [
            nextcord.SelectOption(label="Trang chính", description="Quay về menu trợ giúp chính.", emoji="🏠", value="main_menu")
        ]
        for cog in page_cogs:
            options.append(
                nextcord.SelectOption(label=cog["name"], description=cog["description"], emoji=cog["emoji"], value=cog["id"])
            )
        
        select_menu = nextcord.ui.Select(placeholder="Chọn một mục để xem...", options=options, custom_id="help_menu_select")
        select_menu.callback = self.on_select_callback
        self.add_item(select_menu)

        # --- Tạo các nút bấm phân trang danh mục ---
        prev_button = nextcord.ui.Button(label="◀️", style=nextcord.ButtonStyle.secondary, custom_id="prev_cat_page")
        prev_button.disabled = self.current_category_page == 0
        prev_button.callback = self.go_to_prev_page
        
        next_button = nextcord.ui.Button(label="▶️", style=nextcord.ButtonStyle.secondary, custom_id="next_cat_page")
        next_button.disabled = self.current_category_page >= self.total_category_pages - 1
        next_button.callback = self.go_to_next_page
        
        self.add_item(prev_button)
        self.add_item(next_button)

    async def interaction_check(self, interaction: nextcord.Interaction) -> bool:
        if interaction.user.id != self.original_author.id:
            await interaction.response.send_message("Đây không phải là menu của bạn!", ephemeral=True)
            return False
        return True

    async def go_to_prev_page(self, interaction: nextcord.Interaction):
        if self.current_category_page > 0:
            self.current_category_page -= 1
            self.update_view_components()
            # Khi chuyển trang danh mục, quay về embed chính
            main_embed = self._create_main_embed()
            await interaction.response.edit_message(embed=main_embed, view=self)

    async def go_to_next_page(self, interaction: nextcord.Interaction):
        if self.current_category_page < self.total_category_pages - 1:
            self.current_category_page += 1
            self.update_view_components()
            main_embed = self._create_main_embed()
            await interaction.response.edit_message(embed=main_embed, view=self)

    async def on_select_callback(self, interaction: nextcord.Interaction):
        try:
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
                await interaction.response.edit_message(embed=new_embed, view=self)

        except Exception as e:
            logger.error(f"Lỗi trong callback của HelpMenuView: {e}", exc_info=True)

    def _create_main_embed(self) -> nextcord.Embed:
        return nextcord.Embed(
            title=f"{ICON_HELP} Menu Trợ giúp",
            description="Chào mừng đến với EconZone! Vui lòng chọn một mục từ menu bên dưới để xem chi tiết các lệnh.",
            color=nextcord.Color.blue()
        ).set_footer(text=f"Trang danh mục {self.current_category_page + 1}/{self.total_category_pages}")

    def _create_cog_embed(self, cog_info: Dict[str, Any]) -> nextcord.Embed:
        embed = nextcord.Embed(title=f"{cog_info['emoji']} {cog_info['name']}", description=cog_info["description"], color=nextcord.Color.blue())
        for cmd_info in cog_info["commands"]:
            command_obj = self.bot.get_command(cmd_info["name"])
            if command_obj:
                usage = f"`{COMMAND_PREFIX}{command_obj.name} {command_obj.signature}`".strip()
                help_text = cmd_info.get("desc", "Chưa có mô tả.")
                embed.add_field(name=f"`{COMMAND_PREFIX}{command_obj.name}`", value=f"*{help_text}*\n**Cách dùng:** {usage}", inline=False)
        embed.set_footer(text=f"Trang danh mục {self.current_category_page + 1}/{self.total_category_pages}")
        return embed

class HelpSlashCommandCog(commands.Cog, name="Help Slash Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cogs_data = [
            {
                "id": "economy", "name": "Lệnh Kinh tế", "emoji": ICON_MONEY_BAG,
                "description": "Các lệnh liên quan đến tiền tệ, tài khoản.",
                "commands": [
                    {"name": "balance", "desc": "Xem số dư tất cả các ví của bạn hoặc người khác."},
                    {"name": "deposit", "desc": "Gửi Tiền từ Ví vào Bank."},
                    {"name": "withdraw", "desc": "Rút tiền từ Bank về Ví ."},
                    {"name": "transfer", "desc": "Chuyển tiền từ Bank của bạn cho người khác."}
                ]
            },
            {
                "id": "earning", "name": "Lệnh Kiếm tiền", "emoji": "💼",
                "description": "Các cách để kiếm thêm thu nhập.",
                "commands": [
                    {"name": "work", "desc": "Làm việc để kiếm Ecoin và kinh nghiệm."},
                    {"name": "daily", "desc": "Nhận thưởng hàng ngày."},
                    {"name": "crime", "desc": "Làm nhiệm vụ phi pháp, có rủi ro."},
                    {"name": "fish", "desc": "Câu cá để bán kiếm tiền."},
                    {"name": "rob", "desc": "Cướp tiền từ người chơi khác."},
                    {"name": "beg", "desc": "Ăn xin để nhận một ít tiền lẻ."}
                ]
            },
            {
                "id": "games", "name": "Lệnh Trò chơi", "emoji": ICON_GAME,
                "description": "Các trò chơi may rủi.",
                "commands": [
                    {"name": "coinflip", "desc": "Chơi tung đồng xu 50/50."},
                    {"name": "dice", "desc": "Đổ xúc xắc, thắng nếu tổng lớn hơn 7."},
                    {"name": "slots", "desc": "Quay máy xèng để thử vận may."}
                ]
            },
            {
                "id": "shop", "name": "Lệnh Cửa hàng", "emoji": ICON_SHOP,
                "description": "Các lệnh liên quan đến mua, bán và túi đồ.",
                "commands": [
                    {"name": "shop", "desc": "Hiển thị các vật phẩm đang bán."},
                    {"name": "buy", "desc": "Mua một vật phẩm từ cửa hàng."},
                    {"name": "sell", "desc": "Bán một vật phẩm từ túi đồ."},
                    {"name": "inventory", "desc": "Kiểm tra túi đồ của bạn."},
                    {"name": "use", "desc": "Sử dụng một vật phẩm tiêu thụ."}
                ]
            },
        ]

    @nextcord.slash_command(name="menu", description="Mở menu trợ giúp chính của bot.")
    async def menu_slash_command(self, interaction: nextcord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            
            view = HelpMenuView(self.cogs_data, interaction.user, self.bot)
            initial_embed = view._create_main_embed()

            await interaction.followup.send(embed=initial_embed, view=view, ephemeral=True)
            view.message = await interaction.original_message()

        except nextcord.errors.HTTPException as e:
            logger.warning(f"Lỗi khi phản hồi tương tác /menu (có thể do timeout): {e}")
            pass
        except Exception as e:
            logger.error(f"Lỗi không xác định trong /menu: {e}", exc_info=True)

def setup(bot: commands.Bot):
    bot.add_cog(HelpSlashCommandCog(bot))
