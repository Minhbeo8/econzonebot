# core/travel_manager.py

import logging

logger = logging.getLogger(__name__)

class TravelManager:
    def __init__(self, bot):
        """
        Khởi tạo TravelManager với bot instance để truy cập CSDL và các thành phần khác.
        """
        self.bot = bot

    async def check_travel_legality(self, user_id: int, current_guild_id: int) -> tuple[bool, str | None]:
        """
        Kiểm tra xem một hành động của người dùng có phải là "vượt biên trái phép" hay không.
        Sử dụng các hàm từ bot.db đã được định nghĩa ở bước trước.

        Trả về:
            tuple[bool, str | None]: Một tuple chứa (is_illegal, reason)
            - (False, None): Hành động hợp lệ.
            - (True, "lý do"): Vi phạm, cùng với lý do tại sao.
        """
        # Lấy thông tin từ CSDL một cách an toàn qua luồng của bot
        try:
            # Đảm bảo get_or_create_user được gọi để người dùng chắc chắn tồn tại
            await self.bot.loop.run_in_executor(None, self.bot.db.get_or_create_user, user_id, current_guild_id)
            
            last_guild_id = await self.bot.loop.run_in_executor(
                None, self.bot.db.get_last_active_guild, user_id
            )
        except Exception as e:
            logger.error(f"Lỗi khi truy vấn CSDL trong TravelManager cho user {user_id}: {e}", exc_info=True)
            # Mặc định là hợp lệ nếu có lỗi CSDL để tránh khóa người dùng oan
            return (False, None)

        # Trường hợp 1: Người chơi mới (chưa có last_guild_id) hoặc vẫn ở server cũ.
        # Coi last_guild_id = 0 là người chơi mới đối với hệ thống này.
        if not last_guild_id or last_guild_id == current_guild_id:
            return (False, None)

        # Trường hợp 2: Người chơi đã di chuyển sang một server mới (vượt biên)
        # Bây giờ, kiểm tra xem họ có đủ giấy tờ (vật phẩm) không.
        inventory = await self.bot.loop.run_in_executor(
            None, self.bot.db.get_user_inventory, user_id
        )

        # Điều kiện để bị bắt: Vượt biên nhưng thiếu "vé máy bay"
        # Giả sử trong items.json, key của vé máy bay là 'plane_ticket'
        if 'plane_ticket' not in inventory or inventory.get('plane_ticket', 0) < 1:
            return (True, "vượt biên trái phép không có vé máy bay")
        
        # Nếu có vé máy bay, logic trừ vé sẽ được xử lý sau khi kiểm tra thành công
        # (trong decorator hoặc lệnh) để đảm bảo vé chỉ bị trừ khi lệnh thực sự chạy.

        # Nếu tất cả kiểm tra đều qua, việc di chuyển là hợp lệ.
        return (False, None)
