# bot/cogs/economy/visa_cmd.py
import nextcord
from nextcord.ext import commands
import logging
import uuid

from core.database import get_or_create_global_user_profile
from core.utils import try_send, format_large_number, require_travel_check
from core.config import COMMAND_PREFIX, UPGRADE_VISA_COST
from core.icons import ICON_SUCCESS, ICON_ERROR, ICON_INFO, ICON_BANK_MAIN, ICON_ECOBANK, ICON_ECOVISA

logger = logging.getLogger(__name__)

class VisaCommandCog(commands.Cog, name="Visa Commands"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("VisaCommandCog (v3 - Refactored) initialized.")

    @commands.group(name='visa', invoke_without_command=True)
    async def visa(self, ctx: commands.Context):
        """Lệnh cha cho các hoạt động liên quan đến thẻ Visa."""
        await try_send(ctx, content=f"{ICON_INFO} Vui lòng sử dụng một lệnh con. Gõ `{COMMAND_PREFIX}help visa` để xem chi tiết.")

    @visa.command(name="buy")
    @commands.guild_only()
    @require_travel_check
    async def buy_visa(self, ctx: commands.Context, visa_id_str: str):
        """Mua một thẻ Visa mới bằng tiền từ Bank trung tâm của bạn."""
        item_id_to_buy = visa_id_str.lower().strip()
        # [SỬA] Sử dụng item definitions từ cache
        all_items = self.bot.item_definitions

        if item_id_to_buy not in all_items or all_items[item_id_to_buy].get("type") != "visa":
            await try_send(ctx, content=f"{ICON_ERROR} Loại Visa `{visa_id_str}` không hợp lệ.")
            return

        try:
            # [SỬA] Sử dụng cache
            economy_data = self.bot.economy_data
            global_profile = get_or_create_global_user_profile(economy_data, ctx.author.id)
            
            visa_details = all_items[item_id_to_buy]
            price = visa_details.get("price", 0)

            if global_profile.get("bank_balance", 0) < price:
                await try_send(ctx, content=f"{ICON_ERROR} Bạn không đủ tiền trong Bank. Cần **{price:,}**, bạn có **{global_profile.get('bank_balance', 0):,}**.")
                return

            global_profile["bank_balance"] -= price
            
            new_visa_item = {
                "item_id": item_id_to_buy,
                "unique_id": str(uuid.uuid4())[:8],
                "type": "visa",
                "visa_type": visa_details["visa_type"],
                "source_guild_id": ctx.guild.id,
                "balance": 0,
                "capacity": visa_details["capacity"]
            }
            
            global_profile.setdefault("inventory_global", []).append(new_visa_item)

            logger.info(f"User {ctx.author.id} đã mua {item_id_to_buy} với giá {price} từ bank.")
            await try_send(ctx, content=f"{ICON_SUCCESS} Bạn đã mua thành công **{visa_details['name']}**! Thẻ đã được thêm vào túi đồ toàn cục. Dùng `{COMMAND_PREFIX}visa topup` để nạp tiền.")

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'visa buy': {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi mua Visa.")

    @visa.command(name="balance", aliases=["bal", "list"])
    @require_travel_check
    async def visa_balance(self, ctx: commands.Context):
        """Xem số dư của tất cả các thẻ Visa bạn đang sở hữu."""
        try:
            # [SỬA] Sử dụng cache
            economy_data = self.bot.economy_data
            global_profile = get_or_create_global_user_profile(economy_data, ctx.author.id)
            inventory_global = global_profile.get("inventory_global", [])
            
            visa_items = [item for item in inventory_global if isinstance(item, dict) and item.get("type") == "visa"]

            if not visa_items:
                await try_send(ctx, content=f"{ICON_INFO} Bạn chưa sở hữu thẻ Visa nào.")
                return

            embed = nextcord.Embed(title=f"💳 Các Thẻ Visa của {ctx.author.name}", color=nextcord.Color.dark_purple())
            embed.set_footer(text=f"Dùng {COMMAND_PREFIX}visa topup <ID_thẻ> <số_tiền> để nạp tiền.")
            
            # [SỬA] Sử dụng item definitions từ cache
            all_items = self.bot.item_definitions
            for visa in visa_items:
                visa_icon = ICON_ECOBANK if visa.get("visa_type") == "local" else ICON_ECOVISA
                visa_name = all_items.get(visa['item_id'], {}).get('name', 'Visa không xác định')
                
                source_server_name = "Toàn cầu"
                if source_guild_id := visa.get("source_guild_id"):
                    source_guild = self.bot.get_guild(source_guild_id)
                    if source_guild:
                        source_server_name = source_guild.name
                
                embed.add_field(
                    name=f"{visa_icon} {visa_name} (ID: `{visa.get('unique_id')}`)",
                    value=(f"**Số dư:** `{format_large_number(visa.get('balance', 0))}` / `{format_large_number(visa.get('capacity', 0))}`\n"
                           f"**Loại:** `{visa.get('visa_type', 'N/A').capitalize()}`\n"
                           f"**Nơi phát hành:** `{source_server_name}`"),
                    inline=False
                )

            await try_send(ctx, embed=embed)

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'visa balance': {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi xem số dư Visa.")

def setup(bot: commands.Bot):
    bot.add_cog(VisaCommandCog(bot))
