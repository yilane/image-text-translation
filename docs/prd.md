# 图片文字翻译项目需求文档

## 项目概述

开发一个智能图片文字翻译工具，用户可以上传包含文字的图片，系统自动识别文字内容并通过AI大模型翻译成目标语言，同时保持原图片的排版、字体样式和视觉效果。

## 核心功能需求

### 1. 图片导入功能
- **支持格式**：PNG、JPG、JPEG、BMP、TIFF、WebP
- **文件大小限制**：建议单文件不超过10MB
- **导入方式**：
  - 拖拽上传
  - 点击选择文件
  - 粘贴剪贴板图片
  - 批量上传（可选）

### 2. 文字识别与翻译
- **OCR文字识别**：
  - 准确识别图片中的文字内容
  - 检测文字区域和边界框
  - 识别文字方向和排列方式
  - 支持手写字体和多种印刷字体

- **语言支持**：
  - 源语言自动检测
  - 目标语言：中文、英文、日文、韩文、法文、德文、西班牙文、俄文等主流语言
  - 支持语言扩展

### 3. 图片重构与排版保持
- **排版保持**：
  - 保持原文字的位置坐标
  - 维持文字行间距和字间距
  - 保留文字对齐方式（左对齐、居中、右对齐）
  
- **字体样式**：
  - 尽量匹配原字体风格
  - 保持字体大小比例
  - 保留粗体、斜体等样式
  - 维持文字颜色

## 技术架构方案

### 前端技术栈
- **框架**：React 18 + TypeScript
- **UI库**：Ant Design
- **图片处理**：Fabric.js / Konva.js
- **文件上传**：react-dropzone
- **状态管理**：Redux Toolkit / Zustand
- **HTTP客户端**：Axios

### 后端技术栈
- **框架**：Python + FastAPI
- **OCR服务**：PaddleOCR（百度开源OCR项目）
- **翻译服务**：AI大模型API调用
  - OpenAI GPT-3.5/GPT-4
  - OpenRouter（多模型接入平台）
  - DeepSeek Chat API
  - 支持其他兼容OpenAI格式的API
- **图像处理**：Pillow、OpenCV-Python
- **异步处理**：asyncio、aiohttp
- **文件处理**：python-multipart

### 数据库与存储
- **数据库**：SQLite / PostgreSQL（用户配置、翻译历史）
- **文件存储**：本地存储 / MinIO / 云存储
- **缓存**：Redis（可选，用于API调用缓存）

## 详细实现流程

### 第一阶段：图片预处理
1. **图片上传验证**
   - 文件格式检查
   - 文件大小限制
   - 图片质量评估

2. **图像优化**
   - 图片去噪处理
   - 对比度增强
   - 分辨率适配

### 第二阶段：文字识别
1. **PaddleOCR识别**
   - 调用PaddleOCR进行文字识别
   - 获取文字内容、位置坐标和置信度
   - 识别文字的方向和语言

2. **文字区域分析**
   - 文字块分组和排序
   - 行列关系分析
   - 文字边界框计算

### 第三阶段：AI翻译
1. **语言检测**
   - 基于识别文字自动检测源语言
   - 用户手动选择确认

2. **AI大模型翻译**
   - 构建翻译提示词（Prompt）
   - 调用选定的AI模型API
   - 支持上下文相关的翻译
   - 保持专业术语一致性

### 第四阶段：图片重构
1. **文字区域处理**
   - 智能移除原文字内容
   - 背景修复和填充

2. **翻译文字渲染**
   - 根据原文字样式选择合适字体
   - 计算文字布局和大小
   - 处理文本溢出和换行

3. **图片合成**
   - 将翻译文字绘制到原图位置
   - 保持文字颜色和样式
   - 生成最终翻译图片

## 用户界面设计

### 主要页面组件
1. **上传组件**
   - Ant Design Upload 组件
   - 拖拽上传区域
   - 文件格式和大小提示
   - 上传进度展示

2. **配置面板**
   - 源语言选择器
   - 目标语言选择器
   - AI模型选择（OpenAI/OpenRouter/DeepSeek）
   - API密钥配置

3. **预览组件**
   - 原图与翻译图对比显示
   - 识别文字区域高亮
   - 翻译结果实时预览

4. **结果操作**
   - 下载翻译后图片
   - 重新翻译功能
   - 历史记录查看

### 交互功能
- 文字区域点击编辑
- 手动调整翻译内容
- 批量处理模式
- 设置保存和导入

## 核心技术实现

### PaddleOCR集成
```python
# 核心OCR识别逻辑
from paddleocr import PaddleOCR

class OCRService:
    def __init__(self):
        self.ocr = PaddleOCR(use_angle_cls=True, lang='ch')
    
    def extract_text(self, image_path):
        result = self.ocr.ocr(image_path, cls=True)
        return self.parse_ocr_result(result)
```

### AI翻译服务
```python
# AI翻译API调用
class TranslationService:
    def __init__(self, api_provider, api_key):
        self.provider = api_provider  # openai, openrouter, deepseek
        self.api_key = api_key
    
    async def translate_text(self, text, source_lang, target_lang):
        prompt = self.build_translation_prompt(text, source_lang, target_lang)
        return await self.call_ai_api(prompt)
```

### 图像处理流程
```python
# 图像处理和文字替换
class ImageProcessor:
    def remove_original_text(self, image, text_regions):
        # 移除原文字，背景修复
        pass
    
    def render_translated_text(self, image, translations, styles):
        # 渲染翻译文字到图片
        pass
```

## 技术难点与解决方案

### 1. PaddleOCR优化
- **问题**：特殊场景识别准确率
- **解决方案**：
  - 图像预处理优化
  - 多语言模型切换
  - 置信度阈值调整
  - 用户手动校正功能

### 2. AI翻译质量
- **问题**：上下文理解和专业术语
- **解决方案**：
  - 精心设计翻译提示词
  - 支持多个AI模型对比
  - 用户自定义术语词典
  - 翻译历史学习

### 3. 排版算法
- **问题**：翻译后文本长度变化
- **解决方案**：
  - 动态字体大小调整
  - 智能换行处理
  - 区域扩展算法
  - 布局优化策略

### 4. 背景修复
- **问题**：移除文字后的背景填充
- **解决方案**：
  - 基于周边像素的智能填充
  - 纹理匹配算法
  - 深度学习修复模型（可选）

## API接口设计

### 核心接口
1. **POST /api/upload** - 图片上传
2. **POST /api/ocr** - 文字识别
3. **POST /api/translate** - AI翻译
4. **POST /api/process** - 图片处理
5. **GET /api/result/{task_id}** - 获取处理结果

### 配置接口
1. **POST /api/config/ai** - AI模型配置
2. **GET /api/languages** - 支持语言列表
3. **POST /api/settings** - 用户设置保存

## 性能优化策略

### 前端优化
- 图片压缩上传
- 组件懒加载
- 结果缓存机制
- 分片上传大文件

### 后端优化
- 异步任务队列
- 图像处理并行化
- AI API调用池化
- 结果缓存存储

### 系统优化
- CDN静态资源加速
- 数据库查询优化
- 内存使用优化
- 错误重试机制

## 部署架构

### 开发环境
- 前端：Vite + React开发服务器
- 后端：FastAPI + Uvicorn
- 数据库：SQLite本地文件

### 生产环境
- 前端：Nginx静态文件服务
- 后端：FastAPI + Gunicorn/Uvicorn
- 数据库：PostgreSQL
- 反向代理：Nginx
- 容器化：Docker + Docker Compose

## 扩展功能规划

### 高级功能
1. **智能批量处理**
   - 文件夹批量上传
   - 自动语言检测
   - 批量下载结果

2. **用户体验增强**
   - 实时翻译预览
   - 历史记录管理
   - 自定义翻译模板

3. **API服务化**
   - RESTful API接口
   - SDK开发包
   - Webhook回调支持

### 集成扩展
1. **第三方集成**
   - 浏览器扩展插件
   - 移动端APP
   - 桌面应用程序

2. **AI能力扩展**
   - 图像背景智能修复
   - 文字风格迁移
   - 多模态内容理解

## 总结

本项目基于PaddleOCR和AI大模型的技术组合，能够实现高质量的图片文字翻译功能。通过FastAPI后端和Ant Design前端的现代化技术栈，可以构建出用户体验良好、功能完整的翻译工具。重点关注OCR识别精度、AI翻译质量和排版保持三个核心技术点，确保最终产品的实用性和稳定性。