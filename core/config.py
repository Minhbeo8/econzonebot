import os
from dotenv import load_dotenv

# Tải các biến môi trường từ file .env
load_dotenv()

# --- Cấu hình Xác thực & API ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# --- Cấu hình Bot cơ bản ---
COMMAND_PREFIX = "!"
BOT_OWNER_IDS = [1370417047070048276] 
BOT_VERSION = "v0.2-stable"
# --- Thời gian chờ (giây) ---
WORK_COOLDOWN = 3600
DAILY_COOLDOWN = 86400
CRIME_COOLDOWN = 1800
BEG_COOLDOWN = 300
FISH_COOLDOWN = 600
ROB_COOLDOWN = 7200
SLOTS_COOLDOWN = 5
CF_COOLDOWN = 5
DICE_COOLDOWN = 5

# --- Cân bằng Kinh tế & Game ---
# (Các cấu hình game khác giữ nguyên...)
WORK_PAYOUT_MIN = 150
WORK_PAYOUT_MAX = 500
WORK_XP_LOCAL_MIN = 5
WORK_XP_LOCAL_MAX = 20
WORK_XP_GLOBAL_MIN = 10
WORK_XP_GLOBAL_MAX = 30
DAILY_REWARD_MIN = 500
DAILY_REWARD_MAX = 1500
DAILY_XP_LOCAL_MIN = 15
DAILY_XP_LOCAL_MAX = 50
DAILY_XP_GLOBAL_MIN = 25
DAILY_XP_GLOBAL_MAX = 75
BEG_SUCCESS_RATE = 0.7
BEG_REWARD_MIN = 10
BEG_REWARD_MAX = 100
LAUNDER_TAX_RATE_MIN = 0.15
LAUNDER_TAX_RATE_MAX = 0.50
DEPOSIT_FEE_PERCENTAGE = 0.05
UPGRADE_VISA_COST = 20000
CRIME_SUCCESS_RATE = 0.60
ROB_SUCCESS_RATE = 0.50
ROB_FINE_RATE = 0.25
BASE_CATCH_CHANCE = 0.1
WANTED_LEVEL_CATCH_MULTIPLIER = 0.05
WANTED_LEVEL_CRIMINAL_THRESHOLD = 5.0
TAINTED_ITEM_SELL_LIMIT = 2
TAINTED_ITEM_SELL_RATE = 0.2
TAINTED_ITEM_TAX_RATE = 0.4
FOREIGN_ITEM_SELL_PENALTY = 0.5

# --- Chi phí Sinh tồn ---
WORK_ENERGY_COST = 10
WORK_HUNGER_COST = 5
CRIME_ENERGY_COST = 8
CRIME_HUNGER_COST = 4
ROB_ENERGY_COST = 12
ROB_HUNGER_COST = 6
FISH_ENERGY_COST = 5
FISH_HUNGER_COST = 3

# --- Cấu hình Tác vụ Sinh tồn ---
SURVIVAL_TICK_RATE_MINUTES = 20
SURVIVAL_STAT_DECAY = 1
SURVIVAL_HEALTH_REGEN = 2

# --- Dữ liệu Game (ít thay đổi) ---
CITIZEN_TITLES = { 0: "Công Dân", 10: "Người Có Tiếng Tăm", 25: "Nhân Vật Ưu Tú", 50: "Huyền Thoại Server" }
CRIMINAL_TITLES = { 0: "Tội Phạm Vặt", 10: "Kẻ Ngoài Vòng Pháp Luật", 25: "Trùm Tội Phạm", 50: "Bố Già" }
SLOTS_EMOJIS = ["🍒", "🍊", "🍋", "🔔", "⭐", "💎"]
FISH_CATCHES = { "🐠": 50, "🐟": 75, "🐡": 100, "🦑": 150, "🦐": 30, "🦀": 60, "👢": 5, "🔩": 1, "🪵": 10 }

# --- SỬA: Ánh xạ Lệnh không cần Prefix (Phím tắt) ---
BARE_COMMAND_MAP = {
    # Tài Khoản & Tổng Quan
    "balance": "balance", "bal": "balance",
    "bank": "bank",
    "deposit": "deposit", "dep": "deposit",
    "withdraw": "withdraw", "wd": "withdraw",
    "transfer": "transfer", "tf": "transfer",
    "leaderboard": "leaderboard", "lb": "leaderboard",
    "inventory": "inventory", "inv": "inventory",
    "visa": "visa",
    "howtoplay": "howtoplay", "h": "howtoplay", "guide": "howtoplay",

    # Kiếm Tiền & Cơ Hội
    "work": "work", "w": "work",
    "daily": "daily", "d": "daily",
    "beg": "beg", "b": "beg",
    "crime": "crime",
    "fish": "fish",
    "rob": "rob",
    "launder": "launder", "ruatien": "launder",

    # Giải Trí & Cờ Bạc
    "slots": "slots", "sl": "slots",
    "coinflip": "coinflip", "cf": "coinflip",
    "dice": "dice", "roll": "dice",

    # Cửa Hàng Vật Phẩm
    "shop": "shop", "store": "shop",
    "buy": "buy",
    "sell": "sell",
    "use": "use"
}
