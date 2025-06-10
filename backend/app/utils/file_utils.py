import os
import mimetypes
from PIL import Image
from typing import Dict, Any

def validate_image_file(file_path: str) -> bool:
    """
    验证图像文件是否有效
    """
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except Exception:
        return False

def get_image_info(file_path: str) -> Dict[str, Any]:
    """
    获取图像文件信息
    """
    try:
        with Image.open(file_path) as img:
            return {
                "width": img.width,
                "height": img.height,
                "format": img.format,
                "mode": img.mode,
                "size_bytes": os.path.getsize(file_path)
            }
    except Exception as e:
        raise ValueError(f"无法读取图像信息: {str(e)}")

def get_file_mimetype(file_path: str) -> str:
    """
    获取文件MIME类型
    """
    mimetype, _ = mimetypes.guess_type(file_path)
    return mimetype or "application/octet-stream"

def ensure_directory(directory: str) -> None:
    """
    确保目录存在
    """
    os.makedirs(directory, exist_ok=True)

def safe_filename(filename: str) -> str:
    """
    生成安全的文件名
    """
    # 移除或替换不安全的字符
    import re
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    return filename[:255]  # 限制文件名长度 