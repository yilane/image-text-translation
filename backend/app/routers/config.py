"""
配置管理API路由
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from typing import Dict, Any
from pydantic import BaseModel
from ..core.config_manager import config_manager
import tempfile
import os

router = APIRouter()

class ConfigUpdateRequest(BaseModel):
    """配置更新请求"""
    config: Dict[str, Any]

class PreferencesUpdateRequest(BaseModel):
    """用户偏好更新请求"""
    preferences: Dict[str, Any]

@router.get("/config/translation-providers")
async def get_translation_providers():
    """获取所有翻译服务提供商配置"""
    try:
        providers = {}
        for provider, config in config_manager.translation_configs.items():
            # 不返回API密钥
            provider_config = {
                "provider": config.provider,
                "api_url": config.api_url,
                "model": config.model,
                "max_tokens": config.max_tokens,
                "temperature": config.temperature,
                "timeout": config.timeout,
                "enabled": config.enabled,
                "has_api_key": bool(config.api_key)
            }
            providers[provider] = provider_config
        
        return {
            "success": True,
            "data": {
                "providers": providers,
                "enabled_providers": config_manager.get_enabled_providers()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取翻译服务配置失败: {str(e)}")

@router.put("/config/translation-providers/{provider}")
async def update_translation_provider(provider: str, request: ConfigUpdateRequest):
    """更新翻译服务提供商配置"""
    try:
        if provider not in config_manager.translation_configs:
            raise HTTPException(status_code=404, detail="翻译服务提供商不存在")
        
        success = config_manager.update_translation_config(provider, request.config)
        if not success:
            raise HTTPException(status_code=500, detail="更新配置失败")
        
        return {
            "success": True,
            "message": f"{provider} 配置更新成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新翻译服务配置失败: {str(e)}")

@router.get("/config/ocr")
async def get_ocr_config():
    """获取OCR配置"""
    try:
        ocr_config = config_manager.get_ocr_config()
        return {
            "success": True,
            "data": {
                "use_angle_cls": ocr_config.use_angle_cls,
                "use_space_char": ocr_config.use_space_char,
                "det_db_thresh": ocr_config.det_db_thresh,
                "det_db_box_thresh": ocr_config.det_db_box_thresh,
                "det_db_unclip_ratio": ocr_config.det_db_unclip_ratio,
                "rec_batch_num": ocr_config.rec_batch_num,
                "lang": ocr_config.lang
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取OCR配置失败: {str(e)}")

@router.put("/config/ocr")
async def update_ocr_config(request: ConfigUpdateRequest):
    """更新OCR配置"""
    try:
        success = config_manager.update_ocr_config(request.config)
        if not success:
            raise HTTPException(status_code=500, detail="更新OCR配置失败")
        
        return {
            "success": True,
            "message": "OCR配置更新成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新OCR配置失败: {str(e)}")

@router.get("/config/image-processing")
async def get_image_processing_config():
    """获取图像处理配置"""
    try:
        img_config = config_manager.get_image_processing_config()
        return {
            "success": True,
            "data": {
                "inpaint_radius": img_config.inpaint_radius,
                "font_size_ratio": img_config.font_size_ratio,
                "font_path": img_config.font_path,
                "auto_font_color": img_config.auto_font_color,
                "default_font_color": img_config.default_font_color,
                "padding_ratio": img_config.padding_ratio,
                "line_spacing": img_config.line_spacing
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图像处理配置失败: {str(e)}")

@router.put("/config/image-processing")
async def update_image_processing_config(request: ConfigUpdateRequest):
    """更新图像处理配置"""
    try:
        success = config_manager.update_image_processing_config(request.config)
        if not success:
            raise HTTPException(status_code=500, detail="更新图像处理配置失败")
        
        return {
            "success": True,
            "message": "图像处理配置更新成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新图像处理配置失败: {str(e)}")

@router.get("/config/user-preferences")
async def get_user_preferences():
    """获取用户偏好设置"""
    try:
        prefs = config_manager.get_user_preferences()
        return {
            "success": True,
            "data": {
                "default_source_language": prefs.default_source_language,
                "default_target_language": prefs.default_target_language,
                "default_provider": prefs.default_provider,
                "min_confidence": prefs.min_confidence,
                "save_original": prefs.save_original,
                "auto_detect_language": prefs.auto_detect_language,
                "theme": prefs.theme,
                "history_limit": prefs.history_limit
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户偏好设置失败: {str(e)}")

@router.put("/config/user-preferences")
async def update_user_preferences(request: PreferencesUpdateRequest):
    """更新用户偏好设置"""
    try:
        success = config_manager.update_user_preferences(request.preferences)
        if not success:
            raise HTTPException(status_code=500, detail="更新用户偏好设置失败")
        
        return {
            "success": True,
            "message": "用户偏好设置更新成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新用户偏好设置失败: {str(e)}")

@router.get("/config/validate")
async def validate_config():
    """验证配置有效性"""
    try:
        validation_result = config_manager.validate_config()
        return {
            "success": True,
            "data": validation_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"验证配置失败: {str(e)}")

@router.get("/config/export")
async def export_config():
    """导出配置文件"""
    try:
        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        temp_file.close()
        
        success = config_manager.export_config(temp_file.name)
        if not success:
            os.unlink(temp_file.name)
            raise HTTPException(status_code=500, detail="导出配置失败")
        
        return FileResponse(
            path=temp_file.name,
            filename="config_export.json",
            media_type="application/json"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出配置失败: {str(e)}")

@router.post("/config/import")
async def import_config(file: UploadFile = File(...)):
    """导入配置文件"""
    try:
        if not file.filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="只支持JSON格式的配置文件")
        
        # 保存上传的文件到临时位置
        temp_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.json', delete=False)
        content = await file.read()
        temp_file.write(content)
        temp_file.close()
        
        try:
            success = config_manager.import_config(temp_file.name)
            if not success:
                raise HTTPException(status_code=500, detail="导入配置失败")
            
            return {
                "success": True,
                "message": "配置导入成功"
            }
        finally:
            os.unlink(temp_file.name)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入配置失败: {str(e)}")

@router.get("/config/status")
async def get_config_status():
    """获取配置状态"""
    try:
        validation_result = config_manager.validate_config()
        enabled_providers = config_manager.get_enabled_providers()
        
        return {
            "success": True,
            "data": {
                "config_valid": validation_result["valid"],
                "enabled_providers_count": len(enabled_providers),
                "enabled_providers": enabled_providers,
                "errors": validation_result["errors"],
                "warnings": validation_result["warnings"],
                "config_file_exists": os.path.exists(config_manager.config_file)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置状态失败: {str(e)}") 