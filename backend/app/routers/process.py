from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import uuid
import cv2
import logging

from ..services.ocr_service import ocr_service
from ..services.translation_service import translation_service, TranslationProvider
from ..services.image_processing_service import image_processing_service

router = APIRouter()
logger = logging.getLogger(__name__)

class ProcessImageRequest(BaseModel):
    image_path: str
    target_language: str = "en"
    source_language: str = "auto"
    provider: str = "openai"
    min_confidence: float = 0.5

class ProcessImageWithRegionsRequest(BaseModel):
    image_path: str
    text_regions: List[Dict[str, Any]]
    translated_texts: List[str]
    target_language: str = "en"

@router.post("/process/translate-image")
async def process_translate_image(file: UploadFile = File(...), 
                                target_language: str = "en",
                                source_language: str = "auto",
                                provider: str = "openai",
                                min_confidence: float = 0.5):
    """
    完整的图片翻译处理流程
    
    Args:
        file: 上传的图片文件
        target_language: 目标语言
        source_language: 源语言
        provider: 翻译提供商
        min_confidence: 最小置信度
        
    Returns:
        处理后的图片和相关信息
    """
    try:
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="只支持图片文件")
        
        # 生成唯一文件名
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        input_path = f"uploads/{file_id}_input{file_extension}"
        output_path = f"results/{file_id}_output{file_extension}"
        
        # 保存上传的文件
        with open(input_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 步骤1：OCR文字检测
        logger.info("开始OCR文字检测...")
        text_regions = ocr_service.detect_text(input_path)
        
        if not text_regions:
            raise HTTPException(status_code=400, detail="未检测到文字内容")
        
        # 步骤2：过滤低置信度结果
        text_regions = ocr_service.filter_results_by_confidence(text_regions, min_confidence)
        
        if not text_regions:
            raise HTTPException(status_code=400, detail="过滤后无有效文字内容")
        
        # 步骤3：提取文字内容
        texts_to_translate = [region['text'] for region in text_regions]
        
        # 步骤4：翻译文字
        logger.info("开始翻译文字...")
        try:
            provider_enum = TranslationProvider(provider)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"不支持的翻译提供商: {provider}")
        
        translated_texts = await translation_service.batch_translate(
            texts=texts_to_translate,
            target_language=target_language,
            source_language=source_language,
            provider=provider_enum
        )
        
        # 步骤5：图像处理（移除原文字并渲染翻译文字）
        logger.info("开始图像处理...")
        processed_image = image_processing_service.process_image(
            image_path=input_path,
            text_regions=text_regions,
            translated_texts=translated_texts,
            target_language=target_language
        )
        
        if processed_image is None:
            raise HTTPException(status_code=500, detail="图像处理失败")
        
        # 保存处理后的图片
        cv2.imwrite(output_path, processed_image)
        
        # 构建结果数据
        translation_results = []
        for i, (region, original, translated) in enumerate(zip(text_regions, texts_to_translate, translated_texts)):
            translation_results.append({
                "id": i,
                "bbox": region['bbox'],
                "confidence": region['confidence'],
                "original_text": original,
                "translated_text": translated
            })
        
        # 清理输入文件
        if os.path.exists(input_path):
            os.remove(input_path)
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "output_image_path": output_path,
                "translation_results": translation_results,
                "processing_info": {
                    "total_regions": len(text_regions),
                    "source_language": source_language,
                    "target_language": target_language,
                    "provider": provider,
                    "min_confidence": min_confidence
                }
            },
            "message": "图片翻译处理完成"
        })
        
    except Exception as e:
        logger.error(f"图片翻译处理失败: {e}")
        # 清理文件
        for path in [input_path, output_path]:
            if 'path' in locals() and os.path.exists(path):
                os.remove(path)
        raise HTTPException(status_code=500, detail=f"图片翻译处理失败: {str(e)}")

@router.post("/process/from-path")
async def process_image_from_path(request: ProcessImageRequest):
    """
    从指定路径处理图片翻译
    
    Args:
        request: 处理请求参数
        
    Returns:
        处理结果
    """
    try:
        if not os.path.exists(request.image_path):
            raise HTTPException(status_code=404, detail="图片文件不存在")
        
        # 生成输出路径
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(request.image_path)[1]
        output_path = f"results/{file_id}_output{file_extension}"
        
        # OCR检测
        text_regions = ocr_service.detect_text(request.image_path)
        text_regions = ocr_service.filter_results_by_confidence(text_regions, request.min_confidence)
        
        if not text_regions:
            raise HTTPException(status_code=400, detail="未检测到有效文字内容")
        
        # 翻译
        texts_to_translate = [region['text'] for region in text_regions]
        provider_enum = TranslationProvider(request.provider)
        
        translated_texts = await translation_service.batch_translate(
            texts=texts_to_translate,
            target_language=request.target_language,
            source_language=request.source_language,
            provider=provider_enum
        )
        
        # 图像处理
        processed_image = image_processing_service.process_image(
            image_path=request.image_path,
            text_regions=text_regions,
            translated_texts=translated_texts,
            target_language=request.target_language
        )
        
        # 保存结果
        cv2.imwrite(output_path, processed_image)
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "output_image_path": output_path,
                "total_regions": len(text_regions)
            },
            "message": "图片处理完成"
        })
        
    except Exception as e:
        logger.error(f"图片处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"图片处理失败: {str(e)}")

@router.post("/process/custom-regions")
async def process_image_with_custom_regions(request: ProcessImageWithRegionsRequest):
    """
    使用自定义区域和翻译文字处理图片
    
    Args:
        request: 自定义处理请求
        
    Returns:
        处理结果
    """
    try:
        if not os.path.exists(request.image_path):
            raise HTTPException(status_code=404, detail="图片文件不存在")
        
        # 生成输出路径
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(request.image_path)[1]
        output_path = f"results/{file_id}_custom{file_extension}"
        
        # 图像处理
        processed_image = image_processing_service.process_image(
            image_path=request.image_path,
            text_regions=request.text_regions,
            translated_texts=request.translated_texts,
            target_language=request.target_language
        )
        
        # 保存结果
        cv2.imwrite(output_path, processed_image)
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "output_image_path": output_path,
                "processed_regions": len(request.text_regions)
            },
            "message": "自定义区域处理完成"
        })
        
    except Exception as e:
        logger.error(f"自定义区域处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"自定义区域处理失败: {str(e)}")

@router.get("/process/result/{file_id}")
async def get_processed_image(file_id: str):
    """
    获取处理后的图片文件
    
    Args:
        file_id: 文件ID
        
    Returns:
        图片文件
    """
    try:
        # 查找文件
        possible_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
        file_path = None
        
        for ext in possible_extensions:
            path = f"results/{file_id}_output{ext}"
            if os.path.exists(path):
                file_path = path
                break
        
        if not file_path:
            raise HTTPException(status_code=404, detail="处理结果文件不存在")
        
        return FileResponse(
            path=file_path,
            media_type="image/jpeg",
            filename=f"{file_id}_translated.jpg"
        )
        
    except Exception as e:
        logger.error(f"获取处理结果失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取处理结果失败: {str(e)}")

@router.delete("/process/cleanup/{file_id}")
async def cleanup_processed_files(file_id: str):
    """
    清理处理过程中的临时文件
    
    Args:
        file_id: 文件ID
        
    Returns:
        清理结果
    """
    try:
        deleted_files = []
        possible_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
        
        # 清理所有相关文件
        for ext in possible_extensions:
            for prefix in ['input', 'output', 'custom']:
                file_path = f"results/{file_id}_{prefix}{ext}"
                if os.path.exists(file_path):
                    os.remove(file_path)
                    deleted_files.append(file_path)
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "deleted_files": deleted_files,
                "count": len(deleted_files)
            },
            "message": "文件清理完成"
        })
        
    except Exception as e:
        logger.error(f"文件清理失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件清理失败: {str(e)}") 