from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import asyncio
import logging
from datetime import datetime

from ..core.database import get_db
from ..services.newsapi_service import NewsAPIService
from ..services.newsapi_mock_service import NewsAPIMockService
from ..services.newsapi_real_data_service import NewsAPIRealDataService

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/newsapi/test")
async def test_newsapi_connection(
    use_mock: bool = Query(True, description="使用模拟服务")
):
    """测试NewsAPI连接"""
    if use_mock:
        newsapi_service = NewsAPIMockService()
    else:
        newsapi_service = NewsAPIService()
    
    return await newsapi_service.test_api_connection()

@router.get("/newsapi/collect-sample")
async def collect_newsapi_sample(
    company_name: str = Query("OpenAI", description="公司名称"),
    year: int = Query(2025, description="年份"),
    month: int = Query(9, description="月份"),
    use_mock: bool = Query(True, description="使用模拟服务"),
    db: Session = Depends(get_db)
):
    """采集单个公司的NewsAPI数据样本"""
    if use_mock:
        newsapi_service = NewsAPIMockService()
    else:
        newsapi_service = NewsAPIService()
    
    try:
        result = await newsapi_service.get_monthly_mentions(company_name, year, month)
        return result
    except Exception as e:
        logger.error(f"采集NewsAPI数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"采集失败: {str(e)}")

@router.post("/newsapi/collect-three-months")
async def collect_three_months_data(
    background_tasks: BackgroundTasks,
    company_names: List[str] = Query(["OpenAI", "Anthropic", "DeepMind"], description="公司名称列表"),
    db: Session = Depends(get_db)
):
    """采集指定公司3个月的NewsAPI数据"""
    
    task_id = f"newsapi_collect_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    async def collect_task():
        newsapi_service = NewsAPIService()
        
        # 目标月份：2025年7月、8月、9月
        target_months = [(2025, 7), (2025, 8), (2025, 9)]
        results = {}
        
        for company_name in company_names:
            company_results = {}
            
            for year, month in target_months:
                try:
                    logger.info(f"开始采集 {company_name} {year}-{month:02d} 的数据...")
                    monthly_data = await newsapi_service.get_monthly_mentions(company_name, year, month)
                    month_key = f"{year}-{month:02d}"
                    company_results[month_key] = monthly_data
                    
                    # 添加延迟避免API限流
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"采集 {company_name} {year}-{month:02d} 数据失败: {str(e)}")
                    month_key = f"{year}-{month:02d}"
                    company_results[month_key] = {
                        "success": False,
                        "error": str(e),
                        "mention_count": 0
                    }
            
            results[company_name] = company_results
        
        logger.info(f"NewsAPI数据采集完成: {len(company_names)}家公司，3个月数据")
        return results
    
    # 添加后台任务
    background_tasks.add_task(collect_task)
    
    return {
        "task_id": task_id,
        "status": "started",
        "message": f"NewsAPI数据采集任务已开始（{len(company_names)}家公司，3个月数据）",
        "target_companies": company_names,
        "target_months": ["2025-07", "2025-08", "2025-09"]
    }

@router.get("/newsapi/api-limits")
async def get_newsapi_limits():
    """获取NewsAPI限制信息"""
    newsapi_service = NewsAPIService()
    return newsapi_service.get_api_limits()

# ===== 专门针对178家公司的NewsAPI分析功能 =====

@router.post("/newsapi/generate-company-data")
async def generate_newsapi_company_data(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """为178家公司生成NewsAPI数据（2025年7月、8月、9月）"""
    
    task_id = f"newsapi_company_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    async def generate_task():
        real_data_service = NewsAPIRealDataService(db)
        try:
            result = await real_data_service.generate_newsapi_data_for_companies()
            logger.info(f"NewsAPI公司数据生成完成: {result['message']}")
        except Exception as e:
            logger.error(f"NewsAPI公司数据生成失败: {str(e)}")
    
    # 添加后台任务
    background_tasks.add_task(generate_task)
    
    return {
        "task_id": task_id,
        "status": "started",
        "message": "正在为178家公司生成NewsAPI数据（2025年7月、8月、9月）",
        "estimated_time": "约30-60秒"
    }

@router.get("/newsapi/company-analysis")
async def get_newsapi_company_analysis(
    target_month: str = Query("2025-09", description="目标月份，格式YYYY-MM"),
    db: Session = Depends(get_db)
):
    """获取178家公司的NewsAPI环比分析结果"""
    
    real_data_service = NewsAPIRealDataService(db)
    
    try:
        result = real_data_service.get_newsapi_mom_analysis(target_month)
        return result
    except Exception as e:
        logger.error(f"获取NewsAPI公司分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")

@router.get("/newsapi/company-summary")
async def get_newsapi_company_summary(
    db: Session = Depends(get_db)
):
    """获取178家公司NewsAPI数据汇总统计"""
    
    real_data_service = NewsAPIRealDataService(db)
    
    try:
        result = real_data_service.get_newsapi_summary_stats()
        return result
    except Exception as e:
        logger.error(f"获取NewsAPI汇总统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")