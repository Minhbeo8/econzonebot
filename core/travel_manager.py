import nextcord
from nextcord.ext import commands
import logging
from functools import wraps

# SỬA: Import trực tiếp từ database_sqlite
from .database_sqlite import get_db_connection, get_or_create_user_local_data
from .config import COMMAND_PREFIX
from .icons import ICON_ERROR

logger = logging.getLogger(__name__)

def require_travel_check(func):
    """
    Decorator để kiểm tra xem người dùng có cần phải di chuyển đến server hiện tại không.
    Nếu có, nó sẽ ngăn lệnh thực thi và gửi một tin nhắn hướng dẫn.
    """
    @wraps(func)
    async def wrapper(self, ctx: commands.Context, *args, **kwargs):
        if not ctx.guild:
            # Bỏ qua check nếu lệnh không ở trong server (ví dụ: DM)
            return await func(self, ctx, *args, **kwargs)

        user_id = ctx.author.id
        current_guild_id = ctx.guild.id

        # Lấy vị trí hiện tại của người dùng từ CSDL
        conn = get_db_connection()
        try:
            profile_cursor = conn.execute("SELECT current_guild_id FROM users WHERE user_id = ?", (user_id,))
            user_profile = profile_cursor.fetchone()
        finally:
            conn.close()

        user_location_id = user_profile['current_guild_id'] if user_profile else None
        
        # Nếu vị trí hiện tại của người dùng không phải là server này
        if user_location_id != current_guild_id:
            try:
                target_guild = self.bot.get_guild(user_location_id)
                guild_name = target_guild.name if target_guild else f"một server khác (ID: {user_location_id})"
                
                embed = nextcord.Embed(
                    title=f"{ICON_ERROR} Sai Vị Trí",
                    description=f"Bạn đang ở **{guild_name}**. Bạn cần phải di chuyển đến server **{ctx.guild.name}** để sử dụng lệnh này.",
                    color=nextcord.Color.red()
                )
                embed.add_field(name="Cách di chuyển?", value=f"Sử dụng lệnh `/travel <tên_server>`.")
                await ctx.send(embed=embed)
            except Exception as e:
                logger.error(f"Lỗi khi gửi tin nhắn travel check: {e}")
                await ctx.send(f"{ICON_ERROR} Bạn cần di chuyển đến server này trước khi dùng lệnh.")
            return # Dừng không cho thực thi lệnh gốc

        # Nếu vị trí đã đúng, thực thi lệnh như bình thường
        return await func(self, ctx, *args, **kwargs)
    return wrapper
