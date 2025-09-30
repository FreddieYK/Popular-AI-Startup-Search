from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_  # 添加and_导入
from typing import List, Optional
import csv
import io
import logging
from datetime import datetime, timedelta

from ..core.database import get_db
from ..schemas import (
    MonthlyYoYAnalysisResponse, CalculateMonthlyRequest, 
    TaskResponse, AutomationStatus
)
from ..models import Company, MonthlyMention  # 添加缺失的导入
from ..services.analysis_service import AnalysisService
from ..services.scheduler_service import SchedulerService
from ..services.heat_index_service import HeatIndexService
from ..services.newsapi_service import NewsAPIService


logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/analysis/monthly-mom-matrix")
async def get_monthly_mom_matrix(
    months: int = Query(6, description="获取近几个月的数据"),
    company_ids: Optional[List[int]] = Query(None, description="公司ID列表"),
    db: Session = Depends(get_db)
):
    """获取矩阵形式的月度环比分析结果（每行一家公司，每列一个月份）"""
    analysis_service = AnalysisService(db)
    
    # 生成近n个月的月份列表
    current_date = datetime.now()
    month_list = []
    for i in range(months):
        target_date = current_date - timedelta(days=30*i)
        month_list.append(target_date.strftime("%Y-%m"))
    
    month_list.reverse()  # 从最早月份开始
    
    # 获取所有公司列表
    from ..models import Company
    if company_ids:
        companies = db.query(Company).filter(
            Company.id.in_(company_ids),
            Company.status == "active"
        ).all()
    else:
        companies = db.query(Company).filter(
            Company.status == "active"
        ).all()
    
    # 构建矩阵数据
    matrix_data = []
    
    for company in companies:
        company_row = {
            "company_id": company.id,
            "company_name": company.cleaned_name,
            "monthly_changes": {}
        }
        
        # 为每个月获取环比数据
        for month in month_list:
            try:
                result = analysis_service.get_monthly_mom_results(month, [company.id])  # type: ignore
                
                # 获取热度指数
                from ..models import HeatIndex
                heat_record = db.query(HeatIndex).filter(
                    HeatIndex.company_id == company.id,
                    HeatIndex.year_month == month
                ).first()
                
                if result["results"] and len(result["results"]) > 0:
                    item = result["results"][0]
                    company_row["monthly_changes"][month] = {
                        "current_month_mentions": item["current_month_mentions"],
                        "previous_month_mentions": item["previous_month_mentions"],
                        "monthly_change_percentage": item["monthly_change_percentage"],
                        "formatted_change": item["formatted_change"],
                        "status": item["status"],
                        "heat_index": heat_record.heat_index if heat_record else None,  # type: ignore
                        "heat_level": heat_record.heat_level if heat_record else "冷门"  # type: ignore
                    }
                else:
                    company_row["monthly_changes"][month] = {
                        "current_month_mentions": 0,
                        "previous_month_mentions": 0,
                        "monthly_change_percentage": 0,
                        "formatted_change": "N/A",
                        "status": "no_data",
                        "heat_index": heat_record.heat_index if heat_record else None,  # type: ignore
                        "heat_level": heat_record.heat_level if heat_record else "冷门"  # type: ignore
                    }
            except Exception as e:
                print(f"获取{company.cleaned_name}在{month}的数据失败: {str(e)}")
                company_row["monthly_changes"][month] = {
                    "current_month_mentions": 0,
                    "previous_month_mentions": 0,
                    "monthly_change_percentage": 0,
                    "formatted_change": "N/A",
                    "status": "error"
                }
        
        matrix_data.append(company_row)
    
    return {
        "matrix_data": matrix_data,
        "months": month_list,
        "total_companies": len(matrix_data),
        "analysis_type": "mom"
    }

@router.get("/analysis/monthly-mom")
async def get_monthly_mom_analysis(
    month: Optional[str] = Query(None, description="分析月份，格式YYYY-MM，默认当前月"),
    company_ids: Optional[List[int]] = Query(None, description="公司ID列表，默认全部"),
    db: Session = Depends(get_db)
):
    """获取月度环比分析结果（包含热度指数）"""
    analysis_service = AnalysisService(db)
    
    # 如果未指定月份，使用当前月份
    if not month:
        month = datetime.now().strftime("%Y-%m")
    
    # 验证月份格式
    try:
        datetime.strptime(month, "%Y-%m")
    except ValueError:
        raise HTTPException(status_code=400, detail="月份格式错误，应为YYYY-MM")
    
    # 先尝试使用环比分析数据
    try:
        result = analysis_service.get_monthly_mom_results(month, company_ids)
        logger.info(f"环比分析数据查询成功: {len(result['results'])}条记录")
    except Exception as e:
        logger.warning(f"环比分数据查询失败: {str(e)}，使用备用方案")
        # 备用方案：直接从公司表查询
        from ..models import Company
        
        if company_ids:
            companies = db.query(Company).filter(
                Company.id.in_(company_ids),
                Company.status == "active"
            ).all()
        else:
            companies = db.query(Company).filter(
                Company.status == "active"
            ).all()
        
        # 创建空的结果结构
        result = {
            "results": [
                {
                    "id": i + 1,
                    "company_id": company.id,
                    "company_name": company.cleaned_name,
                    "analysis_month": month,
                    "current_month_mentions": 0,
                    "previous_month_mentions": 0,
                    "monthly_change_percentage": 0.0,
                    "status": "no_data",
                    "formatted_change": "N/A",
                    "created_at": datetime.now()
                }
                for i, company in enumerate(companies)
            ],
            "total_companies": len(companies),
            "successful_analyses": 0,
            "failed_analyses": len(companies)
        }
    
    # 获取热度指数数据
    from ..models import HeatIndex
    
    # 为结果添加热度指数信息
    enhanced_results = []
    heat_found_count = 0
    
    for i, item in enumerate(result["results"]):
        # 获取该公司的热度指数
        heat_record = db.query(HeatIndex).filter(
            HeatIndex.company_id == item["company_id"],
            HeatIndex.year_month == month
        ).first()
        
        # 添加热度指数信息
        enhanced_item = item.copy()
        if heat_record:
            enhanced_item["heat_index"] = heat_record.heat_index  # type: ignore
            enhanced_item["heat_level"] = heat_record.heat_level  # type: ignore
            enhanced_item["avg_volume_percent"] = heat_record.avg_volume_percent  # type: ignore
            enhanced_item["peak_volume_percent"] = heat_record.peak_volume_percent  # type: ignore
            heat_found_count += 1
            
            # 调试前5条记录
            if i < 5:
                logger.info(f"热度指数调试 - 公司{i+1}: {item['company_name']} (ID: {item['company_id']}) - 找到热度记录: {heat_record.heat_index}")
        else:
            enhanced_item["heat_index"] = None
            enhanced_item["heat_level"] = "冷门"
            enhanced_item["avg_volume_percent"] = 0.0
            enhanced_item["peak_volume_percent"] = 0.0
            
            # 调试前5条记录
            if i < 5:
                logger.info(f"热度指数调试 - 公司{i+1}: {item['company_name']} (ID: {item['company_id']}) - 未找到热度记录")
        
        enhanced_results.append(enhanced_item)
    
    logger.info(f"热度指数处理完成: 总计{len(enhanced_results)}条记录，找到{heat_found_count}条热度记录")
    
    return {
        "results": enhanced_results,
        "month": month,
        "total_companies": result["total_companies"],
        "successful_analyses": result["successful_analyses"],
        "failed_analyses": result["failed_analyses"]
    }

@router.get("/analysis/monthly-yoy", response_model=MonthlyYoYAnalysisResponse)
async def get_monthly_yoy_analysis(
    month: Optional[str] = Query(None, description="分析月份，格式YYYY-MM，默认当前月"),
    company_ids: Optional[List[int]] = Query(None, description="公司ID列表，默认全部"),
    db: Session = Depends(get_db)
):
    """获取月度同比分析结果"""
    analysis_service = AnalysisService(db)
    
    # 如果未指定月份，使用当前月份
    if not month:
        month = datetime.now().strftime("%Y-%m")
    
    # 验证月份格式
    try:
        datetime.strptime(month, "%Y-%m")
    except ValueError:
        raise HTTPException(status_code=400, detail="月份格式错误，应为YYYY-MM")
    
    result = analysis_service.get_monthly_yoy_results(month, company_ids)
    
    return MonthlyYoYAnalysisResponse(
        results=result["results"],
        month=month,
        total_companies=result["total_companies"],
        successful_analyses=result["successful_analyses"],
        failed_analyses=result["failed_analyses"]
    )

@router.post("/analysis/calculate-monthly", response_model=TaskResponse)
async def calculate_monthly_analysis(
    request: CalculateMonthlyRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """手动触发月度同比计算任务"""
    analysis_service = AnalysisService(db)
    
    # 生成任务ID
    task_id = f"monthly_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # 添加后台任务
    background_tasks.add_task(
        analysis_service.calculate_monthly_yoy_analysis,
        request.month,
        request.company_ids,
        task_id
    )
    
    return TaskResponse(
        task_id=task_id,
        status="started",
        message="月度同比分析任务已开始"
    )

@router.get("/analysis/status/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    # 这里可以实现任务状态查询逻辑
    # 简化版本，实际应用中可以使用Redis或数据库存储任务状态
    return {
        "task_id": task_id,
        "status": "completed",
        "message": "任务已完成"
    }

@router.get("/export/monthly-csv")
async def export_monthly_csv(
    month: Optional[str] = Query(None, description="月份，格式YYYY-MM"),
    analysis_type: str = Query("mom", description="分析类型：mom环比，yoy同比"),
    company_ids: Optional[List[int]] = Query(None, description="公司ID列表"),
    db: Session = Depends(get_db)
):
    """导出月度分析CSV结果"""
    analysis_service = AnalysisService(db)
    
    if not month:
        month = datetime.now().strftime("%Y-%m")
    
    print(f"CSV导出参数: month={month}, analysis_type={analysis_type}")  # 调试信息
    
    # 获取分析结果
    if analysis_type == "mom":
        print("使用环比分析")
        result = analysis_service.get_monthly_mom_results(month, company_ids)
        # 环比分析表头
        headers = [
            "公司名称", 
            "分析月份", 
            "当前月提及数", 
            "上月提及数", 
            "月度环比变化", 
            "状态"
        ]
    else:
        print("使用同比分析")
        result = analysis_service.get_monthly_yoy_results(month, company_ids)
        # 同比分析表头
        headers = [
            "公司名称", 
            "分析月份", 
            "当前月提及数", 
            "去年同月提及数", 
            "月度同比变化", 
            "状态"
        ]
    
    print(f"分析结果数量: {len(result['results'])}")
    
    # 创建CSV内容
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 写入表头
    writer.writerow(headers)
    
    # 写入数据
    for item in result["results"]:
        if analysis_type == "mom":
            writer.writerow([
                item["company_name"],
                item["analysis_month"],
                item["current_month_mentions"] or 0,
                item["previous_month_mentions"] or 0,
                item["formatted_change"],
                item["status"]
            ])
        else:
            writer.writerow([
                item.company_name,
                item.analysis_month,
                item.current_month_mentions or 0,
                item.previous_year_mentions or 0,
                item.formatted_change,
                item.status
            ])
    
    # 准备响应
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=monthly_{analysis_type}_analysis_{month}.csv"
        }
    )

@router.get("/export/monthly-range-csv")
async def export_monthly_range_csv(
    months: int = Query(6, description="导出近几个月的数据"),
    analysis_type: str = Query("mom", description="分析类型：mom环比，yoy同比"),
    company_ids: Optional[List[int]] = Query(None, description="公司ID列表"),
    db: Session = Depends(get_db)
):
    """导出近n个月的月度分析CSV结果"""
    analysis_service = AnalysisService(db)
    
    # 生成近n个月的月份列表
    current_date = datetime.now()
    month_list = []
    for i in range(months):
        target_date = current_date - timedelta(days=30*i)
        month_list.append(target_date.strftime("%Y-%m"))
    
    month_list.reverse()  # 从最早月份开始
    
    # 创建CSV内容
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 写入表头
    if analysis_type == "mom":
        headers = [
            "公司名称", 
            "分析月份", 
            "当前月提及数", 
            "上月提及数", 
            "月度环比变化", 
            "状态"
        ]
    else:
        headers = [
            "公司名称", 
            "分析月份", 
            "当前月提及数", 
            "去年同月提及数", 
            "月度同比变化", 
            "状态"
        ]
    
    writer.writerow(headers)
    
    # 为每个月获取数据并写入
    all_results = []
    for month in month_list:
        try:
            if analysis_type == "mom":
                result = analysis_service.get_monthly_mom_results(month, company_ids)
            else:
                result = analysis_service.get_monthly_yoy_results(month, company_ids)
            
            # 添加月份标识，用于区分数据来源
            for item in result["results"]:
                if analysis_type == "mom":
                    writer.writerow([
                        item["company_name"],
                        item["analysis_month"],
                        item["current_month_mentions"] or 0,
                        item["previous_month_mentions"] or 0,
                        item["formatted_change"],
                        item["status"]
                    ])
                else:
                    writer.writerow([
                        item.company_name,
                        item.analysis_month,
                        item.current_month_mentions or 0,
                        item.previous_year_mentions or 0,
                        item.formatted_change,
                        item.status
                    ])
        except Exception as e:
            print(f"获取{month}数据失败: {str(e)}")
            continue
    
    # 准备响应
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=monthly_{analysis_type}_analysis_{months}months.csv"
        }
    )

@router.get("/automation/status", response_model=AutomationStatus)
async def get_automation_status(db: Session = Depends(get_db)):
    """获取自动化任务状态"""
    scheduler_service = SchedulerService(db)
    status = scheduler_service.get_automation_status()
    
    return AutomationStatus(
        next_run=status.get("next_run"),
        last_run=status.get("last_run"),
        enabled=status.get("enabled", True),
        total_tasks=status.get("total_tasks", 0),
        active_tasks=status.get("active_tasks", 0)
    )

@router.post("/automation/enable")
async def enable_automation(db: Session = Depends(get_db)):
    """启用自动化任务"""
    scheduler_service = SchedulerService(db)
    scheduler_service.enable_automation()
    
    return {"message": "自动化任务已启用"}

@router.post("/automation/disable")
async def disable_automation(db: Session = Depends(get_db)):
    """禁用自动化任务"""
    scheduler_service = SchedulerService(db)
    scheduler_service.disable_automation()
    
    return {"message": "自动化任务已禁用"}

# ===== 热度指数相关API =====

@router.post("/analysis/calculate-heat-index")
async def calculate_heat_index(
    background_tasks: BackgroundTasks,
    year: int = Query(..., description="年份"),
    month: int = Query(..., description="月份（1-12）"),
    company_ids: Optional[List[int]] = Query(None, description="公司ID列表，默认全部"),
    db: Session = Depends(get_db)
):
    """计算指定月份的公司热度指数"""
    heat_service = HeatIndexService(db)
    
    # 生成任务ID
    task_id = f"heat_index_{year}_{month:02d}_{datetime.now().strftime('%H%M%S')}"
    
    # 添加后台任务
    background_tasks.add_task(
        heat_service.calculate_monthly_heat_index,
        year, month, company_ids
    )
    
    return {
        "task_id": task_id,
        "status": "started",
        "message": f"热度指数计算任务已开始（{year}-{month:02d}）"
    }

@router.get("/analysis/heat-rankings")
async def get_heat_rankings(
    year_month: str = Query(..., description="年月，格式YYYY-MM"),
    limit: int = Query(50, description="返回排名数量"),
    db: Session = Depends(get_db)
):
    """获取热度排名"""
    heat_service = HeatIndexService(db)
    
    # 验证月份格式
    try:
        datetime.strptime(year_month, "%Y-%m")
    except ValueError:
        raise HTTPException(status_code=400, detail="月份格式错误，应为YYYY-MM")
    
    rankings = heat_service.get_monthly_heat_rankings(year_month, limit)
    
    return {
        "rankings": rankings,
        "year_month": year_month,
        "total_rankings": len(rankings)
    }

@router.get("/analysis/heat-trend/{company_id}")
async def get_heat_trend(
    company_id: int,
    months_back: int = Query(6, description="回溯月份数"),
    db: Session = Depends(get_db)
):
    """获取公司热度趋势"""
    heat_service = HeatIndexService(db)
    
    # 检查公司是否存在
    from ..models import Company
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="公司不存在")
    
    trend_data = heat_service.get_heat_trend(company_id, months_back)
    
    return {
        "company_id": company_id,
        "company_name": company.name,
        "trend_data": trend_data,
        "months_back": months_back
    }

# ===== NewsAPI相关API =====

@router.post("/analysis/newsapi-collect")
async def collect_newsapi_data(
    background_tasks: BackgroundTasks,
    company_ids: Optional[List[int]] = Query(None, description="公司ID列表，默认全部"),
    db: Session = Depends(get_db)
):
    """采集NewsAPI数据（过3个月：2025年7月、8月、9月）"""
    
    # 创建任务ID
    task_id = f"newsapi_collect_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    async def collect_task():
        from ..services.newsapi_data_collection_service import NewsAPIDataCollectionService
        collection_service = NewsAPIDataCollectionService(db)
        
        try:
            result = await collection_service.collect_three_months_data(company_ids)
            logger.info(f"NewsAPI数据采集完成: {result['message']}")
        except Exception as e:
            logger.error(f"NewsAPI数据采集失败: {str(e)}")
    
    # 添加后台任务
    background_tasks.add_task(collect_task)
    
    return {
        "task_id": task_id,
        "status": "started",
        "message": "NewsAPI数据采集任务已开始（目标月份：2025-07, 2025-08, 2025-09）"
    }

@router.get("/analysis/newsapi-test")
async def test_newsapi_connection(db: Session = Depends(get_db)):
    """测试NewsAPI连接"""
    newsapi_service = NewsAPIService()
    
    return await newsapi_service.test_api_connection()

@router.get("/analysis/newsapi-summary")
async def get_newsapi_monthly_summary(
    month: str = Query(..., description="月份，格式YYYY-MM"),
    company_ids: Optional[List[int]] = Query(None, description="公司ID列表"),
    db: Session = Depends(get_db)
):
    """获取NewsAPI月度数据汇总"""
    
    # 验证月份格式
    try:
        datetime.strptime(month, "%Y-%m")
    except ValueError:
        raise HTTPException(status_code=400, detail="月份格式错误，应为YYYY-MM")
    
    # 直接查询NewsAPI数据
    from sqlalchemy import and_
    query = db.query(MonthlyMention).filter(
        MonthlyMention.year_month == month,
        MonthlyMention.data_source == "newsapi"
    )
    
    if company_ids:
        query = query.filter(MonthlyMention.company_id.in_(company_ids))
    
    monthly_data = query.join(Company).all()
    
    results = []
    total_mentions = 0
    
    for mention in monthly_data:
        results.append({
            "company_id": mention.company_id,
            "company_name": mention.company.cleaned_name,
            "mention_count": mention.mention_count,
            "year_month": mention.year_month
        })
        total_mentions += mention.mention_count
    
    return {
        "success": True,
        "month": month,
        "total_companies": len(results),
        "total_mentions": total_mentions,
        "average_mentions": total_mentions / len(results) if results else 0,
        "data_source": "newsapi",
        "results": results
    }

@router.get("/analysis/newsapi-mom")
async def get_newsapi_mom_analysis(
    target_month: str = Query(..., description="目标月份，格式YYYY-MM"),
    company_ids: Optional[List[int]] = Query(None, description="公司ID列表"),
    db: Session = Depends(get_db)
):
    """获取NewsAPI月度环比分析结果"""
    
    # 验证月份格式
    try:
        target_year, target_month_num = map(int, target_month.split("-"))
    except ValueError:
        raise HTTPException(status_code=400, detail="月份格式错误，应为YYYY-MM")
    
    # 计算上一个月
    if target_month_num == 1:
        previous_year = target_year - 1
        previous_month_num = 12
    else:
        previous_year = target_year
        previous_month_num = target_month_num - 1
    
    previous_month = f"{previous_year:04d}-{previous_month_num:02d}"
    
    # 获取要分析的公司
    if company_ids:
        companies = db.query(Company).filter(
            Company.id.in_(company_ids),
            Company.status == "active"
        ).all()
    else:
        companies = db.query(Company).filter(
            Company.status == "active"
        ).all()
    
    results = []
    successful_count = 0
    failed_count = 0
    
    for company in companies:
        try:
            # 获取当前月NewsAPI数据
            current_data = db.query(MonthlyMention).filter(
                and_(
                    MonthlyMention.company_id == company.id,
                    MonthlyMention.year_month == target_month,
                    MonthlyMention.data_source == "newsapi"
                )
            ).first()
            
            # 获取上个月NewsAPI数据
            previous_data = db.query(MonthlyMention).filter(
                and_(
                    MonthlyMention.company_id == company.id,
                    MonthlyMention.year_month == previous_month,
                    MonthlyMention.data_source == "newsapi"
                )
            ).first()
            
            current_mentions = current_data.mention_count if current_data else 0
            previous_mentions = previous_data.mention_count if previous_data else 0
            
            # 计算环比变化
            if previous_mentions == 0:
                if current_mentions == 0:
                    change_percentage = 0.0
                    formatted_change = "0.0%"
                else:
                    change_percentage = 999.0  # 表示无穷大增长
                    formatted_change = "+999.0%"
            else:
                change_percentage = ((current_mentions - previous_mentions) / previous_mentions) * 100
                if change_percentage > 0:
                    formatted_change = f"+{change_percentage:.1f}%"
                elif change_percentage < 0:
                    formatted_change = f"{change_percentage:.1f}%"
                else:
                    formatted_change = "0.0%"
            
            results.append({
                "company_id": company.id,
                "company_name": company.cleaned_name,
                "analysis_month": target_month,
                "current_month_mentions": current_mentions,
                "previous_month_mentions": previous_mentions,
                "monthly_change_percentage": change_percentage,
                "formatted_change": formatted_change,
                "status": "success",
                "data_source": "newsapi"
            })
            
            successful_count += 1
            
        except Exception as e:
            logger.error(f"计算公司 {company.cleaned_name} NewsAPI环比分析失败: {str(e)}")
            failed_count += 1
            results.append({
                "company_id": company.id,
                "company_name": company.cleaned_name,
                "status": "failed",
                "error": str(e)
            })
    
    return {
        "success": True,
        "target_month": target_month,
        "previous_month": previous_month,
        "total_companies": len(companies),
        "successful_analyses": successful_count,
        "failed_analyses": failed_count,
        "data_source": "newsapi",
        "results": results
    }

@router.get("/analysis/newsapi-three-months")
async def get_newsapi_three_months_comparison(
    company_ids: Optional[List[int]] = Query(None, description="公司ID列表"),
    db: Session = Depends(get_db)
):
    """获取3个月（2025年7、8、9月）的NewsAPI数据对比"""
    
    months = ["2025-07", "2025-08", "2025-09"]
    comparison_data = {}
    
    # 获取每个月的数据
    for month in months:
        query = db.query(MonthlyMention).filter(
            MonthlyMention.year_month == month,
            MonthlyMention.data_source == "newsapi"
        )
        
        if company_ids:
            query = query.filter(MonthlyMention.company_id.in_(company_ids))
        
        monthly_data = query.join(Company).all()
        
        results = []
        total_mentions = 0
        
        for mention in monthly_data:
            results.append({
                "company_id": mention.company_id,
                "company_name": mention.company.cleaned_name,
                "mention_count": mention.mention_count,
                "year_month": mention.year_month
            })
            total_mentions += mention.mention_count
        
        comparison_data[month] = {
            "month": month,
            "total_companies": len(results),
            "total_mentions": total_mentions,
            "average_mentions": total_mentions / len(results) if results else 0,
            "results": results
        }
    
    return {
        "success": True,
        "message": "3个月NewsAPI数据对比完成",
        "target_months": months,
        "data_source": "newsapi",
        "monthly_summaries": comparison_data
    }

