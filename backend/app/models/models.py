from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from app.database.database import Base

class UserSettings(Base):
    __tablename__ = "user_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    api_provider = Column(String(50), default="openai")  # openai, openrouter, deepseek
    api_key = Column(Text)  # 加密存储
    api_base_url = Column(String(255))  # 自定义API地址
    default_source_lang = Column(String(10), default="auto")
    default_target_lang = Column(String(10), default="en")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TranslationHistory(Base):
    __tablename__ = "translation_history"
    
    id = Column(Integer, primary_key=True, index=True)
    original_image_path = Column(String(255), nullable=False)
    translated_image_path = Column(String(255))
    source_language = Column(String(10))
    target_language = Column(String(10))
    ocr_result = Column(JSON)  # OCR识别结果
    translation_result = Column(JSON)  # 翻译结果
    processing_time = Column(Float)  # 处理耗时（秒）
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class SupportedLanguages(Base):
    __tablename__ = "supported_languages"
    
    id = Column(Integer, primary_key=True, index=True)
    language_code = Column(String(10), unique=True, nullable=False)
    language_name = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow) 