import nextcord
from nextcord.ext import commands
import logging

from core.config import BOT_OWNER_IDS
# [SỬA] Import từ file manager mới
from core.moderation_manager import add_moderator_id, remove_moderator_id, load_moderator_ids
from core.utils import try_send
from core.icons import ICON_SUCCESS, ICON_ERROR, ICON_INFO, ICON_WARNING

logger = logging.getLogger(__name__)

def is_bot_owner():
    """Check decorator để xác định người dùng có phải là chủ bot hay không."""
    def predicate(ctx: commands.Context) -> bool:
        return ctx.author.id in BOT_OWNER_IDS
    return commands.check(predicate)

class ManageModeratorsCog(commands.Cog, name="Manage Moderators"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("ManageModeratorsCog (SQLite Ready) initialized.")

    @commands.group(name="mod", invoke_without_command=True)
    async def mod_group(self, ctx: commands.Context):
        await try_send(ctx, content=f"{ICON_INFO} Vui lòng sử dụng lệnh con: `add` hoặc `remove`.")

    @mod_group.command(name="add")
    @is_bot_owner()
    async def add_mod(self, ctx: commands.Context, user: nextcord.User):
        if add_moderator_id(user.id):
            logger.info(f"BOT OWNER ACTION: {ctx.author.id} đã thêm {user.id} làm moderator.")
            await try_send(ctx, content=f"{ICON_SUCCESS} Đã thêm {user.mention} vào danh sách moderator của bot.")
        else:
            await try_send(ctx, content=f"{ICON_WARNING} {user.mention} đã là moderator rồi.")

    @mod_group.command(name="remove")
    @is_bot_owner()
    async def remove_mod(self, ctx: commands.Context, user: nextcord.User):
        if remove_moderator_id(user.id):
            logger.info(f"BOT OWNER ACTION: {ctx.author.id} đã xóa {user.id} khỏi danh sách moderator.")
            await try_send(ctx, content=f"{ICON_SUCCESS} Đã xóa {user.mention} khỏi danh sách moderator.")
        else:
            await try_send(ctx, content=f"{ICON_WARNING} {user.mention} không có trong danh sách moderator.")

    @mod_group.command(name="list")
    @is_bot_owner()
    async def list_mods(self, ctx: commands.Context):
        mod_ids = load_moderator_ids()
        if not mod_ids:
            await try_send(ctx, content=f"{ICON_INFO} Hiện không có moderator nào.")
            return
        
        mod_mentions = [f"<@{_id}> (`{_id}`)" for _id in mod_ids]
        embed = nextcord.Embed(title="Danh sách Moderator của Bot", description="\n".join(mod_mentions), color=nextcord.Color.blue())
        await try_send(ctx, embed=embed)

    @add_mod.error
    @remove_mod.error
    @list_mods.error
    async def mod_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CheckFailure):
            await try_send(ctx, content=f"{ICON_ERROR} Chỉ chủ sở hữu bot mới có thể dùng lệnh này.")
        else:
            logger.error(f"Lỗi trong lệnh quản lý mod: {error}", exc_info=True)

def setup(bot: commands.Bot):
    bot.add_cog(ManageModeratorsCog(bot))
