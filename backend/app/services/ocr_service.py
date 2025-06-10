import cv2
import numpy as np
from paddleocr import PaddleOCR
from typing import List, Tuple, Dict, Any
import logging
import os

logger = logging.getLogger(__name__)

class OCRService:
    def __init__(self):
        """初始化OCR服务"""
        self.ocr = None
        self._init_ocr()
    
    def _init_ocr(self):
        """初始化PaddleOCR"""
        try:
            # 支持中英文识别
            self.ocr = PaddleOCR(
                use_angle_cls=True,  # 使用角度分类器
                lang='ch',  # 支持中文
                use_gpu=False,  # 根据环境调整
                show_log=False
            )
            logger.info("PaddleOCR初始化成功")
        except Exception as e:
            logger.error(f"PaddleOCR初始化失败: {e}")
            raise e
    
    def detect_text(self, image_path: str) -> List[Dict[str, Any]]:
        """
        检测图片中的文字
        
        Args:
            image_path: 图片路径
            
        Returns:
            包含文字信息的列表，每个元素包含bbox、text、confidence
        """
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"图片文件不存在: {image_path}")
            
            # 使用PaddleOCR进行文字检测和识别
            result = self.ocr.ocr(image_path, cls=True)
            
            if not result or not result[0]:
                return []
            
            # 解析结果
            text_results = []
            for line in result[0]:
                if line:
                    bbox = line[0]  # 边界框坐标
                    text_info = line[1]  # (文字内容, 置信度)
                    
                    text_results.append({
                        'bbox': bbox,
                        'text': text_info[0],
                        'confidence': float(text_info[1])
                    })
            
            logger.info(f"检测到 {len(text_results)} 个文字区域")
            return text_results
            
        except Exception as e:
            logger.error(f"文字检测失败: {e}")
            raise e
    
    def detect_text_from_array(self, image_array: np.ndarray) -> List[Dict[str, Any]]:
        """
        从numpy数组检测文字
        
        Args:
            image_array: 图片数组
            
        Returns:
            包含文字信息的列表
        """
        try:
            result = self.ocr.ocr(image_array, cls=True)
            
            if not result or not result[0]:
                return []
            
            text_results = []
            for line in result[0]:
                if line:
                    bbox = line[0]
                    text_info = line[1]
                    
                    text_results.append({
                        'bbox': bbox,
                        'text': text_info[0],
                        'confidence': float(text_info[1])
                    })
            
            return text_results
            
        except Exception as e:
            logger.error(f"从数组检测文字失败: {e}")
            raise e
    
    def get_text_regions(self, image_path: str) -> Tuple[List[Dict], np.ndarray]:
        """
        获取文字区域信息和原始图片
        
        Args:
            image_path: 图片路径
            
        Returns:
            (文字区域列表, 图片数组)
        """
        try:
            # 读取图片
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"无法读取图片: {image_path}")
            
            # 检测文字
            text_results = self.detect_text_from_array(image)
            
            return text_results, image
            
        except Exception as e:
            logger.error(f"获取文字区域失败: {e}")
            raise e
    
    def filter_results_by_confidence(self, results: List[Dict], min_confidence: float = 0.5) -> List[Dict]:
        """
        根据置信度过滤结果
        
        Args:
            results: OCR结果列表
            min_confidence: 最小置信度阈值
            
        Returns:
            过滤后的结果列表
        """
        return [result for result in results if result['confidence'] >= min_confidence]

# 创建全局OCR服务实例
ocr_service = OCRService() 