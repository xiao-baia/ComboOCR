"""
安全验证模块
提供文件验证、图像验证等安全功能
"""
import os
from typing import Tuple, Optional
from werkzeug.datastructures import FileStorage
from PIL import Image
from config import ServerConfig, SecurityConfig
from backend.logger import logger

class ValidationError(Exception):
    """验证错误异常"""
    pass

def validate_file_size(file_obj: FileStorage) -> bool:
    """
    验证文件实际大小

    Args:
        file_obj: 文件对象

    Returns:
        是否通过验证

    Raises:
        ValidationError: 文件过大时抛出异常
    """
    # 保存当前位置
    current_position = file_obj.tell()

    # 移动到文件末尾获取大小
    file_obj.seek(0, os.SEEK_END)
    file_length = file_obj.tell()

    # 恢复到原始位置
    file_obj.seek(current_position)

    if file_length > ServerConfig.MAX_CONTENT_LENGTH:
        raise ValidationError(
            f"文件大小 {file_length} 字节超过限制 {ServerConfig.MAX_CONTENT_LENGTH} 字节"
        )

    logger.debug(f"文件大小验证通过: {file_length} 字节")
    return True

def validate_image_content(filepath: str) -> Tuple[bool, Optional[str]]:
    """
    验证文件是否为真实的图像文件

    Args:
        filepath: 图像文件路径

    Returns:
        (是否验证通过, 错误信息)
    """
    if not SecurityConfig.VALIDATE_IMAGE_CONTENT:
        return True, None

    try:
        # 尝试打开并验证图像
        with Image.open(filepath) as img:
            # 验证图像
            img.verify()

            # 重新打开以获取图像信息（verify后图像会被关闭）
            with Image.open(filepath) as img_info:
                width, height = img_info.size
                total_pixels = width * height

                # 检查图像尺寸，防止解压炸弹攻击
                if total_pixels > SecurityConfig.MAX_IMAGE_PIXELS:
                    error_msg = f"图像像素数 {total_pixels} 超过限制 {SecurityConfig.MAX_IMAGE_PIXELS}"
                    logger.warning(error_msg)
                    return False, error_msg

                logger.debug(f"图像验证通过: {width}x{height}, 格式: {img_info.format}")
                return True, None

    except (IOError, OSError) as e:
        error_msg = f"无效的图像文件: {str(e)}"
        logger.warning(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"图像验证失败: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def validate_upload_file(file_obj: FileStorage) -> Tuple[bool, Optional[str]]:
    """
    验证上传的文件

    Args:
        file_obj: 上传的文件对象

    Returns:
        (是否验证通过, 错误信息)
    """
    # 检查文件是否存在
    if not file_obj or file_obj.filename == '':
        return False, "未选择文件"

    # 检查文件扩展名
    from backend.file_utils import allowed_file
    if not allowed_file(file_obj.filename):
        supported = ', '.join(ServerConfig.ALLOWED_EXTENSIONS)
        return False, f"不支持的文件格式，支持的格式: {supported}"

    # 验证文件大小
    try:
        validate_file_size(file_obj)
    except ValidationError as e:
        return False, str(e)

    return True, None

def setup_rate_limiter(app):
    """
    设置速率限制器

    Args:
        app: Flask应用实例

    Returns:
        配置好的Limiter实例
    """
    if not SecurityConfig.RATE_LIMIT_ENABLED:
        logger.info("速率限制已禁用")
        return None

    try:
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address

        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            default_limits=[SecurityConfig.RATE_LIMIT_DEFAULT],
            storage_uri=SecurityConfig.RATE_LIMIT_STORAGE_URL
        )
        logger.info(f"速率限制已启用: {SecurityConfig.RATE_LIMIT_DEFAULT}")
        return limiter
    except ImportError:
        logger.warning("flask-limiter 未安装，速率限制功能不可用")
        return None
