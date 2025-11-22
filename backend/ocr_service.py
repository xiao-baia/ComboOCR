"""
OCR 服务模块
包含所有OCR相关的核心业务逻辑
"""
import os
import sys
import cv2
import torch
import numpy as np
import base64
import gc
from typing import Dict, List, Tuple, Optional, Any
from PIL import Image, ImageDraw, ImageFont
import torch.nn.functional as F

from onnxocr.onnx_paddleocr import ONNXPaddleOcr
from utils.utils_doctr_plus import DocTr_Plus
from utils.utils_gcdrnet import convert_state_dict, stride_integral
from model.unext import UNext_full_resolution_padding, UNext_full_resolution_padding_L_py_L
from config import ModelConfig, ImageConfig
from backend.logger import logger


class OCRService:
    """OCR服务类，封装所有OCR相关功能"""

    def __init__(self, device_name: str = None):
        """
        初始化OCR服务

        Args:
            device_name: 设备名称，如 'cuda:0' 或 'cpu'
        """
        if device_name is None:
            device_name = "cuda:0" if torch.cuda.is_available() else "cpu"

        self.device = torch.device(device_name)
        self.models = None
        self._init_models()

    def _init_models(self):
        """初始化所有模型"""
        logger.info("正在加载模型...")

        try:
            # ONNX OCR模型 (检测+识别一体) - 必须加载
            ocr_model = ONNXPaddleOcr(
                use_angle_cls=ModelConfig.USE_ANGLE_CLS,
                use_gpu=ModelConfig.USE_GPU
            )
            logger.info("ONNX OCR 模型加载成功")

            # 文本图像扭曲矫正模型(DocTr++) - 必须加载
            if not os.path.exists(ModelConfig.DEWARP_MODEL_PATH):
                raise FileNotFoundError(f"dewarp模型文件不存在: {ModelConfig.DEWARP_MODEL_PATH}")

            dewarp_model = DocTr_Plus(weights=ModelConfig.DEWARP_MODEL_PATH, device=self.device)
            logger.info("扭曲矫正模型加载成功")

            # 文本图像外观增强模型(GCDRNet) - 可选加载
            gcnet = None
            drnet = None
            try:
                if os.path.exists(ModelConfig.GCNET_MODEL_PATH) and \
                   os.path.exists(ModelConfig.DRNET_MODEL_PATH):
                    gcnet = UNext_full_resolution_padding(
                        num_classes=3,
                        input_channels=3,
                        img_size=ModelConfig.ENHANCEMENT_IMG_SIZE
                    ).to(self.device)
                    state = convert_state_dict(
                        torch.load(ModelConfig.GCNET_MODEL_PATH, map_location=self.device)['model_state']
                    )
                    gcnet.load_state_dict(state)
                    gcnet.eval()
                    logger.info("gcnet模型加载成功")

                    drnet = UNext_full_resolution_padding_L_py_L(
                        num_classes=3,
                        input_channels=6,
                        img_size=ModelConfig.ENHANCEMENT_IMG_SIZE
                    ).to(self.device)
                    state = convert_state_dict(
                        torch.load(ModelConfig.DRNET_MODEL_PATH, map_location=self.device)['model_state']
                    )
                    drnet.load_state_dict(state)
                    drnet.eval()
                    logger.info("drnet模型加载成功")
                else:
                    logger.warning("外观增强模型文件未找到，将跳过外观增强功能")

            except Exception as e:
                logger.error(f"外观增强模型加载失败: {str(e)}")
                logger.warning("将继续运行，但外观增强功能不可用")
                gcnet = None
                drnet = None

            logger.info(f"模型初始化完成！使用设备: {self.device}")

            self.models = {
                'ocr_model': ocr_model,
                'gcnet': gcnet,
                'drnet': drnet,
                'dewarp_model': dewarp_model
            }

            # 模型预热
            self._warmup_models()

        except Exception as e:
            logger.error(f"关键模型加载失败: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    def _warmup_models(self):
        """预热模型，避免首次推理慢"""
        logger.info("预热模型...")
        try:
            dummy_image = np.zeros((100, 100, 3), dtype=np.uint8)
            _ = self.models['ocr_model'].ocr(dummy_image)
            logger.info("模型预热完成")
        except Exception as e:
            logger.warning(f"模型预热失败: {e}")

    def is_enhancement_available(self) -> bool:
        """检查外观增强功能是否可用"""
        return self.models['gcnet'] is not None and self.models['drnet'] is not None

    @staticmethod
    def sort_ocr_results(ocr_result: List[Dict]) -> str:
        """
        将OCR结果按照从上到下、从左到右的顺序排序

        Args:
            ocr_result: OCR识别结果列表

        Returns:
            排序后的文本字符串
        """
        if not ocr_result:
            return ""

        # 计算每个文本框的中心点和高度
        for item in ocr_result:
            polygon = item['polygon']
            item['center_x'] = sum(polygon[0::2]) / 4
            item['center_y'] = sum(polygon[1::2]) / 4

        heights = [max(item['polygon'][1::2]) - min(item['polygon'][1::2]) for item in ocr_result]
        avg_height = sum(heights) / max(1, len(heights))
        line_threshold = avg_height / 2

        # 按y坐标排序
        sorted_by_y = sorted(ocr_result, key=lambda x: x['center_y'])

        # 行分组
        lines = []
        if sorted_by_y:
            current_line = [sorted_by_y[0]]
            base_y = sorted_by_y[0]['center_y']

            for item in sorted_by_y[1:]:
                if abs(item['center_y'] - base_y) > line_threshold:
                    current_line = sorted(current_line, key=lambda x: x['center_x'])
                    lines.append(current_line)
                    current_line = [item]
                    base_y = item['center_y']
                else:
                    current_line.append(item)

            if current_line:
                current_line = sorted(current_line, key=lambda x: x['center_x'])
                lines.append(current_line)

        # 拼接文本
        result_text = ""
        for line in lines:
            line_text = "".join(item['text'] for item in line)
            result_text += line_text + "\n"

        return result_text.strip()

    @staticmethod
    def convert_paddleocr_format(paddle_result: List) -> List[Dict]:
        """
        将PaddleOCR的结果格式转换为标准格式

        Args:
            paddle_result: PaddleOCR原始结果

        Returns:
            标准格式的OCR结果列表
        """
        ocr_result = []

        if not paddle_result or not paddle_result[0]:
            return ocr_result

        for item in paddle_result[0]:
            points = item[0]
            text_info = item[1]
            text = text_info[0]

            polygon = []
            for point in points:
                polygon.extend([float(point[0]), float(point[1])])

            ocr_result.append({
                'polygon': polygon,
                'text': text
            })

        return ocr_result

    def apply_appearance_enhancement(self, image: np.ndarray) -> np.ndarray:
        """应用外观增强处理"""
        if not self.is_enhancement_available():
            logger.info("外观增强模型未加载，跳过外观增强步骤")
            return image

        im_org, padding_h, padding_w = stride_integral(image)
        h, w = im_org.shape[:2]

        im_tensor = None
        im_org_tensor = None
        shadow = None
        model1_im = None
        pred = None

        try:
            with torch.no_grad():
                im_tensor = torch.from_numpy(im_org.transpose(2, 0, 1) / 255).unsqueeze(0).float().to(self.device)
                im_org_tensor = torch.from_numpy(im_org.transpose(2, 0, 1) / 255).unsqueeze(0).float().to(self.device)

                shadow = self.models['gcnet'](im_tensor)
                shadow = F.interpolate(shadow, (h, w))

                model1_im = torch.clamp(im_org_tensor / shadow, 0, 1)
                pred, _, _, _ = self.models['drnet'](torch.cat((im_org_tensor, model1_im), 1))

                pred_np = pred[0].permute(1, 2, 0).detach().cpu().numpy()
                pred_np = (pred_np * 255).astype(np.uint8)
                pred_np = pred_np[padding_h:, padding_w:]

        finally:
            for tensor in [im_tensor, im_org_tensor, shadow, model1_im, pred]:
                if tensor is not None:
                    del tensor
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect()

        return np.clip(pred_np, 0, 255).astype(np.uint8)

    def apply_dewarp_correction(self, image: np.ndarray) -> np.ndarray:
        """应用扭曲矫正处理"""
        img_ori = image / 255.
        h_, w_, c_ = img_ori.shape
        img_ori = cv2.resize(img_ori, (ModelConfig.DEWARP_SIZE, ModelConfig.DEWARP_SIZE))
        h, w, _ = img_ori.shape
        img = cv2.resize(img_ori, (ModelConfig.DEWARP_INPUT_SIZE, ModelConfig.DEWARP_INPUT_SIZE))
        img = img.transpose(2, 0, 1)

        img_tensor = None
        bm = None

        try:
            img_tensor = torch.from_numpy(img).float().unsqueeze(0).to(self.device)

            with torch.no_grad():
                bm = self.models['dewarp_model'](img_tensor)
                bm_np = bm.detach().cpu().numpy()[0]

            bm0 = cv2.blur(bm_np[0, :, :], (3, 3))
            bm1 = cv2.blur(bm_np[1, :, :], (3, 3))

            img_geo = cv2.remap(img_ori, bm0, bm1, cv2.INTER_LINEAR) * 255
            img_geo = cv2.resize(img_geo, (w_, h_))

        finally:
            for tensor in [img_tensor, bm]:
                if tensor is not None:
                    del tensor
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect()

        return np.clip(img_geo, 0, 255).astype(np.uint8)

    @staticmethod
    def draw_text_boxes(image: np.ndarray, ocr_result: List[Dict]) -> np.ndarray:
        """在图像上绘制OCR检测的文本框"""
        if not ocr_result:
            return image

        result_image = image.copy()

        for i, item in enumerate(ocr_result):
            polygon = item['polygon']
            color = ImageConfig.VISUALIZATION_COLORS[i % len(ImageConfig.VISUALIZATION_COLORS)]

            points = []
            for j in range(0, len(polygon), 2):
                points.append((int(polygon[j]), int(polygon[j + 1])))

            pts = np.array(points, np.int32).reshape((-1, 1, 2))
            cv2.polylines(result_image, [pts], True, color, 2)

        return result_image

    @staticmethod
    def create_text_visualization(ocr_result: List[Dict], width: int, height: int) -> np.ndarray:
        """创建文本可视化图像（简化版）"""
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)

        if not ocr_result:
            try:
                font = ImageFont.truetype(ImageConfig.FONT_PATH, 50)
            except:
                font = ImageFont.load_default()

            msg = "未识别到文本"
            text_bbox = draw.textbbox((0, 0), msg, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            draw.text((x, y), msg, fill='gray', font=font)
            return np.array(img)

        # 简化的文本绘制
        for i, item in enumerate(ocr_result):
            polygon = item['polygon']
            text = item['text']
            color = ImageConfig.VISUALIZATION_COLORS[i % len(ImageConfig.VISUALIZATION_COLORS)]

            if not text or not text.strip():
                continue

            x_coords = polygon[0::2]
            y_coords = polygon[1::2]
            min_x = max(0, int(min(x_coords)))
            max_x = min(width, int(max(x_coords)))
            min_y = max(0, int(min(y_coords)))
            max_y = min(height, int(max(y_coords)))

            region_width = max_x - min_x
            region_height = max_y - min_y

            if region_width <= 10 or region_height <= 10:
                continue

            # 简化字体大小计算
            font_size = min(50, region_height - 10)
            if font_size < 12:
                font_size = 12

            try:
                font = ImageFont.truetype(ImageConfig.FONT_PATH, font_size)
            except:
                font = ImageFont.load_default()

            # 绘制背景和文本
            overlay = Image.new('RGBA', (width, height), (255, 255, 255, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.rectangle([min_x, min_y, max_x, max_y],
                                   fill=(*color, 80), outline=color, width=1)

            img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
            draw = ImageDraw.Draw(img)

            # 绘制文本
            margin = 5
            draw.text((min_x + margin, min_y + margin), text, fill='black', font=font)

        return np.array(img)

    def process_image(
        self,
        image_path: str,
        use_enhancement: bool = False,
        use_dewarp: bool = False
    ) -> Dict[str, Any]:
        """
        处理单张图片并返回OCR结果

        Args:
            image_path: 图像路径
            use_enhancement: 是否使用外观增强
            use_dewarp: 是否使用扭曲矫正

        Returns:
            包含OCR结果的字典
        """
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"无法读取图像文件: {image_path}")

        logger.info(f"开始处理图像: {os.path.basename(image_path)}")
        logger.info(f"   - 外观增强: {'启用' if use_enhancement else '禁用'}")
        logger.info(f"   - 扭曲矫正: {'启用' if use_dewarp else '禁用'}")

        try:
            # 1. 可选：外观增强
            if use_enhancement:
                image = self.apply_appearance_enhancement(image)
            else:
                logger.info("跳过外观增强步骤")

            # 2. 可选：文本图像扭曲矫正
            if use_dewarp:
                image = self.apply_dewarp_correction(image)
            else:
                logger.info("跳过扭曲矫正步骤")

            processed_image = image.copy()

            # 3. ONNX OCR推理
            paddle_result = self.models['ocr_model'].ocr(image)

            # 4. 转换结果格式
            ocr_result = self.convert_paddleocr_format(paddle_result)

            # 5. 排序拼接
            sorted_text = self.sort_ocr_results(ocr_result) if ocr_result else ""

            # 6. 创建可视化
            logger.info("正在创建可视化图像...")
            image_with_boxes = self.draw_text_boxes(processed_image, ocr_result)
            img_height, img_width = image_with_boxes.shape[:2]
            text_image = self.create_text_visualization(ocr_result, img_width, img_height)
            visualization = np.hstack([image_with_boxes, text_image])

            _, img_encoded = cv2.imencode('.png', visualization)
            visualization_base64 = base64.b64encode(img_encoded).decode('utf-8')

            logger.info("可视化图像创建完成")

            processing_info = {
                'use_enhancement': use_enhancement,
                'use_dewarp': use_dewarp,
                'text_regions_count': len(ocr_result) if ocr_result else 0
            }

            return {
                'sorted_text': sorted_text,
                'ocr_result': ocr_result,
                'visualization': visualization_base64,
                'processing_info': processing_info
            }

        finally:
            if torch.cuda.is_available():
                with torch.cuda.device(self.device):
                    torch.cuda.empty_cache()
            gc.collect()


# 全局OCR服务实例（延迟初始化）
_ocr_service: Optional[OCRService] = None


def get_ocr_service() -> OCRService:
    """获取OCR服务单例"""
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService()
    return _ocr_service
