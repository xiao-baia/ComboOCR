简体中文 | [English](./Readme_en.md) |

# ComboOCR - 智能文本识别系统

<div align="center">
    <img src="images\ComboOCR_logo.svg" alt="logo" style="zoom:400%;" />
</div>

![ComboOCR](https://img.shields.io/badge/ComboOCR-%E6%99%BA%E8%83%BDOCR-blue) ![Python](https://img.shields.io/badge/Python-3.8+-green) ![Flask](https://img.shields.io/badge/Flask-2.3-orange) ![Version](https://img.shields.io/badge/Version-2.0.0-success)

**基于深度学习的高精度OCR文本识别系统 - 重构优化版**

> 🎉 **v2.0.0 重大更新**: 完全重构代码架构，前后端分离，模块化设计，安全性和可维护性大幅提升！详见 [OPTIMIZATIONS.md](./OPTIMIZATIONS.md)

## 📖 项目简介

ComboOCR是一个高精度的OCR文本识别系统，集成了多种先进的深度学习模型：

- **PPOCRv5微调模型**: 基于PPOCRv5的检测、识别和文字方向分类模型
- **外观增强模型**: 去除阴影、噪音，提升图像质量
- **扭曲矫正模型**: 自动矫正文档扭曲变形

### ✨ v2.0 新特性

- 🏗️ **前后端分离**: 模块化架构，代码可维护性提升 80%
- 🔒 **安全增强**: 文件验证、速率限制、防恶意攻击
- 📝 **专业日志**: 完善的日志系统，支持文件轮转
- ⚡ **性能优化**: 模型预热、单例模式、自动资源清理
- 🎨 **代码质量**: 类型注解、配置文件化、消除代码重复

## 🚀 快速开始

### 环境要求

- Python 3.8+
- CUDA (可选，用于GPU加速)

### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/your-repo/ComboOCR.git
cd ComboOCR
```

2. **安装依赖**
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

3. **下载模型文件**

将模型文件存储于 `./models` 文件夹下：

- **扭曲矫正模型**: 基于 [DocTr++](https://github.com/fh2019ustc/DocTr-Plus) 实现
  - 下载: [百度网盘](https://pan.baidu.com/s/1mz_Mqwm9i_b7xfj22yU_7A)，提取码：`68av`
  - 路径: `./models/doctr_plus/model.pt`

- **外观增强模型**: 基于 [GCDRNet](https://ieeexplore.ieee.org/abstract/document/10268585/authors#authors) 实现
  - 下载: [百度网盘](https://pan.baidu.com/s/1mz_Mqwm9i_b7xfj22yU_7A)，提取码：`68av`
  - 路径: `./models/gcdr_net/gcnet/checkpoint.pkl` 和 `./models/gcdr_net/drnet/checkpoint.pkl`

模型目录结构：
```
models/
├── doctr_plus/
│   └── model.pt
└── gcdr_net/
    ├── gcnet/
    │   └── checkpoint.pkl
    └── drnet/
        └── checkpoint.pkl
```

### 启动服务

```bash
python app.py
```

启动后访问 `http://localhost:5000` 使用Web界面。

### 配置说明

可在 `config.py` 中修改配置：

```python
# 服务器配置
ServerConfig.HOST = '127.0.0.1'
ServerConfig.PORT = 5000

# 上传限制
ServerConfig.MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

# 安全配置
SecurityConfig.RATE_LIMIT_DEFAULT = "10 per minute"  # 速率限制
```

## 📡 API接口

### 健康检查

**端点**: `GET /health`

**响应示例**:
```json
{
  "status": "OK",
  "message": "Server is running",
  "enhancement_available": true
}
```

### 图像识别接口

**端点**: `POST /process`

**请求参数**:

| 参数            | 类型    | 必填 | 说明                             |
| --------------- | ------- | ---- | -------------------------------- |
| image           | file    | 是   | 图像文件 (支持 png/jpg/jpeg/bmp) |
| use_enhancement | boolean | 否   | 是否启用外观增强 (默认: false)   |
| use_dewarp      | boolean | 否   | 是否启用扭曲矫正 (默认: false)   |

**请求示例**:

```bash
curl -X POST http://localhost:5000/process \
  -F "image=@test.jpg" \
  -F "use_enhancement=true" \
  -F "use_dewarp=true"
```

**响应示例**:

```json
{
  "sorted_text": "识别出的文本内容",
  "ocr_result": [
    {
      "polygon": [x1, y1, x2, y2, x3, y3, x4, y4],
      "text": "文本内容"
    }
  ],
  "visualization": "base64编码的可视化图像",
  "processing_info": {
    "use_enhancement": true,
    "use_dewarp": true,
    "text_regions_count": 5
  }
}
```

## 📁 项目结构

```
ComboOCR/
├── app.py                     # 主应用入口 (新)
├── config.py                  # 配置文件 (新)
├── requirements.txt           # Python依赖
├── OPTIMIZATIONS.md           # 优化说明文档 (新)
├── backend/                   # 后端模块 (新)
│   ├── __init__.py
│   ├── logger.py             # 日志系统
│   ├── file_utils.py         # 文件管理工具
│   ├── security.py           # 安全验证模块
│   └── ocr_service.py        # OCR核心服务
├── frontend/                  # 前端代码 (新)
│   ├── templates/
│   │   └── index.html        # 主页面
│   └── static/
│       ├── css/style.css     # 样式文件
│       └── js/app.js         # 前端逻辑
├── model/                     # 深度学习模型定义
│   ├── GeoTr.py
│   ├── unext.py
│   └── ...
├── onnxocr/                   # OCR引擎
│   ├── onnx_paddleocr.py
│   ├── predict_*.py
│   └── ...
├── utils/                     # 工具函数
│   ├── utils_doctr_plus.py
│   └── utils_gcdrnet.py
├── models/                    # 模型文件目录 (需手动下载)
├── logs/                      # 日志目录 (自动创建)
└── temp_uploads/              # 临时文件目录 (自动创建)
```

## 🔧 高级功能

### 日志系统

日志文件位于 `logs/ocr_system.log`，支持自动轮转：

```python
from backend.logger import logger

logger.info("信息日志")
logger.warning("警告日志")
logger.error("错误日志")
```

### 安全特性

- ✅ 文件类型验证
- ✅ 文件大小限制
- ✅ 图像内容真实性验证
- ✅ 速率限制（默认每分钟10次请求）
- ✅ 防解压炸弹攻击
- ✅ 临时文件自动清理

### 临时文件管理

系统会自动清理超过1小时的临时文件，也可手动触发：

```python
from backend.file_utils import cleanup_old_files

cleanup_old_files('temp_uploads/', max_age_seconds=3600)
```

## 🎨 OCR结果展示

### Web界面展示
<div align="center">
    <img src="images/web_show.png" alt="web" style="zoom:50%;" />
</div>

### demo1
<div align="center">
    <img src="images\show1.png" alt="show1" style="zoom:30%;" />
</div>

### demo2
<div align="center">
    <img src="images\show2.png" alt="show2" style="zoom:13%;" />
</div>

### demo3（扭曲矫正）
<div align="center">
    <img src="images\dewarp_show.jpeg" alt="dewarp" />
</div>

### demo4（外观增强）
<div align="center">
    <img src="images\enhance_show.jpeg" alt="enhance" />
</div>

### demo5（手写体）
<div align="center">
    <img src="images\hand_writing_show.png" alt="hand_writing" style="zoom:40%;" />
</div>

## 🐛 故障排除

### 常见问题

**Q: 启动时提示模型文件不存在**
```
A: 请确保已下载模型文件并放置在正确的路径下，参考"下载模型文件"章节
```

**Q: 外观增强功能不可用**
```
A: 访问 /health 接口检查 enhancement_available 状态，确保外观增强模型已正确加载
```

**Q: 速率限制触发**
```
A: 默认限制为每分钟10次请求，可在 config.py 中调整 SecurityConfig.RATE_LIMIT_DEFAULT
```

**Q: 日志文件过大**
```
A: 日志系统自动轮转，保留最近5个文件，每个最大10MB
```

## 📝 更新日志

### v2.0.0 (2025-11-22)

**架构重构**
- 前后端完全分离
- 模块化设计，创建 backend/ 目录
- 主应用从 1841 行优化到 150 行

**新增功能**
- 专业日志系统（文件轮转）
- 安全验证模块（文件验证、速率限制）
- 临时文件自动清理
- 模型预热功能

**代码质量**
- 添加类型注解
- 配置文件化管理
- 消除通配符导入
- 完善代码注释

详细优化内容请查看 [OPTIMIZATIONS.md](./OPTIMIZATIONS.md)

## 📄 许可证

本项目采用 [LICENSE](./LICENSE) 中规定的许可证。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📮 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue: [GitHub Issues](https://github.com/your-repo/ComboOCR/issues)
- Email: your-email@example.com

---

**ComboOCR v2.0** - 让文字识别更简单、更安全、更高效！
