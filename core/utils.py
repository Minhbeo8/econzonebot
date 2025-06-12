import nextcord
from nextcord.ext import commands
import logging
from typing import Optional, Union
import json
from datetime import datetime, timedelta
from rapidfuzz import fuzz, process
import os
import functools

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

def load_activities_data():
    """Tải dữ liệu hoạt động từ file activities.json."""
    try:
        activities_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'activities.json')
        with open(activities_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("LỖI: không tìm thấy file activities.json.")
        return None
    except json.JSONDecodeError:
        print("LỖI: file activities.json có định dạng không hợp lệ.")
        return None

def format_relative_timestamp(future_timestamp: float) -> str:
    """
    Chuyển đổi một timestamp trong tương lai thành định dạng timestamp tương đối của Discord.
    """
    return f"<t:{int(future_timestamp)}:R>"

def find_best_match(query: str, choices: list, score_cutoff: int = 75) -> Optional[str]:
    """
    Tìm chuỗi gần đúng nhất trong một danh sách.
    """
    best_match = process.extractOne(query, choices, score_cutoff=score_cutoff)
    if best_match:
        return best_match[0]
    return None

# === DECORATOR CHO HỆ THỐNG DU LỊCH ===
def require_travel_check(func):
    """
    Decorator để kiểm tra xem người dùng có 'vượt biên trái phép' không.
    Nó sẽ gọi TravelManager để thực hiện logic kiểm tra.
    """
    @functools.wraps(func)
    async def wrapper(self, ctx: Union[commands.Context, nextcord.Interaction], *args, **kwargs):
        # Đảm bảo bot có travel_manager, nếu không thì báo lỗi và cho qua
        if not hasattr(self.bot, 'travel_manager'):
            logger.error("LỖI: bot.travel_manager chưa được khởi tạo! Bỏ qua kiểm tra du lịch.")
            await func(self, ctx, *args, **kwargs)
            return

        # Lấy user và guild id từ context (hỗ trợ cả slash và prefix commands)
        user_id = ctx.user.id
        guild_id = ctx.guild.id

        # Gọi 'bộ não' để kiểm tra
        is_illegal, reason = await self.bot.travel_manager.check_travel_legality(user_id, guild_id)

        if is_illegal:
            # Nếu vi phạm, gửi tin nhắn cảnh báo và dừng lệnh
            embed = nextcord.Embed(
                title="🚨 BỊ CHẶN BỞI CẢNH SÁT BIÊN PHÒNG 🚨",
                description=f"Bạn không thể thực hiện hành động này.\n**Lý do:** {reason}.",
                color=nextcord.Color.red()
            )
            await try_send(ctx, embed=embed, ephemeral=True)
            return

        # Nếu hợp lệ, cho phép lệnh gốc được thực thi
        await func(self, ctx, *args, **kwargs)

        # Sau khi lệnh thực thi thành công, cập nhật 'dấu chân' của người chơi
        await self.bot.loop.run_in_executor(
            None, self.bot.db.update_last_active_guild, user_id, guild_id
        )

    return wrapper
