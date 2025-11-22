"""
日志工具模块
提供统一的日志记录功能
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from config import LogConfig

def setup_logger(name: str = 'ComboOCR') -> logging.Logger:
    """
    设置并返回配置好的logger实例

    Args:
        name: logger名称

    Returns:
        配置好的logger对象
    """
    # 创建logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LogConfig.LOG_LEVEL))

    # 避免重复添加handler
    if logger.handlers:
        return logger

    # 创建日志目录
    os.makedirs(LogConfig.LOG_DIR, exist_ok=True)

    # 创建formatter
    formatter = logging.Formatter(LogConfig.LOG_FORMAT)

    # 文件handler - 使用RotatingFileHandler自动轮转
    file_handler = RotatingFileHandler(
        LogConfig.LOG_FILE,
        maxBytes=LogConfig.LOG_MAX_BYTES,
        backupCount=LogConfig.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # 控制台handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # 添加handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# 创建默认logger实例
logger = setup_logger()
