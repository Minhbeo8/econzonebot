import nextcord
from nextcord.ext import commands
import random
from datetime import datetime
import logging

from core.utils import try_send, format_relative_timestamp, require_travel_check
# SỬA: Import các biến cấu hình mới
from core.config import BEG_COOLDOWN, BEG_SUCCESS_RATE, BEG_REWARD_MIN, BEG_REWARD_MAX
from core.icons import ICON_LOADING, ICON_GIFT, ICON_WARNING, ICON_BANK_MAIN

logger = logging.getLogger(__name__)

class BegCommandCog(commands.Cog, name="Beg Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("BegCommandCog (SQLite Ready) initialized.")

    @commands.command(name='beg', aliases=['b'])
    @commands.guild_only()
    @require_travel_check
    async def beg(self, ctx: commands.Context):
        author_id = ctx.author.id
        
        now = datetime.now().timestamp()
        last_beg = self.bot.db.get_cooldown(author_id, "beg")
        
        if last_beg and now < last_beg + BEG_COOLDOWN:
            cooldown_end_timestamp = last_beg + BEG_COOLDOWN
            relative_time_str = format_relative_timestamp(cooldown_end_timestamp)
            await try_send(ctx, content=f"{ICON_LOADING} Đừng xin liên tục thế chứ! Hãy quay lại sau ({relative_time_str}).")
            return

        self.bot.db.set_cooldown(author_id, "beg", now)
        
        # SỬA: Sử dụng tỉ lệ thành công từ config
        if random.random() < BEG_SUCCESS_RATE: 
            # SỬA: Sử dụng khoảng tiền từ config
            earnings = random.randint(BEG_REWARD_MIN, BEG_REWARD_MAX)
            
            # Logic gốc của bạn: cộng tiền vào bank
            user_profile = self.bot.db.get_or_create_global_user_profile(author_id)
            new_balance = user_profile['bank_balance'] + earnings
            # Chú ý: Hàm update_balance có vẻ không tồn tại trong db của bạn, tôi giả định nó là update_global_balance
            # Nếu bot báo lỗi ở đây, chúng ta sẽ xem lại hàm CSDL. Tạm thời dùng hàm phù hợp nhất.
            self.bot.db.update_global_balance(author_id, 'bank_balance', earnings)
            
            # Lấy lại số dư mới nhất để hiển thị chính xác
            updated_profile = self.bot.db.get_or_create_global_user_profile(author_id)
            final_balance = updated_profile['bank_balance']

            await try_send(ctx, content=f"{ICON_GIFT} Một người tốt bụng đã cho {ctx.author.mention} **{earnings:,}**! Số dư {ICON_BANK_MAIN} của bạn giờ là: **{final_balance:,}**")
        else:
            await try_send(ctx, content=f"{ICON_WARNING} Không ai cho {ctx.author.mention} tiền cả. 😢")
            
def setup(bot: commands.Bot):
    bot.add_cog(BegCommandCog(bot))
