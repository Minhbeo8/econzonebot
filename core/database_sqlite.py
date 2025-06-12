# core/database_sqlite.py

import sqlite3
import json
import logging

db_logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path='econzone.sqlite'):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.setup_tables()
        # Thêm hàm kiểm tra và cập nhật cột
        self._add_missing_columns()

    def setup_tables(self):
        """Khởi tạo các bảng trong CSDL nếu chúng chưa tồn tại."""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                guild_id INTEGER,
                balance INTEGER DEFAULT 0,
                bank INTEGER DEFAULT 0,
                inventory TEXT DEFAULT '{}',
                level INTEGER DEFAULT 1,
                xp INTEGER DEFAULT 0,
                health INTEGER DEFAULT 100,
                energy INTEGER DEFAULT 100,
                hunger INTEGER DEFAULT 100,
                last_work REAL DEFAULT 0,
                last_crime REAL DEFAULT 0,
                last_rob REAL DEFAULT 0,
                last_fish REAL DEFAULT 0,
                last_beg REAL DEFAULT 0,
                last_daily REAL DEFAULT 0,
                wanted_level REAL DEFAULT 0,
                global_balance REAL DEFAULT 0,
                has_visa INTEGER DEFAULT 0,
                ecobit_balance REAL DEFAULT 0
            )
        ''')
        self.conn.commit()

    def _add_missing_columns(self):
        """Kiểm tra và thêm các cột còn thiếu vào bảng để cập nhật CSDL một cách an toàn."""
        try:
            self.cursor.execute("PRAGMA table_info(users)")
            columns = [info[1] for info in self.cursor.fetchall()]
            
            if 'last_active_guild_id' not in columns:
                db_logger.info("Không tìm thấy cột 'last_active_guild_id'. Đang thêm vào bảng users...")
                self.cursor.execute("ALTER TABLE users ADD COLUMN last_active_guild_id INTEGER DEFAULT 0")
                db_logger.info("Đã thêm cột 'last_active_guild_id' thành công.")
            
            self.conn.commit()
        except Exception as e:
            db_logger.error(f"Lỗi khi kiểm tra/thêm cột: {e}", exc_info=True)

    def get_or_create_user(self, user_id: int, guild_id: int):
        """Lấy thông tin người dùng hoặc tạo mới nếu chưa có."""
        self.cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = self.cursor.fetchone()
        if user is None:
            self.cursor.execute(
                "INSERT INTO users (user_id, guild_id) VALUES (?, ?)",
                (user_id, guild_id)
            )
            self.conn.commit()
            self.cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = self.cursor.fetchone()
        return user

    def get_last_active_guild(self, user_id: int) -> int:
        """Lấy ID của server hoạt động cuối cùng của người dùng."""
        self.cursor.execute("SELECT last_active_guild_id FROM users WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else 0

    def update_last_active_guild(self, user_id: int, guild_id: int):
        """Cập nhật server hoạt động cuối cùng cho người dùng."""
        self.cursor.execute(
            "UPDATE users SET last_active_guild_id = ? WHERE user_id = ?",
            (guild_id, user_id)
        )
        self.conn.commit()

    def get_user_inventory(self, user_id: int) -> dict:
        """Lấy hành trang của người dùng dưới dạng một dictionary."""
        self.cursor.execute("SELECT inventory FROM users WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        if result and result[0]:
            return json.loads(result[0])
        return {}

    def get_user_visa_status(self, user_id: int) -> bool:
        """Kiểm tra người dùng có visa hay không."""
        self.cursor.execute("SELECT has_visa FROM users WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        return bool(result[0]) if result else False

    def update_user_balance(self, user_id: int, amount: int):
        """Cập nhật số dư tài khoản của người dùng."""
        self.cursor.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id = ?",
            (amount, user_id)
        )
        self.conn.commit()

    # Thêm các hàm khác để tương tác với CSDL ở đây nếu cần...
