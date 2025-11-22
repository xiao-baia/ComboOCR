"""
ComboOCR 后端模块
包含所有后端业务逻辑和工具函数
"""

__version__ = '2.0.0'
__author__ = 'ComboOCR Team'

# 导出主要接口
from backend.logger import logger, setup_logger
from backend.file_utils import allowed_file, temporary_file, cleanup_old_files
from backend.security import validate_upload_file, validate_image_content, setup_rate_limiter
from backend.ocr_service import OCRService, get_ocr_service

__all__ = [
    'logger',
    'setup_logger',
    'allowed_file',
    'temporary_file',
    'cleanup_old_files',
    'validate_upload_file',
    'validate_image_content',
    'setup_rate_limiter',
    'OCRService',
    'get_ocr_service',
]
