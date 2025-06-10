from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import os
import uuid
import shutil
from PIL import Image
import aiofiles

from app.database.database import get_db
from app.models.models import TranslationHistory
from app.utils.file_utils import validate_image_file, get_image_info

router = APIRouter()

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
UPLOAD_DIR = "uploads"

@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    上传图片文件
    """
    try:
        # 验证文件格式
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式。支持的格式: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # 验证文件大小
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"文件大小超过限制。最大支持 {MAX_FILE_SIZE // 1024 // 1024}MB"
            )
        
        # 生成唯一文件名
        file_id = str(uuid.uuid4())
        filename = f"{file_id}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        # 确保上传目录存在
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        # 保存文件
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)
        
        # 验证图像文件并获取信息
        try:
            image_info = get_image_info(file_path)
        except Exception as e:
            # 删除无效文件
            os.remove(file_path)
            raise HTTPException(
                status_code=400,
                detail=f"无效的图像文件: {str(e)}"
            )
        
        # 创建翻译历史记录
        history = TranslationHistory(
            original_image_path=file_path,
            status="uploaded"
        )
        db.add(history)
        db.commit()
        db.refresh(history)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "文件上传成功",
                "data": {
                    "file_id": file_id,
                    "history_id": history.id,
                    "file_path": file_path,
                    "file_size": len(file_content),
                    "image_info": image_info
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"文件上传失败: {str(e)}"
        )

@router.get("/upload/history")
async def get_upload_history(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    获取上传历史记录
    """
    try:
        histories = db.query(TranslationHistory)\
                     .order_by(TranslationHistory.created_at.desc())\
                     .offset(skip)\
                     .limit(limit)\
                     .all()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "histories": [
                        {
                            "id": h.id,
                            "original_image_path": h.original_image_path,
                            "translated_image_path": h.translated_image_path,
                            "source_language": h.source_language,
                            "target_language": h.target_language,
                            "status": h.status,
                            "processing_time": h.processing_time,
                            "created_at": h.created_at.isoformat()
                        }
                        for h in histories
                    ]
                }
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取历史记录失败: {str(e)}"
        ) 