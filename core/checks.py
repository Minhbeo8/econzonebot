import nextcord
from nextcord.ext import commands
import logging

# Sửa dòng này để import từ file CSDL mới
from .moderation_manager import load_moderator_ids

logger = logging.getLogger(__name__)

# Tải danh sách ID của moderator một lần khi module được load
MODERATOR_IDS = load_moderator_ids()
if MODERATOR_IDS:
    logger.info(f"Đã tải {len(MODERATOR_IDS)} moderator ID.")
else:
    logger.warning("Không có moderator ID nào được tải. File moderators.json có thể bị trống hoặc lỗi.")

def is_bot_moderator(user: nextcord.User) -> bool:
    """Kiểm tra xem một user có phải là moderator của bot hay không."""
    return user.id in MODERATOR_IDS

def check_is_bot_moderator(ctx: commands.Context) -> bool:
    """Check decorator cho các lệnh prefix."""
    return is_bot_moderator(ctx.author)

def check_is_bot_moderator_interaction(interaction: nextcord.Interaction) -> bool:
    """Check decorator cho các lệnh slash."""
    return is_bot_moderator(interaction.user)

def is_guild_owner(ctx: commands.Context) -> bool:
    """Kiểm tra xem người dùng có phải là chủ server hay không."""
    return ctx.author.id == ctx.guild.owner_id

def is_guild_owner_check(ctx: commands.Context) -> bool:
    """Check decorator cho lệnh prefix của chủ server."""
    if not ctx.guild:
        return False
    return is_guild_owner(ctx)
