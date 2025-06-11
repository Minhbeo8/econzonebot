import nextcord
from nextcord.ext import commands, tasks
import logging
import os
import io
from datetime import datetime
import zipfile

# Các thư viện của Google
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

logger = logging.getLogger(__name__)

# --- Cấu hình ---
# Đường dẫn đến file chìa khóa bạn đã tải về
CREDENTIALS_FILE = 'gdrive_credentials.json'
# ID của thư mục trên Google Drive mà bạn đã chia sẻ
GDRIVE_FOLDER_ID = '1erDyrDEAc36h34UHFoT3GiZlAtwoLLTW'
# Quyền truy cập cần thiết
SCOPES = ['https://www.googleapis.com/auth/drive.file']
# Tần suất sao lưu (đơn vị: giờ)
BACKUP_INTERVAL_HOURS = 6
# Giữ lại bao nhiêu bản sao lưu gần nhất
MAX_BACKUPS_TO_KEEP = 7
# Đường dẫn đến file CSDL cần sao lưu
DB_FILE_PATH = 'data/econzone.sqlite'


class GDriveBackupTaskCog(commands.Cog, name="Google Drive Backup Task"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Kiểm tra các điều kiện cần thiết trước khi khởi động task
        if not os.path.exists(CREDENTIALS_FILE):
            logger.error(f"GDRIVE_BACKUP: Không tìm thấy file credentials '{CREDENTIALS_FILE}'. Task sẽ không chạy.")
            return
        if '1erDyrDEAc36h34UHFoT3GiZlAtwoLLTW' in GDRIVE_FOLDER_ID:
            logger.error("GDRIVE_BACKUP: Vui lòng cấu hình GDRIVE_FOLDER_ID trong gdrive_backup_task.py. Task sẽ không chạy.")
            return
            
        self.backup_task_loop.start()
        logger.info(f"Google Drive Backup Task has been started. Backing up every {BACKUP_INTERVAL_HOURS} hours.")

    def cog_unload(self):
        self.backup_task_loop.cancel()

    def get_gdrive_service(self):
        """Hàm xác thực và tạo đối tượng service để tương tác với Google Drive."""
        creds = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds, cache_discovery=False)
        return service

    @tasks.loop(hours=BACKUP_INTERVAL_HOURS)
    async def backup_task_loop(self):
        logger.info("GDRIVE_BACKUP: Starting scheduled database backup...")

        if not os.path.exists(DB_FILE_PATH):
            logger.warning(f"GDRIVE_BACKUP: Database file not found at '{DB_FILE_PATH}'. Skipping backup.")
            return

        try:
            # Chạy các tác vụ I/O trong một executor riêng để không làm nghẽn bot
            await self.bot.loop.run_in_executor(None, self.perform_backup)
            logger.info("GDRIVE_BACKUP: Backup process completed successfully.")
        except Exception as e:
            logger.error(f"GDRIVE_BACKUP: An error occurred during the backup process: {e}", exc_info=True)

    def perform_backup(self):
        """Hàm thực hiện việc nén, tải lên và dọn dẹp."""
        service = self.get_gdrive_service()
        
        # Tạo file nén trong bộ nhớ
        zip_buffer = io.BytesIO()
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        zip_filename = f'econzone_backup_{timestamp}.zip'
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(DB_FILE_PATH, os.path.basename(DB_FILE_PATH))
        
        zip_buffer.seek(0)

        # Tải file lên Google Drive
        file_metadata = {'name': zip_filename, 'parents': [GDRIVE_FOLDER_ID]}
        media = MediaIoBaseUpload(zip_buffer, mimetype='application/zip', resumable=True)
        
        logger.info(f"GDRIVE_BACKUP: Uploading '{zip_filename}' to Google Drive...")
        uploaded_file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        logger.info(f"GDRIVE_BACKUP: File uploaded successfully. File ID: {uploaded_file.get('id')}")

        # Dọn dẹp các bản sao lưu cũ
        self.cleanup_old_backups(service)

    def cleanup_old_backups(self, service):
        """Xóa các bản sao lưu cũ, chỉ giữ lại số lượng đã định."""
        logger.info("GDRIVE_BACKUP: Checking for old backups to delete...")
        query = f"'{GDRIVE_FOLDER_ID}' in parents and trashed = false"
        results = service.files().list(q=query, pageSize=100, fields="nextPageToken, files(id, name, createdTime)", orderBy="createdTime desc").execute()
        items = results.get('files', [])

        if len(items) > MAX_BACKUPS_TO_KEEP:
            # Các file được sắp xếp từ mới nhất đến cũ nhất, nên ta sẽ xóa những file ở cuối
            files_to_delete = items[MAX_BACKUPS_TO_KEEP:]
            logger.info(f"GDRIVE_BACKUP: Found {len(files_to_delete)} old backups to delete.")
            for item in files_to_delete:
                try:
                    service.files().delete(fileId=item['id']).execute()
                    logger.info(f"GDRIVE_BACKUP: Deleted old backup file: {item['name']}")
                except Exception as e:
                    logger.error(f"GDRIVE_BACKUP: Failed to delete file {item['name']}: {e}")
        else:
            logger.info("GDRIVE_BACKUP: No old backups to delete.")

    @backup_task_loop.before_loop
    async def before_backup_task(self):
        await self.bot.wait_until_ready()

def setup(bot: commands.Bot):
    bot.add_cog(GDriveBackupTaskCog(bot))
