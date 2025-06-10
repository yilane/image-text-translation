from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
import os
import logging

from ..services.ocr_service import ocr_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/ocr/detect")
async def detect_text(file: UploadFile = File(...)):
    """
    检测图片中的文字
    
    Args:
        file: 上传的图片文件
        
    Returns:
        文字检测结果
    """
    try:
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="只支持图片文件")
        
        # 保存上传的文件
        file_path = f"uploads/{file.filename}"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 进行文字检测
        text_results = ocr_service.detect_text(file_path)
        
        # 清理临时文件
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return JSONResponse(content={
            "success": True,
            "data": text_results,
            "message": f"检测到 {len(text_results)} 个文字区域"
        })
        
    except Exception as e:
        logger.error(f"OCR检测失败: {e}")
        raise HTTPException(status_code=500, detail=f"文字检测失败: {str(e)}")

@router.post("/ocr/detect-from-path")
async def detect_text_from_path(image_path: str):
    """
    从指定路径检测图片中的文字
    
    Args:
        image_path: 图片文件路径
        
    Returns:
        文字检测结果
    """
    try:
        if not os.path.exists(image_path):
            raise HTTPException(status_code=404, detail="图片文件不存在")
        
        # 进行文字检测
        text_results = ocr_service.detect_text(image_path)
        
        return JSONResponse(content={
            "success": True,
            "data": text_results,
            "message": f"检测到 {len(text_results)} 个文字区域"
        })
        
    except Exception as e:
        logger.error(f"OCR检测失败: {e}")
        raise HTTPException(status_code=500, detail=f"文字检测失败: {str(e)}")

@router.post("/ocr/filter")
async def filter_ocr_results(results: List[Dict[str, Any]], min_confidence: float = 0.5):
    """
    根据置信度过滤OCR结果
    
    Args:
        results: OCR结果列表
        min_confidence: 最小置信度阈值
        
    Returns:
        过滤后的结果
    """
    try:
        filtered_results = ocr_service.filter_results_by_confidence(results, min_confidence)
        
        return JSONResponse(content={
            "success": True,
            "data": filtered_results,
            "message": f"过滤后剩余 {len(filtered_results)} 个文字区域"
        })
        
    except Exception as e:
        logger.error(f"结果过滤失败: {e}")
        raise HTTPException(status_code=500, detail=f"结果过滤失败: {str(e)}")

# OCR相关路由将在后续任务中实现 