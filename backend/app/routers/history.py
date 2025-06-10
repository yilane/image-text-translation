"""
历史记录API路由
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from ..services.history_service import history_service

router = APIRouter()

class HistoryDeleteRequest(BaseModel):
    """历史记录删除请求"""
    history_ids: List[int]

@router.get("/history/list")
async def get_history_list(
    limit: int = Query(50, ge=1, le=100, description="每页记录数"),
    offset: int = Query(0, ge=0, description="偏移量"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    source_language: Optional[str] = Query(None, description="源语言"),
    target_language: Optional[str] = Query(None, description="目标语言"),
    provider: Optional[str] = Query(None, description="翻译服务提供商"),
    search_text: Optional[str] = Query(None, description="搜索文本")
):
    """获取历史记录列表"""
    try:
        # 解析日期
        start_datetime = None
        end_datetime = None
        
        if start_date:
            try:
                start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="开始日期格式错误，请使用 YYYY-MM-DD")
        
        if end_date:
            try:
                end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
                # 设置为当天的最后一秒
                end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
            except ValueError:
                raise HTTPException(status_code=400, detail="结束日期格式错误，请使用 YYYY-MM-DD")
        
        # 调用服务
        result = history_service.get_history_list(
            limit=limit,
            offset=offset,
            start_date=start_datetime,
            end_date=end_datetime,
            source_language=source_language,
            target_language=target_language,
            provider=provider,
            search_text=search_text
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["message"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史记录列表失败: {str(e)}")

@router.get("/history/{history_id}")
async def get_history_detail(history_id: int):
    """获取历史记录详情"""
    try:
        if history_id <= 0:
            raise HTTPException(status_code=400, detail="历史记录ID必须大于0")
        
        result = history_service.get_history_detail(history_id)
        
        if not result["success"]:
            if "不存在" in result["message"]:
                raise HTTPException(status_code=404, detail=result["message"])
            else:
                raise HTTPException(status_code=500, detail=result["message"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史记录详情失败: {str(e)}")

@router.delete("/history/{history_id}")
async def delete_history(history_id: int):
    """删除单个历史记录"""
    try:
        if history_id <= 0:
            raise HTTPException(status_code=400, detail="历史记录ID必须大于0")
        
        result = history_service.delete_history(history_id)
        
        if not result["success"]:
            if "不存在" in result["message"]:
                raise HTTPException(status_code=404, detail=result["message"])
            else:
                raise HTTPException(status_code=500, detail=result["message"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除历史记录失败: {str(e)}")

@router.delete("/history/batch")
async def delete_histories(request: HistoryDeleteRequest):
    """批量删除历史记录"""
    try:
        if not request.history_ids:
            raise HTTPException(status_code=400, detail="请提供要删除的历史记录ID列表")
        
        if len(request.history_ids) > 100:
            raise HTTPException(status_code=400, detail="一次最多删除100条记录")
        
        # 验证ID
        for history_id in request.history_ids:
            if history_id <= 0:
                raise HTTPException(status_code=400, detail="历史记录ID必须大于0")
        
        result = history_service.delete_histories(request.history_ids)
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["message"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量删除历史记录失败: {str(e)}")

@router.delete("/history/clean")
async def clean_old_histories(
    days: int = Query(30, ge=1, le=365, description="清理多少天前的记录")
):
    """清理旧的历史记录"""
    try:
        result = history_service.clean_old_histories(days)
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["message"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理旧历史记录失败: {str(e)}")

@router.get("/history/statistics/overview")
async def get_statistics():
    """获取历史记录统计信息"""
    try:
        result = history_service.get_statistics()
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["message"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

@router.get("/history/search/suggestions")
async def get_search_suggestions(
    query: str = Query(..., min_length=1, description="搜索关键词")
):
    """获取搜索建议"""
    try:
        # 这里可以实现智能搜索建议，比如根据历史搜索记录、常用词汇等
        # 暂时返回简单的建议
        suggestions = []
        
        # 语言建议
        languages = ["中文", "英文", "日文", "韩文", "法文", "德文", "西班牙文", "俄文"]
        for lang in languages:
            if query.lower() in lang.lower():
                suggestions.append(f"语言:{lang}")
        
        # 提供商建议
        providers = ["OpenAI", "百度翻译", "Google翻译"]
        for provider in providers:
            if query.lower() in provider.lower():
                suggestions.append(f"提供商:{provider}")
        
        return {
            "success": True,
            "data": {
                "suggestions": suggestions[:10]  # 最多返回10个建议
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取搜索建议失败: {str(e)}")

@router.get("/history/export/csv")
async def export_histories_csv(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    source_language: Optional[str] = Query(None, description="源语言"),
    target_language: Optional[str] = Query(None, description="目标语言"),
    provider: Optional[str] = Query(None, description="翻译服务提供商")
):
    """导出历史记录为CSV文件"""
    try:
        # 解析日期
        start_datetime = None
        end_datetime = None
        
        if start_date:
            try:
                start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="开始日期格式错误，请使用 YYYY-MM-DD")
        
        if end_date:
            try:
                end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
                end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
            except ValueError:
                raise HTTPException(status_code=400, detail="结束日期格式错误，请使用 YYYY-MM-DD")
        
        # 获取数据（不分页，获取所有符合条件的记录）
        result = history_service.get_history_list(
            limit=10000,  # 设置一个较大的限制
            offset=0,
            start_date=start_datetime,
            end_date=end_datetime,
            source_language=source_language,
            target_language=target_language,
            provider=provider
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["message"])
        
        # 生成CSV数据
        import csv
        import io
        from fastapi.responses import StreamingResponse
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入表头
        writer.writerow([
            "ID", "文件名", "文件大小(字节)", "源语言", "目标语言", "翻译服务",
            "置信度阈值", "原文", "译文", "处理时间(秒)", "文字区域数", "创建时间"
        ])
        
        # 写入数据
        for history in result["data"]["histories"]:
            writer.writerow([
                history["id"],
                history["file_name"],
                history["file_size"],
                history["source_language"],
                history["target_language"],
                history["provider"],
                history["min_confidence"],
                history["original_text"],
                history["translated_text"],
                history["processing_time"],
                history["text_regions_count"],
                history["created_at"]
            ])
        
        output.seek(0)
        
        # 返回CSV文件
        response = StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),  # 使用utf-8-sig支持中文
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=translation_history.csv"}
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出CSV失败: {str(e)}") 