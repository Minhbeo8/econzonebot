import nextcord
from nextcord.ext import commands
import logging
from typing import Optional, Union
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

async def try_send(
    ctx: Union[commands.Context, nextcord.Interaction],
    content: Optional[str] = None,
    embed: Optional[nextcord.Embed] = None,
    view: Optional[nextcord.ui.View] = None,
    ephemeral: bool = False
) -> Optional[nextcord.Message]:
    """
    Cố gắng gửi tin nhắn. Trả về đối tượng tin nhắn nếu thành công, None nếu thất bại.
    Hỗ trợ cả lệnh prefix và lệnh slash.
    """
    send_method = None
    if isinstance(ctx, commands.Context):
        send_method = ctx.send
    elif isinstance(ctx, nextcord.Interaction):
        # Kiểm tra xem interaction đã được trả lời chưa
        if ctx.response.is_done():
            send_method = ctx.followup.send
        else:
            send_method = ctx.response.send_message

    if not send_method:
        logger.error(f"Không thể xác định phương thức gửi cho context loại: {type(ctx)}")
        return None

    try:
        # Lệnh slash có tham số ephemeral
        if isinstance(ctx, nextcord.Interaction) and ephemeral:
            return await send_method(content=content, embed=embed, view=view, ephemeral=True)
        else:
            return await send_method(content=content, embed=embed, view=view)
    except nextcord.errors.NotFound:
        logger.warning(f"Không thể gửi tin nhắn: Interaction hoặc Context không còn tồn tại.")
    except Exception as e:
        logger.error(f"Lỗi không xác định khi gửi tin nhắn: {e}", exc_info=True)
    return None

def format_large_number(number: int) -> str:
    """Định dạng số lớn với dấu phẩy."""
    return "{:,}".format(number)

def get_player_title(local_level: int, wanted_level: float) -> str:
    """
    Tạo danh hiệu cho người chơi dựa trên các chỉ số được truyền vào.
    """
    if wanted_level > 20: return "🔥 Bị Truy Nã Gắt Gao"
    if wanted_level > 10: return "🩸 Tội Phạm Khét Tiếng"
    if wanted_level > 5: return "💀 Kẻ Ngoài Vòng Pháp Luật"
    if local_level > 50: return "💎 Huyền Thoại Sống"
    if local_level > 30: return "🏆 Lão Làng"
    if local_level > 15: return "🥇 Dân Chơi"
    return "🌱 Tấm Chiếu Mới"

def format_relative_timestamp(future_timestamp: float) -> str:
    """
    Chuyển đổi một timestamp trong tương lai thành định dạng timestamp tương đối của Discord.
    Ví dụ: <t:1678886400:R> sẽ hiển thị là "in 2 hours".
    """
    return f"<t:{int(future_timestamp)}:R>"

def require_travel_check(func):
    """
    Decorator để kiểm tra xem người dùng có đang trong trạng thái 'di chuyển' hay không.
    """
    async def wrapper(self, ctx: commands.Context, *args, **kwargs):
        # Logic này cần được hoàn thiện nếu có hệ thống di chuyển
        # Ví dụ: kiểm tra một trạng thái trong CSDL
        # if self.bot.db.is_user_traveling(ctx.author.id):
        #     await try_send(ctx, content="Bạn đang di chuyển, không thể thực hiện hành động này.")
        #     return
        await func(self, ctx, *args, **kwargs)
    return wrapper
