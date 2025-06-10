import json
import logging
from typing import List

MODS_FILE_PATH = "moderators.json"
logger = logging.getLogger(__name__)

def load_moderator_ids() -> List[int]:
    """Tải danh sách ID của moderator từ file moderators.json."""
    try:
        with open(MODS_FILE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get("moderator_ids", [])
    except (FileNotFoundError, json.JSONDecodeError):
        # Nếu file không tồn tại hoặc rỗng, tạo file mới với danh sách rỗng
        with open(MODS_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump({"moderator_ids": []}, f, indent=4)
        return []

def _save_moderator_ids(mod_ids: List[int]):
    """Lưu lại danh sách ID vào file moderators.json."""
    try:
        with open(MODS_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump({"moderator_ids": sorted(list(set(mod_ids)))}, f, indent=4)
    except Exception as e:
        logger.error(f"Lỗi khi lưu file moderators.json: {e}", exc_info=True)

def add_moderator_id(user_id: int) -> bool:
    """Thêm một ID moderator mới và trả về True nếu thành công."""
    current_ids = load_moderator_ids()
    if user_id in current_ids:
        return False  # Đã tồn tại
    current_ids.append(user_id)
    _save_moderator_ids(current_ids)
    return True

def remove_moderator_id(user_id: int) -> bool:
    """Xóa một ID moderator và trả về True nếu thành công."""
    current_ids = load_moderator_ids()
    if user_id not in current_ids:
        return False # Không tồn tại để xóa
    current_ids.remove(user_id)
    _save_moderator_ids(current_ids)
    return True
