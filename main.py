import sys
import nextcord 
import os
from dotenv import load_dotenv 

# Tải biến môi trường từ .env hoặc Secrets
load_dotenv() 

import logging
import threading

# Import các thành phần cần thiết
from dashboard import run_flask_app
from core.bot import bot, load_all_cogs 
from core.logger import setup_logging 
import core.database_sqlite as db_sqlite
from core.travel_manager import TravelManager

setup_logging(bot_event_loop=bot.loop) 
main_logger = logging.getLogger(__name__) 

if __name__ == "__main__":
    # Khởi động dashboard trên một luồng riêng
    # và truyền đối tượng 'bot' vào để dashboard có thể sử dụng
    threading.Thread(target=run_flask_app, args=(bot,), daemon=True).start()
    
    main_logger.info("==================================================")
    main_logger.info("Bắt đầu khởi chạy Bot Kinh Tế! (main.py)")
    main_logger.info("==================================================")

    # Gán thẳng CSDL SQLite và khởi tạo
    main_logger.info("Bot đang chạy với CSDL SQLite.")
    bot.db = db_sqlite
    bot.db_type = 'sqlite' # Gán thuộc tính để các hàm khác có thể nhận biết
    try:
        bot.db.initialize_database()
    except Exception as e:
        main_logger.critical(f"Không thể khởi tạo CSDL SQLite: {e}", exc_info=True)
        sys.exit(1)

    # Tải dữ liệu định nghĩa vật phẩm vào cache
    try:
        main_logger.info("Đang tải định nghĩa vật phẩm vào cache...")
        bot.item_definitions = bot.db.load_item_definitions()
        main_logger.info("Tải định nghĩa vật phẩm thành công.")
    except Exception as e:
        main_logger.critical(f"Không thể tải dữ liệu ban đầu: {e}", exc_info=True)
        sys.exit(1)

    # Khởi tạo Travel Manager và gắn vào bot
    main_logger.info("Đang khởi tạo Travel Manager...")
    bot.travel_manager = TravelManager(bot) 
    main_logger.info("Travel Manager đã sẵn sàng.")

    # Tải Bot Token từ biến môi trường
    actual_bot_token = os.getenv("BOT_TOKEN")
    if not actual_bot_token:
        main_logger.critical("CRITICAL: BOT_TOKEN không được tìm thấy!")
        sys.exit(1) 
    else:
        main_logger.info("BOT_TOKEN đã được tải thành công.")

    # Tải tất cả các Cogs
    main_logger.info("Đang kiểm tra và tải các Cogs...")
    try:
        load_all_cogs() 
    except Exception as e:
        main_logger.critical(f"Không thể tải Cogs: {e}", exc_info=True)
    
    # Sự kiện tự động sao lưu lần cuối khi bot tắt
    @bot.event
    async def on_close():
        """Sự kiện này chạy khi bot đang trong quá trình tắt."""
        main_logger.info("Bot is shutting down. Performing one final database sync...")
        sync_cog = bot.get_cog("Database Sync Task")
        if sync_cog and hasattr(sync_cog, 'force_sync'):
            try:
                await sync_cog.force_sync()
                main_logger.info("Final database sync successful.")
            except Exception as e:
                main_logger.error(f"Final database sync failed: {e}")
        else:
            main_logger.warning("Could not find sync cog to perform final sync.")

    # Chạy bot và kết nối tới Discord
    main_logger.info("Đang cố gắng kết nối với Discord...")
    try:
        bot.run(actual_bot_token)
    except nextcord.errors.LoginFailure:
        main_logger.critical("LỖI ĐĂNG NHẬP: Token không hợp lệ.", exc_info=False) 
    except KeyboardInterrupt: 
        main_logger.info("Bot đã được dừng bởi người dùng (KeyboardInterrupt).")
    except Exception as e:
        main_logger.critical(f"LỖI KHÔNG XÁC ĐỊNH KHI CHẠY BOT: {type(e).__name__} - {e}", exc_info=True)
    finally:
        main_logger.info("==================================================")
        main_logger.info("Bot đã dừng hoạt động.")
        main_logger.info("==================================================")
