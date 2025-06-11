import nextcord
from nextcord.ext import commands
import logging

from core.utils import try_send, find_best_match, format_large_number
from core.config import TAINTED_ITEM_SELL_RATE, TAINTED_ITEM_TAX_RATE, FOREIGN_ITEM_SELL_PENALTY
from core.icons import ICON_SUCCESS, ICON_ERROR, ICON_WARNING, ICON_INFO, ICON_ECOIN

logger = logging.getLogger(__name__)

class SellCommandCog(commands.Cog, name="Sell Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("SellCommandCog (SQLite & Fuzzy Search Ready) initialized.")

    @commands.command(name='sell')
    @commands.guild_only()
    async def sell(self, ctx: commands.Context, item_id: str, quantity: int = 1):
        """Bán một vật phẩm từ túi đồ của bạn."""
        author_id = ctx.author.id
        guild_id = ctx.guild.id
        item_id_to_sell = item_id.lower().strip()

        if quantity <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Số lượng bán phải lớn hơn 0.")
            return

        try:
            # Lấy toàn bộ túi đồ của người dùng
            full_inventory = self.bot.db.get_inventory(author_id)
            if not full_inventory:
                await try_send(ctx, content=f"{ICON_ERROR} Túi đồ của bạn trống rỗng!")
                return
            
            # Lấy danh sách các ID vật phẩm duy nhất mà người dùng sở hữu
            owned_item_ids = list(set([item['item_id'] for item in full_inventory]))

            # Logic tìm kiếm thông minh
            if item_id_to_sell not in owned_item_ids:
                best_match = find_best_match(item_id_to_sell, owned_item_ids)
                if best_match:
                    await try_send(ctx, content=f"{ICON_WARNING} Không tìm thấy `{item_id_to_sell}` trong túi đồ. Có phải bạn muốn bán: `{best_match}`?")
                else:
                    await try_send(ctx, content=f"{ICON_ERROR} Bạn không có vật phẩm `{item_id_to_sell}` trong túi đồ để bán.")
                return

            # Lọc ra các vật phẩm có ID trùng khớp để bán
            items_of_id = [item for item in full_inventory if item['item_id'] == item_id_to_sell]
            
            if len(items_of_id) < quantity:
                await try_send(ctx, content=f"{ICON_ERROR} Bạn chỉ có **{len(items_of_id)}x {item_id_to_sell}**, không đủ để bán {quantity} cái.")
                return

            total_earnings = 0
            items_sold_count = 0
            
            global_profile = self.bot.db.get_or_create_global_user_profile(author_id)
            local_data = self.bot.db.get_or_create_user_local_data(author_id, guild_id)
            current_earned_balance = local_data['local_balance_earned']
            current_wanted_level = global_profile['wanted_level']

            items_to_sell_list = items_of_id[:quantity]

            for item_to_sell in items_to_sell_list:
                item_details = self.bot.item_definitions.get(item_to_sell['item_id'], {})
                sell_price = item_details.get("sell_price")

                if sell_price is None:
                    # Bỏ qua nếu vật phẩm không thể bán được
                    continue
                
                final_proceeds = 0
                if item_to_sell['is_tainted']:
                    proceeds = sell_price * TAINTED_ITEM_SELL_RATE
                    tax = proceeds * TAINTED_ITEM_TAX_RATE
                    final_proceeds = round(proceeds - tax)
                    current_wanted_level += 0.1 # Tăng nhẹ điểm nghi ngờ
                elif item_to_sell['is_foreign']:
                    final_proceeds = round(sell_price * (1 - FOREIGN_ITEM_SELL_PENALTY))
                else:
                    final_proceeds = sell_price

                total_earnings += final_proceeds
                # Xóa vật phẩm khỏi CSDL bằng ID duy nhất của nó
                self.bot.db.remove_item_from_inventory(item_to_sell['inventory_id'])
                items_sold_count += 1

            if items_sold_count == 0:
                await try_send(ctx, content=f"{ICON_INFO} Vật phẩm `{item_id_to_sell}` không thể bán được.")
                return

            # Cập nhật balance và wanted level một lần sau vòng lặp
            self.bot.db.update_balance(author_id, guild_id, 'local_balance_earned', current_earned_balance + total_earnings)
            if current_wanted_level != global_profile['wanted_level']:
                self.bot.db.update_wanted_level(author_id, current_wanted_level)

            msg = f"{ICON_SUCCESS} Bạn đã bán thành công **{items_sold_count}x {item_id_to_sell}** và nhận được tổng cộng **{total_earnings:,}** {ICON_ECOIN}."
            await try_send(ctx, content=msg)

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'sell' cho user {author_id}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi bạn bán hàng.")

def setup(bot: commands.Bot):
    bot.add_cog(SellCommandCog(bot))
