# main.py
from core.logger import setup_logging 
import core.database_sqlite as db_sqlite
from core.bot import bot, load_all_cogs 

setup_logging(bot_event_loop=bot.loop) 
main_logger = logging.getLogger(__name__) 

if __name__ == "__main__":
    import threading
from dashboard import run_flask_app
def run_dashboard():
    app.run(host="0.0.0.0", port=8080)
    main_logger.info("==================================================")
    main_logger.info("Bắt đầu khởi chạy Bot Kinh Tế! (main.py)")
    main_logger.info("==================================================")

    # [SỬA ĐỔI] Gán thẳng CSDL SQLite và khởi tạo
    main_logger.info("Bot đang chạy với CSDL SQLite.")
    bot.db = db_sqlite
    bot.db_type = 'sqlite' # Giữ lại biến này để on_message hoạt động đúng
    try:
        bot.db.initialize_database()
    except Exception as e:
        main_logger.critical(f"Không thể khởi tạo CSDL SQLite: {e}", exc_info=True)
        sys.exit(1)

try:
        main_logger.info("Đang tải định nghĩa vật phẩm vào cache...")
        bot.item_definitions = bot.db.load_item_definitions()
        main_logger.info("Tải định nghĩa vật phẩm thành công.")
    except Exception as e:
        main_logger.critical(f"Không thể tải dữ liệu ban đầu: {e}", exc_info=True)
        sys.exit(1)

    # Phần còn lại của file giữ nguyên
    actual_bot_token = os.getenv("BOT_TOKEN")
    if not actual_bot_token:
        main_logger.critical("CRITICAL: BOT_TOKEN không được tìm thấy!")
        sys.exit(1) 
    else:
        main_logger.info("BOT_TOKEN đã được tải thành công.")

    main_logger.info("Đang kiểm tra và tải các Cogs...")
    try:
        load_all_cogs() 
    except Exception as e:
        main_logger.critical(f"Không thể tải Cogs: {e}", exc_info=True)
    
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
        # Chỉ lưu khi dùng JSON
        if DB_TYPE == 'json':
            main_logger.info("Đang lưu dữ liệu kinh tế (JSON) lần cuối từ cache...")
            try:
                if hasattr(bot, 'economy_data'):
                    bot.db.save_economy_data(bot.economy_data)
                    main_logger.info("Lưu dữ liệu lần cuối thành công.")
            except Exception as e:
                main_logger.error(f"Lỗi khi lưu dữ liệu lần cuối: {e}", exc_info=True)
            
        main_logger.info("==================================================")
        main_logger.info("Bot đã dừng hoạt động.")
        main_logger.info("==================================================")
