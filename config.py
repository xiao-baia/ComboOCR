"""
ComboOCR 配置文件
包含所有系统配置、路径和常量定义
"""
import os

# 基础目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 服务器配置
class ServerConfig:
    """服务器相关配置"""
    HOST = '127.0.0.1'
    PORT = 5000
    DEBUG = False

    # 上传配置
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'temp_uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp'}

# 模型配置
class ModelConfig:
    """模型路径和参数配置"""
    MODELS_DIR = os.path.join(BASE_DIR, 'models')

    # 模型路径
    DEWARP_MODEL_PATH = os.path.join(MODELS_DIR, 'doctr_plus', 'model.pt')
    GCNET_MODEL_PATH = os.path.join(MODELS_DIR, 'gcdr_net', 'gcnet', 'checkpoint.pkl')
    DRNET_MODEL_PATH = os.path.join(MODELS_DIR, 'gcdr_net', 'drnet', 'checkpoint.pkl')

    # 模型参数
    DEWARP_SIZE = 2560
    DEWARP_INPUT_SIZE = 288
    ENHANCEMENT_IMG_SIZE = 512

    # OCR 配置
    USE_ANGLE_CLS = True
    USE_GPU = False
    REC_IMAGE_SHAPE = "3, 48, 320"

# 图像处理配置
class ImageConfig:
    """图像处理相关配置"""
    # 可视化配置
    VISUALIZATION_COLORS = [
        (255, 99, 71),   # 番茄红
        (60, 179, 113),  # 海洋绿
        (30, 144, 255),  # 道奇蓝
        (255, 165, 0),   # 橙色
        (218, 112, 214), # 兰花紫
        (32, 178, 170),  # 浅海洋绿
        (255, 20, 147),  # 深粉红
        (0, 191, 255),   # 深天蓝
        (50, 205, 50),   # 酸橙绿
        (255, 215, 0),   # 金色
    ]

    # 字体配置
    FONT_PATH = os.path.join(BASE_DIR, 'onnxocr', 'fonts', 'simfang.ttf')
    DEFAULT_FONT_SIZE = 100
    MIN_FONT_SIZE = 12

# 日志配置
class LogConfig:
    """日志系统配置"""
    LOG_DIR = os.path.join(BASE_DIR, 'logs')
    LOG_FILE = os.path.join(LOG_DIR, 'ocr_system.log')
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5

# 安全配置
class SecurityConfig:
    """安全相关配置"""
    # 速率限制
    RATE_LIMIT_ENABLED = True
    RATE_LIMIT_DEFAULT = "10 per minute"
    RATE_LIMIT_STORAGE_URL = "memory://"

    # CORS配置
    CORS_ORIGINS = ['http://127.0.0.1:5000', 'http://localhost:5000']

    # 文件验证
    VALIDATE_IMAGE_CONTENT = True
    MAX_IMAGE_PIXELS = 178956970  # 防止解压炸弹攻击

# 开发环境配置
class DevelopmentConfig(ServerConfig):
    """开发环境配置"""
    DEBUG = True

# 生产环境配置
class ProductionConfig(ServerConfig):
    """生产环境配置"""
    DEBUG = False

# 根据环境变量选择配置
ENV = os.getenv('FLASK_ENV', 'production')
if ENV == 'development':
    Config = DevelopmentConfig
else:
    Config = ProductionConfig
