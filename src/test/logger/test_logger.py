#test_logger
import logging

# Cấu hình logging để ghi vào file
logging.basicConfig(
    level=logging.INFO,
    filename='test_code/app.log',  # Lưu log vào file app.log
    filemode='a',        # Chế độ append
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    # Mô phỏng lỗi
    value = int("abc")  # Chuyển đổi chuỗi không hợp lệ thành số
except ValueError as e:
    logger.error("Lỗi chuyển đổi giá trị: %s", e)