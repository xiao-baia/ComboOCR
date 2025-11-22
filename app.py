"""
ComboOCR - 智能文本识别系统
主应用程序入口
"""
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import sys

# 导入配置
from config import ServerConfig, SecurityConfig

# 导入后端模块
from backend.logger import logger
from backend.file_utils import temporary_file, cleanup_old_files
from backend.security import setup_rate_limiter, validate_upload_file, validate_image_content
from backend.ocr_service import get_ocr_service

# 创建Flask应用
app = Flask(__name__,
            template_folder='frontend/templates',
            static_folder='frontend/static')

# CORS配置
CORS(app, origins=SecurityConfig.CORS_ORIGINS)

# 应用配置
app.config['UPLOAD_FOLDER'] = ServerConfig.UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = ServerConfig.MAX_CONTENT_LENGTH

# 设置速率限制器
limiter = setup_rate_limiter(app)

# 初始化OCR服务（全局单例）
logger.info("初始化OCR服务...")
ocr_service = get_ocr_service()
logger.info("OCR服务初始化完成")


@app.route('/')
def index():
    """首页路由"""
    return render_template('index.html')


@app.route('/static/<path:filename>')
def serve_static(filename):
    """静态文件服务"""
    return send_from_directory('frontend/static', filename)


@app.route('/health')
def health_check():
    """健康检查接口"""
    enhancement_available = ocr_service.is_enhancement_available()
    return jsonify({
        "status": "OK",
        "message": "Server is running",
        "enhancement_available": enhancement_available
    })


@app.route('/process', methods=['POST'])
def process():
    """
    图像处理接口
    接收上传的图像文件，进行OCR识别并返回结果
    """
    # 1. 验证请求中是否有文件
    if 'image' not in request.files:
        logger.warning("请求中没有图像文件")
        return jsonify({"error": "No image part"}), 400

    file = request.files['image']

    # 2. 验证上传的文件
    is_valid, error_msg = validate_upload_file(file)
    if not is_valid:
        logger.warning(f"文件验证失败: {error_msg}")
        return jsonify({"error": error_msg}), 400

    # 3. 获取处理参数
    use_enhancement = request.form.get('use_enhancement', 'false').lower() == 'true'
    use_dewarp = request.form.get('use_dewarp', 'false').lower() == 'true'

    # 4. 检查外观增强功能是否可用
    if use_enhancement and not ocr_service.is_enhancement_available():
        error_msg = "外观增强模型未加载，无法使用此功能"
        logger.warning(error_msg)
        return jsonify({"error": error_msg}), 400

    try:
        # 5. 使用临时文件管理器处理文件
        with temporary_file(file) as filepath:
            # 验证图像内容
            is_valid_image, error_msg = validate_image_content(filepath)
            if not is_valid_image:
                return jsonify({"error": error_msg}), 400

            # 处理图像
            logger.info(f"开始处理图像: {file.filename}")
            result = ocr_service.process_image(
                filepath,
                use_enhancement=use_enhancement,
                use_dewarp=use_dewarp
            )
            logger.info(f"图像处理完成: {file.filename}")

        return jsonify(result)

    except Exception as e:
        logger.error(f"处理图像时发生错误: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.before_request
def before_request():
    """请求前处理 - 清理旧的临时文件"""
    cleanup_old_files(ServerConfig.UPLOAD_FOLDER, max_age_seconds=3600)


@app.errorhandler(413)
def request_entity_too_large(error):
    """处理文件过大错误"""
    return jsonify({
        "error": f"文件过大，最大允许 {ServerConfig.MAX_CONTENT_LENGTH / 1024 / 1024} MB"
    }), 413


@app.errorhandler(429)
def ratelimit_handler(e):
    """处理速率限制错误"""
    return jsonify({
        "error": "请求过于频繁，请稍后再试"
    }), 429


@app.errorhandler(500)
def internal_server_error(error):
    """处理内部服务器错误"""
    logger.error(f"内部服务器错误: {str(error)}", exc_info=True)
    return jsonify({
        "error": "服务器内部错误，请稍后重试"
    }), 500


if __name__ == '__main__':
    logger.info(f"启动ComboOCR服务器...")
    logger.info(f"  - 地址: {ServerConfig.HOST}:{ServerConfig.PORT}")
    logger.info(f"  - 调试模式: {ServerConfig.DEBUG}")
    logger.info(f"  - 外观增强: {'可用' if ocr_service.is_enhancement_available() else '不可用'}")

    app.run(
        host=ServerConfig.HOST,
        port=ServerConfig.PORT,
        debug=ServerConfig.DEBUG
    )
