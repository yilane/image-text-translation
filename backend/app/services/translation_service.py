import openai
import requests
import logging
import os
from typing import List, Dict, Optional
from enum import Enum
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class TranslationProvider(Enum):
    """翻译服务提供商"""
    OPENAI = "openai"
    BAIDU = "baidu"
    GOOGLE = "google"

class TranslationService:
    def __init__(self):
        """初始化翻译服务"""
        self.openai_client = None
        self.baidu_api_key = os.getenv("BAIDU_API_KEY")
        self.baidu_secret_key = os.getenv("BAIDU_SECRET_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        
        # 初始化OpenAI客户端
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            self.openai_client = openai.OpenAI(api_key=openai_api_key)
    
    async def translate_text(self, 
                           text: str, 
                           target_language: str = "en", 
                           source_language: str = "auto",
                           provider: TranslationProvider = TranslationProvider.OPENAI) -> str:
        """
        翻译文字
        
        Args:
            text: 需要翻译的文字
            target_language: 目标语言
            source_language: 源语言
            provider: 翻译服务提供商
            
        Returns:
            翻译后的文字
        """
        try:
            if provider == TranslationProvider.OPENAI:
                return await self._translate_with_openai(text, target_language, source_language)
            elif provider == TranslationProvider.BAIDU:
                return await self._translate_with_baidu(text, target_language, source_language)
            elif provider == TranslationProvider.GOOGLE:
                return await self._translate_with_google(text, target_language, source_language)
            else:
                raise ValueError(f"不支持的翻译提供商: {provider}")
                
        except Exception as e:
            logger.error(f"翻译失败: {e}")
            # 返回原文作为fallback
            return text
    
    async def _translate_with_openai(self, text: str, target_language: str, source_language: str) -> str:
        """使用OpenAI进行翻译"""
        if not self.openai_client:
            raise ValueError("OpenAI API密钥未配置")
        
        try:
            # 构建翻译提示
            language_map = {
                "en": "English",
                "zh": "Chinese",
                "ja": "Japanese",
                "ko": "Korean",
                "fr": "French",
                "de": "German",
                "es": "Spanish",
                "ru": "Russian"
            }
            
            target_lang_name = language_map.get(target_language, target_language)
            
            prompt = f"请将以下文字翻译成{target_lang_name}，只返回翻译结果，不要添加任何解释：\n\n{text}"
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一个专业的翻译助手，能够准确翻译各种语言。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            translated_text = response.choices[0].message.content.strip()
            return translated_text
            
        except Exception as e:
            logger.error(f"OpenAI翻译失败: {e}")
            raise e
    
    async def _translate_with_baidu(self, text: str, target_language: str, source_language: str) -> str:
        """使用百度翻译API进行翻译"""
        if not self.baidu_api_key or not self.baidu_secret_key:
            raise ValueError("百度翻译API密钥未配置")
        
        try:
            import hashlib
            import random
            import time
            
            # 百度翻译API参数
            url = "https://fanyi-api.baidu.com/api/trans/vip/translate"
            
            # 语言代码映射
            lang_map = {
                "auto": "auto",
                "zh": "zh",
                "en": "en",
                "ja": "jp",
                "ko": "kor",
                "fr": "fra",
                "de": "de",
                "es": "spa",
                "ru": "ru"
            }
            
            from_lang = lang_map.get(source_language, "auto")
            to_lang = lang_map.get(target_language, "en")
            
            # 生成签名
            salt = str(random.randint(32768, 65536))
            sign_str = self.baidu_api_key + text + salt + self.baidu_secret_key
            sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest()
            
            params = {
                'q': text,
                'from': from_lang,
                'to': to_lang,
                'appid': self.baidu_api_key,
                'salt': salt,
                'sign': sign
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=params) as response:
                    result = await response.json()
                    
                    if 'trans_result' in result:
                        return result['trans_result'][0]['dst']
                    else:
                        raise ValueError(f"百度翻译API返回错误: {result}")
                        
        except Exception as e:
            logger.error(f"百度翻译失败: {e}")
            raise e
    
    async def _translate_with_google(self, text: str, target_language: str, source_language: str) -> str:
        """使用Google翻译API进行翻译"""
        if not self.google_api_key:
            raise ValueError("Google翻译API密钥未配置")
        
        try:
            url = "https://translation.googleapis.com/language/translate/v2"
            
            params = {
                'key': self.google_api_key,
                'q': text,
                'target': target_language,
                'format': 'text'
            }
            
            if source_language != "auto":
                params['source'] = source_language
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=params) as response:
                    result = await response.json()
                    
                    if 'data' in result and 'translations' in result['data']:
                        return result['data']['translations'][0]['translatedText']
                    else:
                        raise ValueError(f"Google翻译API返回错误: {result}")
                        
        except Exception as e:
            logger.error(f"Google翻译失败: {e}")
            raise e
    
    async def batch_translate(self, 
                            texts: List[str], 
                            target_language: str = "en",
                            source_language: str = "auto",
                            provider: TranslationProvider = TranslationProvider.OPENAI) -> List[str]:
        """
        批量翻译文字
        
        Args:
            texts: 需要翻译的文字列表
            target_language: 目标语言
            source_language: 源语言
            provider: 翻译服务提供商
            
        Returns:
            翻译后的文字列表
        """
        try:
            # 并发翻译
            tasks = [
                self.translate_text(text, target_language, source_language, provider)
                for text in texts
            ]
            
            translated_texts = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理异常结果
            results = []
            for i, result in enumerate(translated_texts):
                if isinstance(result, Exception):
                    logger.error(f"翻译第{i}个文本失败: {result}")
                    results.append(texts[i])  # 使用原文
                else:
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"批量翻译失败: {e}")
            return texts  # 返回原文列表
    
    def detect_language(self, text: str) -> str:
        """
        检测文字语言
        
        Args:
            text: 需要检测的文字
            
        Returns:
            语言代码
        """
        try:
            # 简单的语言检测逻辑
            import re
            
            # 检测中文
            if re.search(r'[\u4e00-\u9fff]', text):
                return "zh"
            
            # 检测日文
            if re.search(r'[\u3040-\u309f\u30a0-\u30ff]', text):
                return "ja"
            
            # 检测韩文
            if re.search(r'[\uac00-\ud7af]', text):
                return "ko"
            
            # 检测俄文
            if re.search(r'[\u0400-\u04ff]', text):
                return "ru"
            
            # 默认为英文
            return "en"
            
        except Exception as e:
            logger.error(f"语言检测失败: {e}")
            return "auto"

# 创建全局翻译服务实例
translation_service = TranslationService() 