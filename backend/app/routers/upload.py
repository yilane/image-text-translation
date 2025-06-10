from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import os
import uuid
import shutil
from PIL import Image
import aiofiles
from datetime import datetime

from app.database.database import get_db
from app.utils.file_utils import validate_image_file, get_image_info

router = APIRouter()

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
UPLOAD_BASE_DIR = "uploads"

def get_date_path():
    """
    生成基于当前日期的子目录路径
    格式: YYYY/MM/DD
    """
    now = datetime.now()
    return now.strftime("%Y/%m/%d")

def create_upload_path(filename: str) -> tuple[str, str]:
    """
    创建按日期分类的上传路径
    
    Returns:
        tuple: (相对路径, 绝对路径)
    """
    date_path = get_date_path()
    relative_path = os.path.join(UPLOAD_BASE_DIR, date_path, filename)
    absolute_dir = os.path.join(UPLOAD_BASE_DIR, date_path)
    
    # 确保目录存在
    os.makedirs(absolute_dir, exist_ok=True)
    
    return relative_path, absolute_dir

@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    上传图片文件，按日期目录分类保存
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
        
        # 创建按日期分类的存储路径
        file_path, upload_dir = create_upload_path(filename)
        full_file_path = file_path
        
        # 保存文件
        async with aiofiles.open(full_file_path, 'wb') as f:
            await f.write(file_content)
        
        # 验证图像文件并获取信息
        try:
            image_info = get_image_info(full_file_path)
        except Exception as e:
            # 删除无效文件
            os.remove(full_file_path)
            raise HTTPException(
                status_code=400,
                detail=f"无效的图像文件: {str(e)}"
            )
        
        # 创建上传文件记录
        from ..database.models import UploadedFile
        
        uploaded_file = UploadedFile(
            file_id=file_id,
            original_filename=file.filename,
            file_path=file_path,  # 存储相对路径
            file_size=len(file_content),
            mime_type=file.content_type or f"image/{file_ext[1:]}",
            width=image_info.get("width"),
            height=image_info.get("height"),
            format=image_info.get("format"),
            mode=image_info.get("mode")
        )
        db.add(uploaded_file)
        db.commit()
        db.refresh(uploaded_file)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "文件上传成功",
                "data": {
                    "file_id": file_id,
                    "upload_id": uploaded_file.id,
                    "file_path": file_path,
                    "file_size": len(file_content),
                    "image_info": image_info,
                    "date_path": get_date_path()  # 返回日期路径信息
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
    获取上传文件历史记录
    """
    try:
        from ..database.models import UploadedFile
        
        files = db.query(UploadedFile)\
                  .order_by(UploadedFile.created_at.desc())\
                  .offset(skip)\
                  .limit(limit)\
                  .all()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "files": [
                        {
                            "id": f.id,
                            "file_id": f.file_id,
                            "original_filename": f.original_filename,
                            "file_path": f.file_path,
                            "file_size": f.file_size,
                            "mime_type": f.mime_type,
                            "width": f.width,
                            "height": f.height,
                            "format": f.format,
                            "created_at": f.created_at.isoformat()
                        }
                        for f in files
                    ]
                }
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取上传历史失败: {str(e)}"
        )

@router.get("/upload/storage-info")
async def get_storage_info(
    db: Session = Depends(get_db)
):
    """
    获取存储信息统计
    """
    try:
        from ..database.models import UploadedFile
        import os
        from collections import defaultdict
        
        # 获取数据库统计
        total_files = db.query(UploadedFile).count()
        
        # 计算总大小
        all_files = db.query(UploadedFile).all()
        total_size = sum(f.file_size for f in all_files) if all_files else 0
        
        # 按日期统计文件
        files_by_date = defaultdict(lambda: {"count": 0, "size": 0})
        all_files = db.query(UploadedFile).all()
        
        for file_record in all_files:
            date_str = file_record.created_at.strftime("%Y-%m-%d")
            files_by_date[date_str]["count"] += 1
            files_by_date[date_str]["size"] += file_record.file_size
        
        # 检查目录结构
        directory_structure = {}
        if os.path.exists(UPLOAD_BASE_DIR):
            for root, dirs, files in os.walk(UPLOAD_BASE_DIR):
                rel_path = os.path.relpath(root, UPLOAD_BASE_DIR)
                if rel_path != ".":
                    directory_structure[rel_path] = len(files)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "total_files": total_files,
                    "total_size": total_size,
                    "total_size_mb": round(total_size / 1024 / 1024, 2),
                    "files_by_date": dict(files_by_date),
                    "directory_structure": directory_structure,
                    "storage_path_format": "uploads/YYYY/MM/DD/"
                }
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取存储信息失败: {str(e)}"
        ) 