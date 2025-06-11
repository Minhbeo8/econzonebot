# bot/core/database_sqlite.py
import sqlite3
import logging
import os
import json
from typing import Dict, Any, List

logger = logging.getLogger(__name__)
DB_PATH = "data/econzone.sqlite"

# --- KẾT NỐI VÀ KHỞI TẠO ---
def get_db_connection():
    """Tạo và trả về một kết nối tới CSDL."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_database():
    """Tạo tất cả các bảng cần thiết nếu chúng chưa tồn tại."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            bank_balance INTEGER DEFAULT 0,
            wanted_level REAL DEFAULT 0.0,
            level_global INTEGER DEFAULT 1,
            xp_global INTEGER DEFAULT 0,
            last_active_guild_id INTEGER
        );
        CREATE TABLE IF NOT EXISTS user_guild_data (
            user_id INTEGER NOT NULL,
            guild_id INTEGER NOT NULL,
            local_balance_earned INTEGER DEFAULT 0,
            local_balance_adadd INTEGER DEFAULT 0,
            level_local INTEGER DEFAULT 1,
            xp_local INTEGER DEFAULT 0,
            health INTEGER DEFAULT 100,
            hunger INTEGER DEFAULT 100,
            energy INTEGER DEFAULT 100,
            PRIMARY KEY (user_id, guild_id),
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        );
        CREATE TABLE IF NOT EXISTS items (
            item_id TEXT PRIMARY KEY,
            name TEXT,
            description TEXT,
            price INTEGER,
            sell_price INTEGER,
            type TEXT,
            effect_stat TEXT,
            effect_value INTEGER,
            capacity INTEGER,
            current_stock INTEGER DEFAULT 20,
            max_stock INTEGER DEFAULT 50
        );
        CREATE TABLE IF NOT EXISTS inventories (
            inventory_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_id TEXT NOT NULL,
            location TEXT NOT NULL,
            guild_id INTEGER,
            is_tainted BOOLEAN DEFAULT 0,
            is_foreign BOOLEAN DEFAULT 0,
            quantity INTEGER DEFAULT 1,
            custom_data TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (item_id) REFERENCES items (item_id)
        );
        CREATE TABLE IF NOT EXISTS cooldowns (key TEXT PRIMARY KEY, value REAL);
        CREATE TABLE IF NOT EXISTS guild_configs (
            guild_id INTEGER PRIMARY KEY,
            bare_command_active_channels TEXT DEFAULT '[]',
            muted_channels TEXT DEFAULT '[]'
        );
    """)
    conn.commit()
    conn.close()
    logger.info("CSDL SQLite đã được kiểm tra và khởi tạo (nếu cần).")

# --- HÀM TẢI DỮ LIỆU ---

def load_item_definitions(file_path: str = 'items.json') -> Dict[str, Any]:
    """
    [SỬA] Tải định nghĩa vật phẩm từ file JSON.
    Hàm này giờ sẽ đọc tất cả các key ở cấp cao nhất làm vật phẩm.
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"File định nghĩa vật phẩm '{file_path}' không tồn tại.")
            return {}
        with open(file_path, 'r', encoding='utf-8') as f:
            item_data = json.load(f)
       
        return item_data

    except json.JSONDecodeError:
        logger.error(f"Lỗi cú pháp trong file {file_path}. Vui lòng kiểm tra lại.")
        return {}
    except Exception as e:
        logger.error(f"Lỗi không xác định khi tải file định nghĩa vật phẩm '{file_path}': {e}", exc_info=True)
        return {}

def load_moderator_ids(file_path: str = 'moderators.json') -> List[int]:
    # (Hàm này giữ nguyên)
    try:
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({"moderator_ids": []}, f, indent=4)
            return []
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f).get("moderator_ids", [])
    except:
        return []

# --- QUẢN LÝ USER & GUILD ---
def get_or_create_global_user_profile(user_id: int):
    # (Hàm này giữ nguyên)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user_profile = cursor.fetchone()
    conn.commit()
    conn.close()
    return user_profile

def get_or_create_user_local_data(user_id: int, guild_id: int):
    # (Hàm này giữ nguyên)
    get_or_create_global_user_profile(user_id)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO user_guild_data (user_id, guild_id) VALUES (?, ?)", (user_id, guild_id))
    cursor.execute("SELECT * FROM user_guild_data WHERE user_id = ? AND guild_id = ?", (user_id, guild_id))
    local_data = cursor.fetchone()
    conn.commit()
    conn.close()
    return local_data

def get_or_create_guild_config(guild_id: int):
    # (Hàm này giữ nguyên)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO guild_configs (guild_id) VALUES (?)", (guild_id,))
    cursor.execute("SELECT * FROM guild_configs WHERE guild_id = ?", (guild_id,))
    config = cursor.fetchone()
    conn.commit()
    conn.close()
    return config

# --- CẬP NHẬT DỮ LIỆU ---
def update_guild_config_list(guild_id: int, list_name: str, new_list: list):
    conn = get_db_connection()
    conn.execute(f"UPDATE guild_configs SET {list_name} = ? WHERE guild_id = ?", (json.dumps(new_list), guild_id))
    conn.commit()
    conn.close()

def update_balance(user_id: int, guild_id: int, balance_type: str, new_value: int):
    # (Hàm này giữ nguyên)
    conn = get_db_connection()
    if balance_type == 'bank_balance':
        conn.execute("UPDATE users SET bank_balance = ? WHERE user_id = ?", (new_value, user_id))
    elif balance_type in ['local_balance_earned', 'local_balance_adadd']:
        conn.execute(f"UPDATE user_guild_data SET {balance_type} = ? WHERE user_id = ? AND guild_id = ?", (new_value, user_id, guild_id))
    conn.commit()
    conn.close()

def update_user_stats(user_id: int, guild_id: int, health: int = None, hunger: int = None, energy: int = None):
    # (Hàm này giữ nguyên)
    conn = get_db_connection()
    if health is not None: conn.execute("UPDATE user_guild_data SET health = ? WHERE user_id = ? AND guild_id = ?", (max(0, min(100, health)), user_id, guild_id))
    if hunger is not None: conn.execute("UPDATE user_guild_data SET hunger = ? WHERE user_id = ? AND guild_id = ?", (max(0, min(100, hunger)), user_id, guild_id))
    if energy is not None: conn.execute("UPDATE user_guild_data SET energy = ? WHERE user_id = ? AND guild_id = ?", (max(0, min(100, energy)), user_id, guild_id))
    conn.commit()
    conn.close()

def update_xp(user_id: int, guild_id: int, xp_local_gain: int, xp_global_gain: int):
    # (Hàm này giữ nguyên)
    conn = get_db_connection()
    conn.execute("UPDATE users SET xp_global = xp_global + ? WHERE user_id = ?", (xp_global_gain, user_id))
    conn.execute("UPDATE user_guild_data SET xp_local = xp_local + ? WHERE user_id = ? AND guild_id = ?", (xp_local_gain, user_id, guild_id))
    conn.commit()
    conn.close()
    
def update_level(user_id: int, level_type: str, new_level: int, new_xp: int, guild_id: int = None):
    # (Hàm này giữ nguyên)
    conn = get_db_connection()
    if level_type == 'global':
        conn.execute("UPDATE users SET level_global = ?, xp_global = ? WHERE user_id = ?", (new_level, new_xp, user_id))
    elif level_type == 'local' and guild_id:
        conn.execute("UPDATE user_guild_data SET level_local = ?, xp_local = ? WHERE user_id = ? AND guild_id = ?", (new_level, new_xp, user_id, guild_id))
    conn.commit()
    conn.close()

def update_wanted_level(user_id: int, new_wanted_level: float):
    # (Hàm này giữ nguyên)
    conn = get_db_connection()
    conn.execute("UPDATE users SET wanted_level = ? WHERE user_id = ?", (new_wanted_level, user_id))
    conn.commit()
    conn.close()
def perform_survival_decay(decay_amount: int, regen_amount: int):
    """
    Thực hiện việc giảm chỉ số sinh tồn và hồi máu cho tất cả user.
    Hàm này chạy một vài lệnh UPDATE hiệu quả trên toàn bộ CSDL.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # 1. Hồi máu cho những người dùng có đủ năng lượng và độ no
        cursor.execute("""
            UPDATE user_guild_data
            SET health = MIN(100, health + ?)
            WHERE hunger > 70 AND energy > 50
        """, (regen_amount,))
        
        # 2. Giảm độ no và năng lượng cho tất cả người dùng
        cursor.execute("""
            UPDATE user_guild_data
            SET 
                hunger = MAX(0, hunger - ?),
                energy = MAX(0, energy - ?)
        """, (decay_amount, decay_amount))
        
        conn.commit()
    finally:
        conn.close()
# --- QUẢN LÝ COOLDOWN ---
def get_cooldown(user_id: int, command: str) -> float:
    # (Hàm này giữ nguyên)
    conn = get_db_connection()
    key = f"{user_id}_{command}"
    result = conn.execute("SELECT value FROM cooldowns WHERE key = ?", (key,)).fetchone()
    conn.close()
    return result['value'] if result else 0

def set_cooldown(user_id: int, command: str, timestamp: float):
    # (Hàm này giữ nguyên)
    conn = get_db_connection()
    key = f"{user_id}_{command}"
    conn.execute("INSERT OR REPLACE INTO cooldowns (key, value) VALUES (?, ?)", (key, timestamp))
    conn.commit()
    conn.close()

# --- QUẢN LÝ INVENTORY ---
def get_inventory(user_id: int, guild_id: int = None, location: str = None):
    # (Hàm này giữ nguyên)
    conn = get_db_connection()
    if location:
        if location == 'local':
            return conn.execute("SELECT * FROM inventories WHERE user_id = ? AND location = 'local' AND guild_id = ?", (user_id, guild_id)).fetchall()
        else:
            return conn.execute("SELECT * FROM inventories WHERE user_id = ? AND location = 'global'", (user_id,)).fetchall()
    else:
        return conn.execute("SELECT * FROM inventories WHERE user_id = ?", (user_id,)).fetchall()

def find_item_in_inventory(user_id: int, item_id: str, guild_id: int):
    # (Hàm này giữ nguyên)
    conn = get_db_connection()
    item = conn.execute("SELECT * FROM inventories WHERE user_id = ? AND item_id = ? AND location = 'local' AND guild_id = ? LIMIT 1", (user_id, item_id, guild_id)).fetchone()
    if item:
        conn.close()
        return item
    item = conn.execute("SELECT * FROM inventories WHERE user_id = ? AND item_id = ? AND location = 'global' LIMIT 1", (user_id, item_id)).fetchone()
    conn.close()
    return item

def add_item_to_inventory(user_id: int, item_id: str, quantity: int, location: str, guild_id: int = None, is_tainted: bool = False, custom_data: dict = None):
    # (Hàm này giữ nguyên)
    conn = get_db_connection()
    custom_data_str = json.dumps(custom_data) if custom_data else None
    for _ in range(quantity):
        conn.execute("INSERT INTO inventories (user_id, item_id, location, guild_id, is_tainted, custom_data) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, item_id, location, guild_id, is_tainted, custom_data_str))
    conn.commit()
    conn.close()

def remove_item_from_inventory(inventory_id: int):
    # (Hàm này giữ nguyên)
    conn = get_db_connection()
    conn.execute("DELETE FROM inventories WHERE inventory_id = ?", (inventory_id,))
    conn.commit()
    conn.close()

# --- HÀM TRUY VẤN LEADERBOARD ---
def get_global_leaderboard():
    # (Hàm này giữ nguyên)
    conn = get_db_connection()
    users = conn.execute("SELECT user_id, bank_balance FROM users WHERE bank_balance > 0 ORDER BY bank_balance DESC").fetchall()
    conn.close()
    return users

def get_server_leaderboard(guild_id: int):
    # (Hàm này giữ nguyên)
    conn = get_db_connection()
    users = conn.execute("SELECT user_id, (local_balance_earned + local_balance_adadd) as total_local_wealth FROM user_guild_data WHERE guild_id = ? AND total_local_wealth > 0 ORDER BY total_local_wealth DESC", (guild_id,)).fetchall()
    conn.close()
    return users

def get_richest_user_in_guild(guild_id: int):
    # (Hàm này giữ nguyên)
    conn = get_db_connection()
    richest = conn.execute("SELECT user_id, (local_balance_earned + local_balance_adadd) as total_local_wealth FROM user_guild_data WHERE guild_id = ? ORDER BY total_local_wealth DESC LIMIT 1", (guild_id,)).fetchone()
    conn.close()
    return richest
