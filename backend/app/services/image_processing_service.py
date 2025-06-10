import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import logging
from typing import List, Dict, Tuple, Optional
from skimage import restoration
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

logger = logging.getLogger(__name__)

class ImageProcessingService:
    def __init__(self):
        """初始化图像处理服务"""
        self.font_cache = {}
        self._load_fonts()
    
    def _load_fonts(self):
        """加载系统字体"""
        try:
            # 常见的中文字体路径
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 
                "/System/Library/Fonts/Arial.ttf",
                "/Windows/Fonts/arial.ttf",
                "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
            ]
            
            # 尝试加载字体
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        self.font_cache['default'] = font_path
                        logger.info(f"成功加载字体: {font_path}")
                        break
                    except Exception as e:
                        logger.warning(f"加载字体失败 {font_path}: {e}")
            
            # 如果没有找到系统字体，使用默认字体
            if 'default' not in self.font_cache:
                logger.warning("未找到系统字体，将使用PIL默认字体")
                
        except Exception as e:
            logger.error(f"字体加载失败: {e}")
    
    def remove_text_from_image(self, image: np.ndarray, text_regions: List[Dict]) -> np.ndarray:
        """
        从图片中移除文字区域
        
        Args:
            image: 原始图片数组
            text_regions: 文字区域列表，每个元素包含bbox
            
        Returns:
            移除文字后的图片数组
        """
        try:
            # 创建掩码
            mask = np.zeros(image.shape[:2], dtype=np.uint8)
            
            for region in text_regions:
                bbox = region['bbox']
                # 将bbox转换为整数坐标
                points = np.array(bbox, dtype=np.int32)
                
                # 在掩码上填充文字区域
                cv2.fillPoly(mask, [points], 255)
            
            # 使用图像修复算法移除文字
            result = cv2.inpaint(image, mask, 3, cv2.INPAINT_TELEA)
            
            return result
            
        except Exception as e:
            logger.error(f"移除文字失败: {e}")
            return image
    
    def calculate_text_size(self, text: str, font_path: str = None, font_size: int = 20) -> Tuple[int, int]:
        """
        计算文字渲染尺寸
        
        Args:
            text: 要渲染的文字
            font_path: 字体路径
            font_size: 字体大小
            
        Returns:
            (宽度, 高度)
        """
        try:
            if font_path and os.path.exists(font_path):
                font = ImageFont.truetype(font_path, font_size)
            elif 'default' in self.font_cache:
                font = ImageFont.truetype(self.font_cache['default'], font_size)
            else:
                font = ImageFont.load_default()
            
            # 创建临时图片来测量文字大小
            temp_img = Image.new('RGB', (1, 1))
            draw = ImageDraw.Draw(temp_img)
            bbox = draw.textbbox((0, 0), text, font=font)
            
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            
            return width, height
            
        except Exception as e:
            logger.error(f"计算文字大小失败: {e}")
            return len(text) * font_size // 2, font_size
    
    def fit_text_to_region(self, text: str, region_width: int, region_height: int, 
                          font_path: str = None, max_font_size: int = 50) -> Tuple[int, str]:
        """
        调整文字大小以适应区域
        
        Args:
            text: 要渲染的文字
            region_width: 区域宽度
            region_height: 区域高度
            font_path: 字体路径
            max_font_size: 最大字体大小
            
        Returns:
            (最适合的字体大小, 调整后的文字)
        """
        try:
            # 从较大的字体开始尝试
            for font_size in range(max_font_size, 8, -2):
                text_width, text_height = self.calculate_text_size(text, font_path, font_size)
                
                # 如果文字能够适应区域
                if text_width <= region_width and text_height <= region_height:
                    return font_size, text
            
            # 如果文字太长，尝试换行
            words = text.split()
            if len(words) > 1:
                # 尝试分成两行
                mid = len(words) // 2
                line1 = ' '.join(words[:mid])
                line2 = ' '.join(words[mid:])
                wrapped_text = f"{line1}\n{line2}"
                
                for font_size in range(max_font_size, 8, -2):
                    text_width, text_height = self.calculate_text_size(wrapped_text, font_path, font_size)
                    if text_width <= region_width and text_height <= region_height:
                        return font_size, wrapped_text
            
            # 如果还是不行，使用最小字体
            return 10, text
            
        except Exception as e:
            logger.error(f"调整文字大小失败: {e}")
            return 12, text
    
    def render_text_on_image(self, image: np.ndarray, text_regions: List[Dict], 
                           translated_texts: List[str], 
                           target_language: str = "en") -> np.ndarray:
        """
        在图片上渲染翻译后的文字
        
        Args:
            image: 已移除原文字的图片数组
            text_regions: 原文字区域列表
            translated_texts: 翻译后的文字列表
            target_language: 目标语言
            
        Returns:
            渲染文字后的图片数组
        """
        try:
            # 转换为PIL Image
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(pil_image)
            
            # 选择合适的字体
            font_path = self._get_font_for_language(target_language)
            
            for i, (region, translated_text) in enumerate(zip(text_regions, translated_texts)):
                if i >= len(translated_texts):
                    break
                
                bbox = region['bbox']
                
                # 计算文字区域的中心和尺寸
                x_coords = [point[0] for point in bbox]
                y_coords = [point[1] for point in bbox]
                
                min_x, max_x = min(x_coords), max(x_coords)
                min_y, max_y = min(y_coords), max(y_coords)
                
                region_width = max_x - min_x
                region_height = max_y - min_y
                
                # 调整文字大小以适应区域
                font_size, fitted_text = self.fit_text_to_region(
                    translated_text, region_width, region_height, font_path
                )
                
                # 加载字体
                try:
                    if font_path and os.path.exists(font_path):
                        font = ImageFont.truetype(font_path, font_size)
                    elif 'default' in self.font_cache:
                        font = ImageFont.truetype(self.font_cache['default'], font_size)
                    else:
                        font = ImageFont.load_default()
                except:
                    font = ImageFont.load_default()
                
                # 计算文字位置（居中）
                text_bbox = draw.textbbox((0, 0), fitted_text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                
                x = min_x + (region_width - text_width) // 2
                y = min_y + (region_height - text_height) // 2
                
                # 选择文字颜色（与背景形成对比）
                text_color = self._get_contrasting_color(image, min_x, min_y, max_x, max_y)
                
                # 绘制文字背景（可选）
                if self._needs_background(image, min_x, min_y, max_x, max_y):
                    bg_color = (255, 255, 255, 128)  # 半透明白色背景
                    draw.rectangle([x-2, y-2, x+text_width+2, y+text_height+2], 
                                 fill=bg_color)
                
                # 绘制文字
                draw.text((x, y), fitted_text, font=font, fill=text_color)
            
            # 转换回OpenCV格式
            result = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            return result
            
        except Exception as e:
            logger.error(f"渲染文字失败: {e}")
            return image
    
    def _get_font_for_language(self, language: str) -> Optional[str]:
        """根据语言选择合适的字体"""
        if language in ['zh', 'ja', 'ko']:
            # 亚洲语言需要特殊字体
            asian_fonts = [
                "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                "/System/Library/Fonts/Arial Unicode MS.ttf"
            ]
            for font_path in asian_fonts:
                if os.path.exists(font_path):
                    return font_path
        
        return self.font_cache.get('default')
    
    def _get_contrasting_color(self, image: np.ndarray, x1: int, y1: int, x2: int, y2: int) -> Tuple[int, int, int]:
        """获取与背景形成对比的文字颜色"""
        try:
            # 计算区域的平均亮度
            region = image[y1:y2, x1:x2]
            if region.size > 0:
                avg_brightness = np.mean(region)
                # 如果背景较暗，使用白色文字；如果背景较亮，使用黑色文字
                if avg_brightness < 128:
                    return (255, 255, 255)  # 白色
                else:
                    return (0, 0, 0)  # 黑色
            else:
                return (0, 0, 0)  # 默认黑色
        except:
            return (0, 0, 0)
    
    def _needs_background(self, image: np.ndarray, x1: int, y1: int, x2: int, y2: int) -> bool:
        """判断是否需要为文字添加背景"""
        try:
            # 计算区域的颜色变化程度
            region = image[y1:y2, x1:x2]
            if region.size > 0:
                std_dev = np.std(region)
                # 如果颜色变化较大，需要背景来提高可读性
                return std_dev > 30
            return False
        except:
            return False
    
    def process_image(self, image_path: str, text_regions: List[Dict], 
                     translated_texts: List[str], target_language: str = "en") -> np.ndarray:
        """
        完整的图像处理流程：移除原文字并渲染翻译文字
        
        Args:
            image_path: 原始图片路径
            text_regions: 文字区域列表
            translated_texts: 翻译后的文字列表
            target_language: 目标语言
            
        Returns:
            处理后的图片数组
        """
        try:
            # 读取图片
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"无法读取图片: {image_path}")
            
            # 移除原文字
            image_without_text = self.remove_text_from_image(image, text_regions)
            
            # 渲染翻译文字
            final_image = self.render_text_on_image(
                image_without_text, text_regions, translated_texts, target_language
            )
            
            return final_image
            
        except Exception as e:
            logger.error(f"图像处理失败: {e}")
            # 返回原图
            return cv2.imread(image_path) if os.path.exists(image_path) else None

# 创建全局图像处理服务实例
image_processing_service = ImageProcessingService() 