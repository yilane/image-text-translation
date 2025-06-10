"""
历史记录服务
管理翻译历史记录的查询、删除等功能
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from ..database.database import SessionLocal
from ..database.models import TranslationHistory
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_, func
import json
import logging

logger = logging.getLogger(__name__)

class HistoryService:
    """历史记录服务"""
    
    def __init__(self):
        pass
    
    def get_history_list(
        self, 
        limit: int = 50, 
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        source_language: Optional[str] = None,
        target_language: Optional[str] = None,
        provider: Optional[str] = None,
        search_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取历史记录列表
        
        Args:
            limit: 每页记录数
            offset: 偏移量
            start_date: 开始日期
            end_date: 结束日期
            source_language: 源语言过滤
            target_language: 目标语言过滤
            provider: 翻译服务提供商过滤
            search_text: 搜索文本
        """
        db = SessionLocal()
        try:
            # 构建查询
            query = db.query(TranslationHistory)
            
            # 日期过滤
            if start_date:
                query = query.filter(TranslationHistory.created_at >= start_date)
            if end_date:
                query = query.filter(TranslationHistory.created_at <= end_date)
            
            # 语言过滤
            if source_language:
                query = query.filter(TranslationHistory.source_language == source_language)
            if target_language:
                query = query.filter(TranslationHistory.target_language == target_language)
            
            # 服务提供商过滤
            if provider:
                query = query.filter(TranslationHistory.provider == provider)
            
            # 文本搜索（在原文和译文中搜索）
            if search_text:
                query = query.filter(
                    or_(
                        TranslationHistory.original_text.ilike(f'%{search_text}%'),
                        TranslationHistory.translated_text.ilike(f'%{search_text}%')
                    )
                )
            
            # 获取总数
            total = query.count()
            
            # 分页查询
            histories = query.order_by(desc(TranslationHistory.created_at))\
                           .offset(offset)\
                           .limit(limit)\
                           .all()
            
            # 转换为字典格式
            history_list = []
            for history in histories:
                history_dict = {
                    "id": history.id,
                    "file_name": history.file_name,
                    "file_size": history.file_size,
                    "source_language": history.source_language,
                    "target_language": history.target_language,
                    "provider": history.provider,
                    "min_confidence": history.min_confidence,
                    "original_text": history.original_text,
                    "translated_text": history.translated_text,
                    "original_image_path": history.original_image_path,
                    "translated_image_path": history.translated_image_path,
                    "processing_time": history.processing_time,
                    "text_regions_count": history.text_regions_count,
                    "created_at": history.created_at.isoformat(),
                    "updated_at": history.updated_at.isoformat() if history.updated_at else None
                }
                
                # 如果有元数据，解析JSON
                if history.meta_data:
                    try:
                        history_dict["metadata"] = json.loads(history.meta_data)
                    except json.JSONDecodeError:
                        history_dict["metadata"] = {}
                else:
                    history_dict["metadata"] = {}
                
                history_list.append(history_dict)
            
            return {
                "success": True,
                "data": {
                    "histories": history_list,
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < total
                }
            }
            
        except Exception as e:
            logger.error(f"获取历史记录列表失败: {e}")
            return {
                "success": False,
                "message": f"获取历史记录列表失败: {str(e)}"
            }
        finally:
            db.close()
    
    def get_history_detail(self, history_id: int) -> Dict[str, Any]:
        """获取历史记录详情"""
        db = SessionLocal()
        try:
            history = db.query(TranslationHistory).filter(
                TranslationHistory.id == history_id
            ).first()
            
            if not history:
                return {
                    "success": False,
                    "message": "历史记录不存在"
                }
            
            # 转换为详细字典格式
            history_detail = {
                "id": history.id,
                "file_id": history.file_id,
                "file_name": history.file_name,
                "file_size": history.file_size,
                "source_language": history.source_language,
                "target_language": history.target_language,
                "provider": history.provider,
                "min_confidence": history.min_confidence,
                "original_text": history.original_text,
                "translated_text": history.translated_text,
                "original_image_path": history.original_image_path,
                "translated_image_path": history.translated_image_path,
                "processing_time": history.processing_time,
                "text_regions_count": history.text_regions_count,
                "created_at": history.created_at.isoformat(),
                "updated_at": history.updated_at.isoformat() if history.updated_at else None
            }
            
            # 解析元数据
            if history.meta_data:
                try:
                    history_detail["metadata"] = json.loads(history.meta_data)
                except json.JSONDecodeError:
                    history_detail["metadata"] = {}
            else:
                history_detail["metadata"] = {}
            
            return {
                "success": True,
                "data": history_detail
            }
            
        except Exception as e:
            logger.error(f"获取历史记录详情失败: {e}")
            return {
                "success": False,
                "message": f"获取历史记录详情失败: {str(e)}"
            }
        finally:
            db.close()
    
    def delete_history(self, history_id: int) -> Dict[str, Any]:
        """删除历史记录"""
        db = SessionLocal()
        try:
            history = db.query(TranslationHistory).filter(
                TranslationHistory.id == history_id
            ).first()
            
            if not history:
                return {
                    "success": False,
                    "message": "历史记录不存在"
                }
            
            # 删除文件（如果存在）
            import os
            if history.original_image_path and os.path.exists(history.original_image_path):
                try:
                    os.remove(history.original_image_path)
                except Exception as e:
                    logger.warning(f"删除原始图片文件失败: {e}")
            
            if history.translated_image_path and os.path.exists(history.translated_image_path):
                try:
                    os.remove(history.translated_image_path)
                except Exception as e:
                    logger.warning(f"删除翻译图片文件失败: {e}")
            
            # 删除数据库记录
            db.delete(history)
            db.commit()
            
            return {
                "success": True,
                "message": "历史记录删除成功"
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"删除历史记录失败: {e}")
            return {
                "success": False,
                "message": f"删除历史记录失败: {str(e)}"
            }
        finally:
            db.close()
    
    def delete_histories(self, history_ids: List[int]) -> Dict[str, Any]:
        """批量删除历史记录"""
        db = SessionLocal()
        try:
            histories = db.query(TranslationHistory).filter(
                TranslationHistory.id.in_(history_ids)
            ).all()
            
            if not histories:
                return {
                    "success": False,
                    "message": "没有找到要删除的历史记录"
                }
            
            deleted_count = 0
            
            for history in histories:
                # 删除文件
                import os
                if history.original_image_path and os.path.exists(history.original_image_path):
                    try:
                        os.remove(history.original_image_path)
                    except Exception as e:
                        logger.warning(f"删除原始图片文件失败: {e}")
                
                if history.translated_image_path and os.path.exists(history.translated_image_path):
                    try:
                        os.remove(history.translated_image_path)
                    except Exception as e:
                        logger.warning(f"删除翻译图片文件失败: {e}")
                
                # 删除数据库记录
                db.delete(history)
                deleted_count += 1
            
            db.commit()
            
            return {
                "success": True,
                "message": f"成功删除 {deleted_count} 条历史记录"
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"批量删除历史记录失败: {e}")
            return {
                "success": False,
                "message": f"批量删除历史记录失败: {str(e)}"
            }
        finally:
            db.close()
    
    def clean_old_histories(self, days: int = 30) -> Dict[str, Any]:
        """清理旧的历史记录"""
        db = SessionLocal()
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            old_histories = db.query(TranslationHistory).filter(
                TranslationHistory.created_at < cutoff_date
            ).all()
            
            if not old_histories:
                return {
                    "success": True,
                    "message": "没有需要清理的旧记录"
                }
            
            deleted_count = 0
            
            for history in old_histories:
                # 删除文件
                import os
                if history.original_image_path and os.path.exists(history.original_image_path):
                    try:
                        os.remove(history.original_image_path)
                    except Exception as e:
                        logger.warning(f"删除原始图片文件失败: {e}")
                
                if history.translated_image_path and os.path.exists(history.translated_image_path):
                    try:
                        os.remove(history.translated_image_path)
                    except Exception as e:
                        logger.warning(f"删除翻译图片文件失败: {e}")
                
                # 删除数据库记录
                db.delete(history)
                deleted_count += 1
            
            db.commit()
            
            return {
                "success": True,
                "message": f"成功清理 {deleted_count} 条 {days} 天前的历史记录"
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"清理旧历史记录失败: {e}")
            return {
                "success": False,
                "message": f"清理旧历史记录失败: {str(e)}"
            }
        finally:
            db.close()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取历史记录统计信息"""
        db = SessionLocal()
        try:
            # 总记录数
            total_records = db.query(TranslationHistory).count()
            
            # 最近7天的记录数
            week_ago = datetime.now() - timedelta(days=7)
            recent_records = db.query(TranslationHistory).filter(
                TranslationHistory.created_at >= week_ago
            ).count()
            
            # 按语言对统计
            language_stats = db.query(
                TranslationHistory.source_language,
                TranslationHistory.target_language,
                func.count(TranslationHistory.id).label('count')
            ).group_by(
                TranslationHistory.source_language,
                TranslationHistory.target_language
            ).all()
            
            # 按提供商统计
            provider_stats = db.query(
                TranslationHistory.provider,
                func.count(TranslationHistory.id).label('count')
            ).group_by(TranslationHistory.provider).all()
            
            # 平均处理时间
            avg_processing_time = db.query(
                func.avg(TranslationHistory.processing_time)
            ).scalar() or 0
            
            return {
                "success": True,
                "data": {
                    "total_records": total_records,
                    "recent_records": recent_records,
                    "language_pairs": [
                        {
                            "source_language": stat[0],
                            "target_language": stat[1],
                            "count": stat[2]
                        }
                        for stat in language_stats
                    ],
                    "providers": [
                        {
                            "provider": stat[0],
                            "count": stat[1]
                        }
                        for stat in provider_stats
                    ],
                    "avg_processing_time": round(avg_processing_time, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"获取历史记录统计失败: {e}")
            return {
                "success": False,
                "message": f"获取历史记录统计失败: {str(e)}"
            }
        finally:
            db.close()

# 全局历史记录服务实例
history_service = HistoryService() 