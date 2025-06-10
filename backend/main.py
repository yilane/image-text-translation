from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.routers import upload, ocr, translate, process, config, history
from app.database.database import engine
from app.database.models import Base

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="图片文字翻译API",
    description="基于PaddleOCR和AI大模型的智能图片文字翻译工具",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # 前端开发地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建上传目录
os.makedirs("uploads", exist_ok=True)
os.makedirs("results", exist_ok=True)

# 静态文件服务
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/results", StaticFiles(directory="results"), name="results")

# 注册路由
app.include_router(upload.router, prefix="/api", tags=["文件上传"])
app.include_router(ocr.router, prefix="/api", tags=["文字识别"])
app.include_router(translate.router, prefix="/api", tags=["文字翻译"])
app.include_router(process.router, prefix="/api", tags=["图像处理"])
app.include_router(config.router, prefix="/api", tags=["配置管理"])
app.include_router(history.router, prefix="/api", tags=["历史记录"])

@app.get("/")
async def root():
    return {"message": "图片文字翻译API服务正在运行"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 