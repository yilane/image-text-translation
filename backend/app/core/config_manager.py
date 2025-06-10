"""
配置管理系统
支持翻译服务配置、用户偏好设置等
"""
import json
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class TranslationConfig:
    """翻译配置"""
    provider: str = "openai"
    api_key: str = ""
    api_url: str = ""
    model: str = ""
    max_tokens: int = 4000
    temperature: float = 0.3
    timeout: int = 30
    enabled: bool = True

@dataclass
class OCRConfig:
    """OCR配置"""
    use_angle_cls: bool = True
    use_space_char: bool = True
    det_db_thresh: float = 0.3
    det_db_box_thresh: float = 0.6
    det_db_unclip_ratio: float = 1.5
    rec_batch_num: int = 6
    lang: str = "ch"

@dataclass
class ImageProcessingConfig:
    """图像处理配置"""
    inpaint_radius: int = 3
    font_size_ratio: float = 0.8
    font_path: str = ""
    auto_font_color: bool = True
    default_font_color: tuple = (0, 0, 0)
    padding_ratio: float = 0.1
    line_spacing: float = 1.2

@dataclass
class UserPreferences:
    """用户偏好设置"""
    default_source_language: str = "auto"
    default_target_language: str = "en"
    default_provider: str = "openai"
    min_confidence: float = 0.5
    save_original: bool = True
    auto_detect_language: bool = True
    theme: str = "light"
    history_limit: int = 100

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "app_config.json")
        
        # 确保配置目录存在
        os.makedirs(config_dir, exist_ok=True)
        
        # 初始化默认配置
        self._init_default_configs()
        
        # 加载配置
        self.load_config()
    
    def _init_default_configs(self):
        """初始化默认配置"""
        self.translation_configs = {
            "openai": TranslationConfig(
                provider="openai",
                api_key=os.getenv("OPENAI_API_KEY", ""),
                api_url=os.getenv("OPENAI_API_URL", "https://api.openai.com/v1"),
                model="gpt-3.5-turbo",
                max_tokens=4000,
                temperature=0.3,
                timeout=30,
                enabled=True
            ),
            "baidu": TranslationConfig(
                provider="baidu",
                api_key=os.getenv("BAIDU_API_KEY", ""),
                api_url="https://fanyi-api.baidu.com/api/trans/vip/translate",
                model="",
                max_tokens=2000,
                temperature=0.0,
                timeout=30,
                enabled=True
            ),
            "google": TranslationConfig(
                provider="google",
                api_key=os.getenv("GOOGLE_API_KEY", ""),
                api_url="https://translation.googleapis.com/language/translate/v2",
                model="",
                max_tokens=2000,
                temperature=0.0,
                timeout=30,
                enabled=True
            )
        }
        
        self.ocr_config = OCRConfig()
        self.image_processing_config = ImageProcessingConfig()
        self.user_preferences = UserPreferences()
    
    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 加载翻译配置
                if "translation_configs" in config_data:
                    for provider, config in config_data["translation_configs"].items():
                        if provider in self.translation_configs:
                            self.translation_configs[provider] = TranslationConfig(**config)
                
                # 加载OCR配置
                if "ocr_config" in config_data:
                    self.ocr_config = OCRConfig(**config_data["ocr_config"])
                
                # 加载图像处理配置
                if "image_processing_config" in config_data:
                    self.image_processing_config = ImageProcessingConfig(**config_data["image_processing_config"])
                
                # 加载用户偏好
                if "user_preferences" in config_data:
                    self.user_preferences = UserPreferences(**config_data["user_preferences"])
                
                logger.info("配置文件加载成功")
            else:
                logger.info("配置文件不存在，使用默认配置")
                self.save_config()
                
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            logger.info("使用默认配置")
    
    def save_config(self):
        """保存配置到文件"""
        try:
            config_data = {
                "translation_configs": {
                    provider: asdict(config) 
                    for provider, config in self.translation_configs.items()
                },
                "ocr_config": asdict(self.ocr_config),
                "image_processing_config": asdict(self.image_processing_config),
                "user_preferences": asdict(self.user_preferences),
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            logger.info("配置文件保存成功")
            return True
            
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            return False
    
    def get_translation_config(self, provider: str) -> Optional[TranslationConfig]:
        """获取翻译配置"""
        return self.translation_configs.get(provider)
    
    def update_translation_config(self, provider: str, config: Dict[str, Any]) -> bool:
        """更新翻译配置"""
        try:
            if provider in self.translation_configs:
                current_config = asdict(self.translation_configs[provider])
                current_config.update(config)
                self.translation_configs[provider] = TranslationConfig(**current_config)
                return self.save_config()
            return False
        except Exception as e:
            logger.error(f"更新翻译配置失败: {e}")
            return False
    
    def get_ocr_config(self) -> OCRConfig:
        """获取OCR配置"""
        return self.ocr_config
    
    def update_ocr_config(self, config: Dict[str, Any]) -> bool:
        """更新OCR配置"""
        try:
            current_config = asdict(self.ocr_config)
            current_config.update(config)
            self.ocr_config = OCRConfig(**current_config)
            return self.save_config()
        except Exception as e:
            logger.error(f"更新OCR配置失败: {e}")
            return False
    
    def get_image_processing_config(self) -> ImageProcessingConfig:
        """获取图像处理配置"""
        return self.image_processing_config
    
    def update_image_processing_config(self, config: Dict[str, Any]) -> bool:
        """更新图像处理配置"""
        try:
            current_config = asdict(self.image_processing_config)
            current_config.update(config)
            self.image_processing_config = ImageProcessingConfig(**current_config)
            return self.save_config()
        except Exception as e:
            logger.error(f"更新图像处理配置失败: {e}")
            return False
    
    def get_user_preferences(self) -> UserPreferences:
        """获取用户偏好"""
        return self.user_preferences
    
    def update_user_preferences(self, preferences: Dict[str, Any]) -> bool:
        """更新用户偏好"""
        try:
            current_prefs = asdict(self.user_preferences)
            current_prefs.update(preferences)
            self.user_preferences = UserPreferences(**current_prefs)
            return self.save_config()
        except Exception as e:
            logger.error(f"更新用户偏好失败: {e}")
            return False
    
    def get_enabled_providers(self) -> List[str]:
        """获取启用的翻译服务提供商"""
        return [
            provider for provider, config in self.translation_configs.items()
            if config.enabled and config.api_key
        ]
    
    def validate_config(self) -> Dict[str, Any]:
        """验证配置有效性"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # 检查翻译服务配置
        enabled_providers = self.get_enabled_providers()
        if not enabled_providers:
            validation_result["valid"] = False
            validation_result["errors"].append("没有可用的翻译服务提供商")
        
        for provider, config in self.translation_configs.items():
            if config.enabled and not config.api_key:
                validation_result["warnings"].append(f"{provider} 缺少API密钥")
        
        # 检查OCR配置
        if self.ocr_config.det_db_thresh < 0 or self.ocr_config.det_db_thresh > 1:
            validation_result["warnings"].append("OCR检测阈值应在0-1之间")
        
        # 检查图像处理配置
        if self.image_processing_config.font_size_ratio <= 0:
            validation_result["warnings"].append("字体大小比例应大于0")
        
        return validation_result
    
    def export_config(self, export_path: str) -> bool:
        """导出配置"""
        try:
            config_data = {
                "translation_configs": {
                    provider: {k: v for k, v in asdict(config).items() if k != "api_key"}
                    for provider, config in self.translation_configs.items()
                },
                "ocr_config": asdict(self.ocr_config),
                "image_processing_config": asdict(self.image_processing_config),
                "user_preferences": asdict(self.user_preferences),
                "export_time": datetime.now().isoformat()
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"配置导出成功: {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
            return False
    
    def import_config(self, import_path: str) -> bool:
        """导入配置"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 导入配置（不包括API密钥）
            if "ocr_config" in config_data:
                self.ocr_config = OCRConfig(**config_data["ocr_config"])
            
            if "image_processing_config" in config_data:
                self.image_processing_config = ImageProcessingConfig(**config_data["image_processing_config"])
            
            if "user_preferences" in config_data:
                self.user_preferences = UserPreferences(**config_data["user_preferences"])
            
            # 保存配置
            return self.save_config()
            
        except Exception as e:
            logger.error(f"导入配置失败: {e}")
            return False

# 全局配置管理器实例
config_manager = ConfigManager() 