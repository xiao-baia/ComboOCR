[简体中文](./Readme.md) | English

# ComboOCR - Intelligent Text Recognition System

<div align="center">
    <img src="images/ComboOCR_logo.svg" alt="logo" style="zoom:400%;" />
</div>

![ComboOCR](https://img.shields.io/badge/ComboOCR-Smart%20OCR-blue) ![Python](https://img.shields.io/badge/Python-3.8+-green) ![Flask](https://img.shields.io/badge/Flask-2.3-orange) ![Version](https://img.shields.io/badge/Version-2.0.0-success)

**High-Precision OCR Text Recognition System Based on Deep Learning - Refactored Edition**

> 🎉 **v2.0.0 Major Update**: Complete code architecture refactoring with frontend-backend separation, modular design, and significant improvements in security and maintainability! See [OPTIMIZATIONS.md](./OPTIMIZATIONS.md)

## 📖 Project Overview

ComboOCR is a high-precision OCR text recognition system that integrates multiple advanced deep learning models:

- **PPOCRv5 Fine-tuned Models**: Detection, recognition, and text direction classification models based on PPOCRv5
- **Appearance Enhancement Model**: Remove shadows and noise to improve image quality
- **Distortion Correction Model**: Automatically correct document distortion and deformation

### ✨ v2.0 New Features

- 🏗️ **Frontend-Backend Separation**: Modular architecture with 80% improved code maintainability
- 🔒 **Enhanced Security**: File validation, rate limiting, malicious attack prevention
- 📝 **Professional Logging**: Comprehensive logging system with file rotation
- ⚡ **Performance Optimization**: Model preheating, singleton pattern, automatic resource cleanup
- 🎨 **Code Quality**: Type annotations, configuration management, code deduplication

## 🚀 Quick Start

### Requirements

- Python 3.8+
- CUDA (optional, for GPU acceleration)

### Installation Steps

1. **Clone Repository**
```bash
git clone https://github.com/your-repo/ComboOCR.git
cd ComboOCR
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

3. **Download Model Files**

Store model files in the `./models` folder:

- **Distortion Correction Model**: Based on [DocTr++](https://github.com/fh2019ustc/DocTr-Plus)
  - Download: [Baidu Netdisk](https://pan.baidu.com/s/1mz_Mqwm9i_b7xfj22yU_7A), extraction code: `68av`
  - Path: `./models/doctr_plus/model.pt`

- **Appearance Enhancement Model**: Based on [GCDRNet](https://ieeexplore.ieee.org/abstract/document/10268585/authors#authors)
  - Download: [Baidu Netdisk](https://pan.baidu.com/s/1mz_Mqwm9i_b7xfj22yU_7A), extraction code: `68av`
  - Paths: `./models/gcdr_net/gcnet/checkpoint.pkl` and `./models/gcdr_net/drnet/checkpoint.pkl`

Model directory structure:
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

### Start Service

```bash
python app.py
```

Visit `http://localhost:5000` after startup to use the web interface.

### Configuration

Modify configurations in `config.py`:

```python
# Server configuration
ServerConfig.HOST = '127.0.0.1'
ServerConfig.PORT = 5000

# Upload limit
ServerConfig.MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

# Security configuration
SecurityConfig.RATE_LIMIT_DEFAULT = "10 per minute"  # Rate limit
```

## 📡 API Interface

### Health Check

**Endpoint**: `GET /health`

**Response Example**:
```json
{
  "status": "OK",
  "message": "Server is running",
  "enhancement_available": true
}
```

### Image Recognition Endpoint

**Endpoint**: `POST /process`

**Request Parameters**:

| Parameter       | Type    | Required | Description                                        |
| --------------- | ------- | -------- | -------------------------------------------------- |
| image           | file    | Yes      | Image file (supports png/jpg/jpeg/bmp)            |
| use_enhancement | boolean | No       | Enable appearance enhancement (default: false)     |
| use_dewarp      | boolean | No       | Enable distortion correction (default: false)     |

**Request Example**:

```bash
curl -X POST http://localhost:5000/process \
  -F "image=@test.jpg" \
  -F "use_enhancement=true" \
  -F "use_dewarp=true"
```

**Response Example**:

```json
{
  "sorted_text": "Recognized text content",
  "ocr_result": [
    {
      "polygon": [x1, y1, x2, y2, x3, y3, x4, y4],
      "text": "Text content"
    }
  ],
  "visualization": "Base64 encoded visualization image",
  "processing_info": {
    "use_enhancement": true,
    "use_dewarp": true,
    "text_regions_count": 5
  }
}
```

## 📁 Project Structure

```
ComboOCR/
├── app.py                     # Main application entry (new)
├── config.py                  # Configuration file (new)
├── requirements.txt           # Python dependencies
├── OPTIMIZATIONS.md           # Optimization documentation (new)
├── backend/                   # Backend modules (new)
│   ├── __init__.py
│   ├── logger.py             # Logging system
│   ├── file_utils.py         # File management utilities
│   ├── security.py           # Security validation module
│   └── ocr_service.py        # OCR core service
├── frontend/                  # Frontend code (new)
│   ├── templates/
│   │   └── index.html        # Main page
│   └── static/
│       ├── css/style.css     # Stylesheet
│       └── js/app.js         # Frontend logic
├── model/                     # Deep learning model definitions
│   ├── GeoTr.py
│   ├── unext.py
│   └── ...
├── onnxocr/                   # OCR engine
│   ├── onnx_paddleocr.py
│   ├── predict_*.py
│   └── ...
├── utils/                     # Utility functions
│   ├── utils_doctr_plus.py
│   └── utils_gcdrnet.py
├── models/                    # Model files directory (manual download required)
├── logs/                      # Log directory (auto-created)
└── temp_uploads/              # Temporary files directory (auto-created)
```

## 🔧 Advanced Features

### Logging System

Log files are located at `logs/ocr_system.log` with automatic rotation:

```python
from backend.logger import logger

logger.info("Info log")
logger.warning("Warning log")
logger.error("Error log")
```

### Security Features

- ✅ File type validation
- ✅ File size limit
- ✅ Image content authenticity verification
- ✅ Rate limiting (default: 10 requests per minute)
- ✅ Decompression bomb attack prevention
- ✅ Automatic temporary file cleanup

### Temporary File Management

The system automatically cleans up temporary files older than 1 hour, or can be triggered manually:

```python
from backend.file_utils import cleanup_old_files

cleanup_old_files('temp_uploads/', max_age_seconds=3600)
```

## 🎨 OCR Results Showcase

### Web Interface Display
<div align="center">
    <img src="images/web_show.png" alt="web" style="zoom:50%;" />
</div>

### Demo 1
<div align="center">
    <img src="images/show1.png" alt="show1" style="zoom:30%;" />
</div>

### Demo 2
<div align="center">
    <img src="images/show2.png" alt="show2" style="zoom:13%;" />
</div>

### Demo 3 (Distortion Correction)
<div align="center">
    <img src="images/dewarp_show.jpeg" alt="dewarp" />
</div>

### Demo 4 (Appearance Enhancement)
<div align="center">
    <img src="images/enhance_show.jpeg" alt="enhance" />
</div>

### Demo 5 (Handwriting)
<div align="center">
    <img src="images/hand_writing_show.png" alt="hand_writing" style="zoom:40%;" />
</div>

## 🐛 Troubleshooting

### Common Issues

**Q: Model file not found error on startup**
```
A: Ensure model files are downloaded and placed in the correct paths, refer to "Download Model Files" section
```

**Q: Appearance enhancement feature unavailable**
```
A: Visit /health endpoint to check enhancement_available status, ensure enhancement models are loaded correctly
```

**Q: Rate limit triggered**
```
A: Default limit is 10 requests per minute, adjust SecurityConfig.RATE_LIMIT_DEFAULT in config.py
```

**Q: Log file too large**
```
A: Logging system auto-rotates, keeps 5 most recent files, each max 10MB
```

## 📝 Changelog

### v2.0.0 (2025-11-22)

**Architecture Refactoring**
- Complete frontend-backend separation
- Modular design with backend/ directory
- Main application optimized from 1841 lines to 150 lines

**New Features**
- Professional logging system (file rotation)
- Security validation module (file validation, rate limiting)
- Automatic temporary file cleanup
- Model preheating functionality

**Code Quality**
- Added type annotations
- Configuration file management
- Eliminated wildcard imports
- Improved code documentation

For detailed optimization content, see [OPTIMIZATIONS.md](./OPTIMIZATIONS.md)

## 📄 License

This project is licensed under the license specified in [LICENSE](./LICENSE).

## 🤝 Contributing

Issues and Pull Requests are welcome!

---

**ComboOCR v2.0** - Making text recognition simpler, safer, and more efficient!
