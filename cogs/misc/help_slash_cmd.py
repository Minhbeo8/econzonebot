import nextcord
from nextcord.ext import commands
import logging
import math
from typing import List, Dict, Any

from core.config import COMMAND_PREFIX
from core.icons import ICON_HELP, ICON_MONEY_BAG, ICON_GAME, ICON_SHOP, ICON_INFO, ICON_CRIME_SCENE, ICON_BACKPACK

logger = logging.getLogger(__name__)

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
        self.clear_items()
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
            main_embed = self._create_main_embed()
            await interaction.response.edit_message(embed=main_embed, view=self)

    async def go_to_next_page(self, interaction: nextcord.Interaction):
        if self.current_category_page < self.total_category_pages - 1:
            self.current_category_page += 1
            self.update_view_components()
            main_embed = self._create_main_embed()
            await interaction.response.edit_message(embed=main_embed, view=self)

    async def on_select_callback(self, interaction: nextcord.Interaction):
        selected_value = interaction.data['values'][0]
        new_embed = self._create_main_embed() if selected_value == "main_menu" else self._create_cog_embed(next((cog for cog in self.cogs_data if cog["id"] == selected_value), None))
        
        if new_embed and self.message:
            await interaction.response.edit_message(embed=new_embed, view=self)

    def _create_main_embed(self) -> nextcord.Embed:
        return nextcord.Embed(
            title=f"{ICON_HELP} Menu Trợ giúp",
            description="Chào mừng đến với EconZone! Vui lòng chọn một mục từ menu bên dưới để xem chi tiết các lệnh.",
            color=nextcord.Color.blue()
        ).set_footer(text=f"Trang danh mục {self.current_category_page + 1}/{self.total_category_pages}")

    def _create_cog_embed(self, cog_info: Dict[str, Any]) -> nextcord.Embed:
        embed = nextcord.Embed(title=f"{cog_info['emoji']} {cog_info['name']}", description=cog_info["description"], color=nextcord.Color.blue())
        for cmd_info in cog_info["commands"]:
            usage_text = cmd_info.get("usage", "")
            # Sửa lại để hiển thị tên lệnh cùng với phím tắt nếu có
            cmd_name_with_alias = f"{cmd_info['name']}"
            if "alias" in cmd_info:
                cmd_name_with_alias += f" ({cmd_info['alias']})"
            
            usage = f"`{COMMAND_PREFIX}{cmd_name_with_alias} {usage_text}`".strip()
            help_text = cmd_info.get("desc", "Chưa có mô tả.")
            embed.add_field(name=f"`{COMMAND_PREFIX}{cmd_info['name']}`", value=f"*{help_text}*\n**Cách dùng:** {usage}", inline=False)
        embed.set_footer(text=f"[]: tham số tùy chọn, <>: tham số bắt buộc")
        return embed

class HelpSlashCommandCog(commands.Cog, name="Help Slash Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # SỬA: Sắp xếp lại và thêm "cách dùng" chi tiết cho tất cả các lệnh
        self.cogs_data = [
            {
                "id": "economy", "name": "Lệnh Kinh tế", "emoji": ICON_MONEY_BAG,
                "description": "Các lệnh liên quan đến tiền tệ, tài khoản.",
                "commands": [
                    {"name": "balance", "alias": "bal", "desc": "Xem số dư ví của bạn hoặc người khác.", "usage": "[@người_dùng]"},
                    {"name": "deposit", "alias": "dep", "desc": "Gửi Tiền từ Ví vào Bank.", "usage": "<số_tiền|all>"},
                    {"name": "withdraw", "alias": "wd", "desc": "Rút tiền từ Bank về Ví.", "usage": "<số_tiền|all>"},
                    {"name": "transfer", "alias": "tf", "desc": "Chuyển tiền từ Bank của bạn cho người khác.", "usage": "<@người_nhận> <số_tiền>"},
                    {"name": "leaderboard", "alias": "lb", "desc": "Xem bảng xếp hạng tài sản trong server.", "usage": ""},
                ]
            },
            {
                "id": "earning", "name": "Lệnh Kiếm tiền", "emoji": "💼",
                "description": "Các cách để kiếm thêm thu nhập.",
                "commands": [
                    {"name": "work", "alias": "w", "desc": "Làm việc để kiếm Ecoin và kinh nghiệm.", "usage": ""},
                    {"name": "daily", "alias": "d", "desc": "Nhận thưởng hàng ngày.", "usage": ""},
                    {"name": "fish", "desc": "Câu cá để bán kiếm tiền.", "usage": ""},
                    {"name": "beg", "alias": "b", "desc": "Ăn xin để nhận một ít tiền lẻ.", "usage": ""},
                ]
            },
            {
                "id": "underworld", "name": "Thế Giới Ngầm", "emoji": ICON_CRIME_SCENE,
                "description": "Các hoạt động phi pháp và rủi ro.",
                "commands": [
                    {"name": "crime", "desc": "Làm nhiệm vụ phi pháp để kiếm Ecobit.", "usage": ""},
                    {"name": "rob", "desc": "Cướp tiền từ ví của người chơi khác.", "usage": "<@nạn_nhân>"},
                    {"name": "launder", "alias": "ruatien", "desc": "Rửa tiền lậu (Ecobit) thành tiền sạch (Ecoin).", "usage": "<số_tiền|all>"},
                ]
            },
            {
                "id": "shop", "name": "Cửa hàng & Vật phẩm", "emoji": ICON_BACKPACK,
                "description": "Các lệnh liên quan đến mua, bán và sử dụng vật phẩm.",
                "commands": [
                    {"name": "shop", "desc": "Hiển thị các vật phẩm đang bán.", "usage": ""},
                    {"name": "buy", "desc": "Mua một vật phẩm từ cửa hàng.", "usage": "<tên_vật_phẩm> [số_lượng]"},
                    {"name": "sell", "desc": "Bán một vật phẩm từ túi đồ.", "usage": "<tên_vật_phẩm> [số_lượng]"},
                    {"name": "inventory", "alias": "inv", "desc": "Kiểm tra túi đồ của bạn hoặc người khác.", "usage": "[@người_dùng]"},
                    {"name": "use", "desc": "Sử dụng một vật phẩm tiêu thụ.", "usage": "<tên_vật_phẩm>"}
                ]
            },
            {
                "id": "games", "name": "Lệnh Trò chơi", "emoji": ICON_GAME,
                "description": "Các trò chơi may rủi để kiếm tiền.",
                "commands": [
                    {"name": "coinflip", "alias": "cf", "desc": "Chơi tung đồng xu 50/50.", "usage": "<số_tiền> <mặt_cược>"},
                    {"name": "dice", "desc": "Đổ xúc xắc, thắng nếu tổng lớn hơn 7.", "usage": "<số_tiền>"},
                    {"name": "slots", "desc": "Quay máy xèng để thử vận may.", "usage": "<số_tiền>"}
                ]
            },
        ]

    @nextcord.slash_command(name="menu", description="Mở menu trợ giúp chính của bot.")
    async def menu_slash_command(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        view = HelpMenuView(self.cogs_data, interaction.user, self.bot)
        initial_embed = view._create_main_embed()
        await interaction.followup.send(embed=initial_embed, view=view, ephemeral=True)
        view.message = await interaction.original_message()

def setup(bot: commands.Bot):
    bot.add_cog(HelpSlashCommandCog(bot))
