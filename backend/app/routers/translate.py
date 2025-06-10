from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import logging

from ..services.translation_service import translation_service, TranslationProvider

router = APIRouter()
logger = logging.getLogger(__name__)

class TranslateRequest(BaseModel):
    text: str
    target_language: str = "en"
    source_language: str = "auto"
    provider: str = "openai"

class BatchTranslateRequest(BaseModel):
    texts: List[str]
    target_language: str = "en"
    source_language: str = "auto"
    provider: str = "openai"

@router.post("/translate/single")
async def translate_single_text(request: TranslateRequest):
    """
    翻译单个文本
    
    Args:
        request: 翻译请求参数
        
    Returns:
        翻译结果
    """
    try:
        # 验证翻译提供商
        try:
            provider = TranslationProvider(request.provider)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"不支持的翻译提供商: {request.provider}")
        
        # 执行翻译
        translated_text = await translation_service.translate_text(
            text=request.text,
            target_language=request.target_language,
            source_language=request.source_language,
            provider=provider
        )
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "original_text": request.text,
                "translated_text": translated_text,
                "source_language": request.source_language,
                "target_language": request.target_language,
                "provider": request.provider
            },
            "message": "翻译成功"
        })
        
    except Exception as e:
        logger.error(f"翻译失败: {e}")
        raise HTTPException(status_code=500, detail=f"翻译失败: {str(e)}")

@router.post("/translate/batch")
async def translate_batch_texts(request: BatchTranslateRequest):
    """
    批量翻译文本
    
    Args:
        request: 批量翻译请求参数
        
    Returns:
        批量翻译结果
    """
    try:
        # 验证翻译提供商
        try:
            provider = TranslationProvider(request.provider)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"不支持的翻译提供商: {request.provider}")
        
        # 执行批量翻译
        translated_texts = await translation_service.batch_translate(
            texts=request.texts,
            target_language=request.target_language,
            source_language=request.source_language,
            provider=provider
        )
        
        # 构建结果
        results = []
        for original, translated in zip(request.texts, translated_texts):
            results.append({
                "original_text": original,
                "translated_text": translated
            })
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "results": results,
                "source_language": request.source_language,
                "target_language": request.target_language,
                "provider": request.provider,
                "total_count": len(results)
            },
            "message": f"批量翻译完成，共处理 {len(results)} 条文本"
        })
        
    except Exception as e:
        logger.error(f"批量翻译失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量翻译失败: {str(e)}")

@router.post("/translate/detect-language")
async def detect_language(text: str):
    """
    检测文本语言
    
    Args:
        text: 需要检测的文本
        
    Returns:
        语言检测结果
    """
    try:
        detected_language = translation_service.detect_language(text)
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "text": text,
                "detected_language": detected_language
            },
            "message": "语言检测完成"
        })
        
    except Exception as e:
        logger.error(f"语言检测失败: {e}")
        raise HTTPException(status_code=500, detail=f"语言检测失败: {str(e)}")

@router.get("/translate/providers")
async def get_translation_providers():
    """
    获取支持的翻译提供商列表
    
    Returns:
        翻译提供商列表
    """
    try:
        providers = [provider.value for provider in TranslationProvider]
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "providers": providers,
                "default": "openai"
            },
            "message": "获取翻译提供商列表成功"
        })
        
    except Exception as e:
        logger.error(f"获取翻译提供商失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取翻译提供商失败: {str(e)}")

@router.get("/translate/supported-languages")
async def get_supported_languages():
    """
    获取支持的语言列表
    
    Returns:
        支持的语言列表
    """
    try:
        languages = {
            "auto": "自动检测",
            "zh": "中文",
            "en": "英文",
            "ja": "日文",
            "ko": "韩文",
            "fr": "法文",
            "de": "德文",
            "es": "西班牙文",
            "ru": "俄文"
        }
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "languages": languages,
                "default_source": "auto",
                "default_target": "en"
            },
            "message": "获取支持语言列表成功"
        })
        
    except Exception as e:
        logger.error(f"获取支持语言失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取支持语言失败: {str(e)}") 