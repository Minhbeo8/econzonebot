import nextcord
from nextcord.ext import commands, tasks
import random
from datetime import datetime, time, timedelta
import logging  # SỬA: Import thư viện logging tiêu chuẩn

from core.database_sqlite import get_db_connection

# SỬA: Lấy logger cho module hiện tại
logger = logging.getLogger(__name__)

class DynamicShopTaskCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.restock_and_update_prices_sqlite.start()

    def cog_unload(self):
        self.restock_and_update_prices_sqlite.cancel()

    def _update_shop_db(self):
        """
        Hàm đồng bộ (synchronous) chứa tất cả logic tương tác với CSDL.
        Hàm này sẽ được chạy trong một executor để không block event loop.
        """
        conn = get_db_connection()
        try:
            items = conn.execute("SELECT * FROM items WHERE price > 0").fetchall()
            logger.info("Dynamic Shop Task (SQLite): Starting DB operations...")

            for item_data in items:
                item = dict(item_data)
                item_id = item['item_id']
                
                # Logic restock
                restock_chance = item.get('restock_chance', 0.5)
                if random.random() < restock_chance:
                    max_stock = item.get('max_stock', 100)
                    restock_amount = random.randint(1, max(2, int(max_stock * 0.1)))
                    new_stock = min(max_stock, item['current_stock'] + restock_amount)
                    conn.execute("UPDATE items SET current_stock = ? WHERE item_id = ?", (new_stock, item_id))

                # Logic cập nhật giá
                price = item['price']
                volatility = item.get('volatility', 0.1)
                trend = item.get('trend', 0)
                
                price_change_percent = random.uniform(-volatility, volatility) + trend
                new_price = price * (1 + price_change_percent)
                
                base_price = item.get('base_price', price)
                min_price = base_price * 0.5
                max_price = base_price * 2.0
                
                final_price = round(max(min_price, min(new_price, max_price)))
                
                conn.execute("UPDATE items SET price = ? WHERE item_id = ?", (final_price, item_id))
                
                if item_id in self.bot.item_definitions:
                    self.bot.item_definitions[item_id]["price"] = final_price

            conn.commit()
            logger.info("Dynamic Shop Task (SQLite): Finished DB operations successfully.")
        except Exception as e:
            logger.error(f"Error during Dynamic Shop DB operations: {e}", exc_info=True)
            conn.rollback()
        finally:
            conn.close()

    @tasks.loop(minutes=30)
    async def restock_and_update_prices_sqlite(self):
        logger.info("Dynamic Shop Task (SQLite): Task loop is running.")
        try:
            await self.bot.loop.run_in_executor(None, self._update_shop_db)
        except Exception as e:
            logger.error(f"Error in Dynamic Shop Task (SQLite) loop: {e}", exc_info=True)

    @restock_and_update_prices_sqlite.before_loop
    async def before_restock_and_update_prices(self):
        await self.bot.wait_until_ready()
        logger.info("Dynamic Shop Task: Waiting for bot to be ready...")

def setup(bot):
    if bot.db_type == 'sqlite':
        bot.add_cog(DynamicShopTaskCog(bot))
    else:
        logger.warning("Skipping DynamicShopTaskCog because database type is not SQLite.")
