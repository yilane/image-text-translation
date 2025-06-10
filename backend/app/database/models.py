"""
数据库模型定义
"""
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class UploadedFile(Base):
    """上传文件记录"""
    __tablename__ = "uploaded_files"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String(36), unique=True, index=True)  # UUID
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    width = Column(Integer)
    height = Column(Integer)
    format = Column(String(10))
    mode = Column(String(10))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TranslationHistory(Base):
    """翻译历史记录"""
    __tablename__ = "translation_history"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String(36), index=True)  # 关联上传文件
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    
    # 翻译配置
    source_language = Column(String(10), nullable=False)
    target_language = Column(String(10), nullable=False)
    provider = Column(String(50), nullable=False)  # openai, baidu, google
    min_confidence = Column(Float, default=0.5)
    
    # 翻译结果
    original_text = Column(Text)  # 合并后的原文
    translated_text = Column(Text)  # 合并后的译文
    
    # 文件路径
    original_image_path = Column(String(500))
    translated_image_path = Column(String(500))
    
    # 处理信息
    processing_time = Column(Float)  # 处理时间（秒）
    text_regions_count = Column(Integer, default=0)  # 识别到的文字区域数量
    
    # 元数据（JSON格式存储详细信息）
    meta_data = Column(Text)  # 存储OCR结果、翻译详情等
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SystemConfig(Base):
    """系统配置"""
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(100), unique=True, index=True)
    config_value = Column(Text)
    config_type = Column(String(20), default="string")  # string, json, boolean, number
    description = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserSession(Base):
    """用户会话（为将来的多用户支持预留）"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True)
    user_id = Column(String(100), index=True, default="default")
    user_preferences = Column(Text)  # JSON格式用户偏好
    last_activity = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

class ProcessingQueue(Base):
    """处理队列（为批量处理功能预留）"""
    __tablename__ = "processing_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(36), unique=True, index=True)
    task_type = Column(String(50), nullable=False)  # translation, ocr, etc.
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    priority = Column(Integer, default=0)
    
    # 任务参数
    input_data = Column(Text)  # JSON格式输入数据
    output_data = Column(Text)  # JSON格式输出数据
    error_message = Column(Text)
    
    # 进度信息
    progress = Column(Float, default=0.0)  # 0-100
    estimated_time = Column(Integer)  # 预估剩余时间（秒）
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 