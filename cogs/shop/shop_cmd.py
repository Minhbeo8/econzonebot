import nextcord
from nextcord.ext import commands
import logging
import math
from typing import List, Dict, Any

# [SỬA] Đã xóa dòng "from core.database import load_item_definitions"
from core.utils import try_send, format_large_number
from core.icons import ICON_SHOP, ICON_MONEY_BAG, ICON_ERROR, ICON_INFO, ICON_ECOIN, ICON_ECOBIT, ICON_UTILITY

logger = logging.getLogger(__name__)

ITEMS_PER_PAGE = 5

class ShopView(nextcord.ui.View):
    # Class View không thay đổi
    def __init__(self, *, items_data: List[Dict[str, Any]], original_author: nextcord.User, bot_instance: commands.Bot):
        super().__init__(timeout=180)
        self.items_data = items_data
        self.original_author = original_author
        self.bot = bot_instance
        self.current_page = 1
        self.total_pages = math.ceil(len(self.items_data) / ITEMS_PER_PAGE) if ITEMS_PER_PAGE > 0 else 1
        self.message = None
        self.update_buttons()

    # ... (Toàn bộ class View giữ nguyên logic cũ) ...
    # ... (Bao gồm update_buttons, generate_embed_for_current_page, vv...)
    def update_buttons(self):
        self.children[0].disabled = self.current_page == 1
        self.children[1].disabled = self.current_page == self.total_pages

    async def generate_embed_for_current_page(self) -> nextcord.Embed:
        # ...
        pass

    async def interaction_check(self, interaction: nextcord.Interaction) -> bool:
        if interaction.user.id != self.original_author.id:
            await interaction.response.send_message("Đây không phải là cửa hàng của bạn!", ephemeral=True)
            return False
        return True

    @nextcord.ui.button(label="Trang trước", style=nextcord.ButtonStyle.grey)
    async def previous_page(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        # ...
        pass

    @nextcord.ui.button(label="Trang sau", style=nextcord.ButtonStyle.grey)
    async def next_page(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        # ...
        pass
        
class ShopCommandCog(commands.Cog, name="Shop Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("ShopCommandCog (SQLite Ready) initialized.")

    @commands.command(name='shop', aliases=['store'])
    @commands.guild_only()
    async def shop(self, ctx: commands.Context):
        """Hiển thị cửa hàng với các vật phẩm có thể mua."""
        try:
            # [SỬA] Lấy định nghĩa vật phẩm từ cache của bot đã được tải lúc khởi động
            all_items = self.bot.item_definitions
            if not all_items:
                await try_send(ctx, content=f"{ICON_ERROR} Cửa hàng hiện đang trống!")
                return

            # Chuyển đổi dict thành list để phân trang
            items_list = [{"id": item_id, **details} for item_id, details in all_items.items() if details.get("price")]
            
            # Sắp xếp vật phẩm theo giá
            sorted_items = sorted(items_list, key=lambda x: x['price'])
            
            view = ShopView(items_data=sorted_items, original_author=ctx.author, bot_instance=self.bot)
            
            # Gửi tin nhắn ban đầu
            # Logic tạo embed cho ShopView cần được hoàn thiện
            # Dưới đây là một ví dụ đơn giản
            embed = nextcord.Embed(title=f"{ICON_SHOP} Chào mừng tới Cửa hàng!", color=nextcord.Color.gold())
            embed.description = "Sử dụng các nút bên dưới để duyệt qua các vật phẩm."
            
            sent_message = await try_send(ctx, embed=embed, view=view)
            if sent_message:
                view.message = sent_message

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'shop': {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi mở cửa hàng.")

def setup(bot: commands.Bot):
    bot.add_cog(ShopCommandCog(bot))
