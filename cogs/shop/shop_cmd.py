import nextcord
from nextcord.ext import commands
import logging
import math
from typing import List, Dict, Any

from core.utils import try_send, format_large_number
from core.icons import ICON_SHOP, ICON_ERROR, ICON_INFO
from core.config import COMMAND_PREFIX

logger = logging.getLogger(__name__)

ITEMS_PER_PAGE = 5

class ShopView(nextcord.ui.View):
    def __init__(self, *, items_data: List[Dict[str, Any]], original_author: nextcord.User):
        super().__init__(timeout=180)
        self.items_data = items_data
        self.original_author = original_author
        self.current_page = 0
        self.total_pages = math.ceil(len(self.items_data) / ITEMS_PER_PAGE)
        self.message = None
        self.update_buttons()

    def update_buttons(self):
        self.children[0].disabled = self.current_page == 0
        self.children[1].disabled = self.current_page >= self.total_pages - 1

    async def generate_embed_for_current_page(self) -> nextcord.Embed:
        start_index = self.current_page * ITEMS_PER_PAGE
        end_index = start_index + ITEMS_PER_PAGE
        
        embed = nextcord.Embed(
            title=f"{ICON_SHOP} Cửa Hàng Vật Phẩm",
            description=f"Sử dụng `{COMMAND_PREFIX}buy <ID vật phẩm>` để mua.",
            color=nextcord.Color.gold()
        )

        page_items = self.items_data[start_index:end_index]

        if not page_items:
            embed.description = "Không có vật phẩm nào để hiển thị."
        else:
            for item in page_items:
                buy_price = item.get('price', 0)
                sell_price = item.get('sell_price', 0)
                # [SỬA] Lấy emoji từ dữ liệu, nếu không có thì để trống
                emoji = item.get('emoji', '') 
                name = item.get('name', item['id'].replace("_", " ").capitalize())
                desc = item.get('description', 'Chưa có mô tả.')
                
                embed.add_field(
                    # [SỬA] Thêm emoji vào trước tên vật phẩm
                    name=f"{emoji} {name} (ID: `{item['id']}`)", 
                    value=f"```{desc}```\n"
                          f"**Giá mua:** {format_large_number(buy_price)} | **Giá bán:** {format_large_number(sell_price)}",
                    inline=False
                )
        
        embed.set_footer(text=f"Trang {self.current_page + 1}/{self.total_pages} | Yêu cầu bởi {self.original_author.display_name}")
        return embed

    async def interaction_check(self, interaction: nextcord.Interaction) -> bool:
        if interaction.user.id != self.original_author.id:
            await interaction.response.send_message("Đây không phải là menu của bạn!", ephemeral=True)
            return False
        return True

    @nextcord.ui.button(label="⬅️ Trang trước", style=nextcord.ButtonStyle.grey)
    async def previous_page(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            new_embed = await self.generate_embed_for_current_page()
            await interaction.response.edit_message(embed=new_embed, view=self)

    @nextcord.ui.button(label="Trang sau ➡️", style=nextcord.ButtonStyle.grey)
    async def next_page(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_buttons()
            new_embed = await self.generate_embed_for_current_page()
            await interaction.response.edit_message(embed=new_embed, view=self)
        
class ShopCommandCog(commands.Cog, name="Shop Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("ShopCommandCog (Icon Ready) initialized.")

    @commands.command(name='shop', aliases=['store'])
    @commands.guild_only()
    async def shop(self, ctx: commands.Context):
        try:
            all_items = self.bot.item_definitions
            if not all_items:
                await try_send(ctx, content=f"{ICON_ERROR} Cửa hàng hiện đang trống!")
                return

            items_list = [{"id": item_id, **details} for item_id, details in all_items.items() if details.get("price")]
            sorted_items = sorted(items_list, key=lambda x: x['price'])
            
            if not sorted_items:
                await try_send(ctx, content=f"{ICON_INFO} Hiện không có vật phẩm nào được bán.")
                return

            view = ShopView(items_data=sorted_items, original_author=ctx.author)
            
            initial_embed = await view.generate_embed_for_current_page()
            
            sent_message = await try_send(ctx, embed=initial_embed, view=view)
            if sent_message:
                view.message = sent_message

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'shop': {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi mở cửa hàng.")

def setup(bot: commands.Bot):
    bot.add_cog(ShopCommandCog(bot))
