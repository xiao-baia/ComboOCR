"""
文件管理工具模块
提供文件上传、验证、临时文件管理等功能
"""
import os
import contextlib
from typing import Optional
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import time
import uuid
from config import ServerConfig
from backend.logger import logger

def allowed_file(filename: str) -> bool:
    """
    检查文件扩展名是否允许

    Args:
        filename: 文件名

    Returns:
        是否允许的文件类型
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ServerConfig.ALLOWED_EXTENSIONS

def generate_unique_filename(original_filename: str) -> str:
    """
    生成唯一的文件名，避免冲突

    Args:
        original_filename: 原始文件名

    Returns:
        唯一的文件名
    """
    filename = secure_filename(original_filename)
    unique_id = f"{int(time.time())}_{uuid.uuid4().hex[:8]}"
    base, ext = os.path.splitext(filename)
    return f"{base}_{unique_id}{ext}"

@contextlib.contextmanager
def temporary_file(file_obj: FileStorage, custom_filename: Optional[str] = None):
    """
    临时文件上下文管理器，自动清理临时文件

    Args:
        file_obj: 上传的文件对象
        custom_filename: 自定义文件名（可选）

    Yields:
        临时文件的完整路径

    Example:
        with temporary_file(uploaded_file) as filepath:
            process_image(filepath)
        # 文件会在退出上下文时自动删除
    """
    # 确保上传目录存在
    os.makedirs(ServerConfig.UPLOAD_FOLDER, exist_ok=True)

    # 生成文件名
    if custom_filename:
        filename = custom_filename
    else:
        filename = generate_unique_filename(file_obj.filename)

    filepath = os.path.join(ServerConfig.UPLOAD_FOLDER, filename)

    try:
        # 保存文件
        file_obj.save(filepath)
        logger.debug(f"临时文件已保存: {filepath}")
        yield filepath
    finally:
        # 清理文件
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                logger.debug(f"临时文件已删除: {filepath}")
            except Exception as e:
                logger.warning(f"删除临时文件失败 {filepath}: {e}")

def cleanup_old_files(directory: str, max_age_seconds: int = 3600):
    """
    清理指定目录中的旧文件

    Args:
        directory: 目录路径
        max_age_seconds: 文件最大保留时间（秒），默认1小时
    """
    if not os.path.exists(directory):
        return

    current_time = time.time()
    removed_count = 0

    try:
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath):
                file_age = current_time - os.path.getmtime(filepath)
                if file_age > max_age_seconds:
                    try:
                        os.remove(filepath)
                        removed_count += 1
                        logger.debug(f"已删除旧文件: {filepath}")
                    except Exception as e:
                        logger.warning(f"删除旧文件失败 {filepath}: {e}")

        if removed_count > 0:
            logger.info(f"清理了 {removed_count} 个旧文件")
    except Exception as e:
        logger.error(f"清理旧文件时出错: {e}")
