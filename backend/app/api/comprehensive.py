from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from ..core.database import get_db
from ..models.company import Company
from ..models.news_data import MonthlyMention
from ..models.analysis import MonthlyMoMAnalysis
from ..services.newsapi_real_data_service import NewsAPIRealDataService

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/comprehensive/ranking")
async def get_comprehensive_ranking(
    target_month: str = Query(..., description="目标月份，格式YYYY-MM"),
    db: Session = Depends(get_db)
):
    """获取GDELT和NewsAPI双数据源的综合排名分析"""
    
    try:
        # 获取GDELT环比分析数据
        gdelt_data = get_gdelt_ranking_data(db, target_month)
        
        # 获取NewsAPI分析数据
        newsapi_service = NewsAPIRealDataService(db)
        newsapi_result = newsapi_service.get_newsapi_mom_analysis(target_month)
        newsapi_data = newsapi_result.get('results', [])
        
        # 计算综合排名
        comprehensive_ranking = calculate_comprehensive_ranking(gdelt_data, newsapi_data)
        
        # 计算排名变化（相较于上个月）
        ranking_with_changes = calculate_ranking_changes(db, target_month, comprehensive_ranking)
        
        return {
            "success": True,
            "target_month": target_month,
            "total_companies": len(ranking_with_changes),
            "data_sources": ["GDELT", "NewsAPI"],
            "calculation_method": "综合排名分数 = GDELT排名 + NewsAPI排名",
            "results": ranking_with_changes
        }
        
    except Exception as e:
        logger.error(f"获取综合排名失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取综合排名失败: {str(e)}")

def get_gdelt_ranking_data(db: Session, target_month: str) -> List[Dict[str, Any]]:
    """获取GDELT月度环比分析数据（从环比分析表获取，确保数据一致性）"""
    
    try:
        # 直接从环比分析表获取数据，确保与环比分析页面一致
        mom_analyses = db.query(MonthlyMoMAnalysis).join(Company).filter(
            MonthlyMoMAnalysis.analysis_month == target_month,
            Company.status == "active"
        ).all()
        
        results = []
        
        for analysis in mom_analyses:
            results.append({
                "company_id": analysis.company_id,
                "company_name": analysis.company.cleaned_name,
                "current_month_mentions": analysis.current_month_mentions,
                "target_month": target_month
            })
        
        # 按当前月提及数排序
        results.sort(key=lambda x: x["current_month_mentions"], reverse=True)
        
        logger.info(f"从环比分析表获取GDELT数据: {len(results)}条记录")
        return results
        
    except Exception as e:
        logger.error(f"从环比分析表获取GDELT数据失败: {str(e)}")
        # 降级到原始方法
        return get_gdelt_ranking_data_fallback(db, target_month)

def get_gdelt_ranking_data_fallback(db: Session, target_month: str) -> List[Dict[str, Any]]:
    """获取GDELT数据的降级方法（直接查询MonthlyMention表）"""
    
    # 获取所有活跃公司
    companies = db.query(Company).filter(Company.status == "active").all()
    
    results = []
    
    for company in companies:
        try:
            # 获取当前月数据
            current_data = db.query(MonthlyMention).filter(
                MonthlyMention.company_id == company.id,
                MonthlyMention.year_month == target_month,
                MonthlyMention.data_source.in_(["gdelt_doc", "gdelt_event"])
            ).first()
            
            current_mentions = current_data.mention_count if current_data else 0
            
            results.append({
                "company_id": company.id,
                "company_name": company.cleaned_name,
                "current_month_mentions": current_mentions,
                "target_month": target_month
            })
            
        except Exception as e:
            logger.error(f"处理公司 {company.cleaned_name} GDELT数据失败: {str(e)}")
            continue
    
    # 按当前月提及数排序
    results.sort(key=lambda x: x["current_month_mentions"], reverse=True)
    
    logger.info(f"使用降级方法获取GDELT数据: {len(results)}条记录")
    return results

def calculate_proper_ranking(data: List[Dict[str, Any]], mentions_key: str) -> Dict[str, Dict[str, Any]]:
    """计算正确的排名（提及数相同的公司拥有相同排名）"""
    rank_map = {}
    
    for item in data:
        company_name = item["company_name"]
        mentions = item.get(mentions_key, 0)
        
        # 计算排名：有多少公司的提及数比当前公司高
        rank = 1
        for other_item in data:
            other_mentions = other_item.get(mentions_key, 0)
            if other_mentions > mentions:
                rank += 1
        
        rank_map[company_name] = {
            "rank": rank,
            "mentions": mentions
        }
    
    return rank_map

def calculate_comprehensive_ranking(
    gdelt_data: List[Dict[str, Any]], 
    newsapi_data: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """计算综合排名"""
    
    # 使用正确的排名计算方法
    gdelt_rank_map = calculate_proper_ranking(gdelt_data, "current_month_mentions")
    newsapi_rank_map = calculate_proper_ranking(newsapi_data, "current_mentions")
    
    # 获取所有公司名称
    all_companies = set()
    all_companies.update(item["company_name"] for item in gdelt_data)
    all_companies.update(item["company_name"] for item in newsapi_data)
    
    # 计算综合排名
    comprehensive_ranking = []
    
    for company_name in all_companies:
        gdelt_info = gdelt_rank_map.get(company_name)
        newsapi_info = newsapi_rank_map.get(company_name)
        
        # 如果某个数据源没有该公司数据，则给予最大排名+1
        gdelt_rank = gdelt_info["rank"] if gdelt_info else len(gdelt_data) + 1
        newsapi_rank = newsapi_info["rank"] if newsapi_info else len(newsapi_data) + 1
        
        # 综合排名分数 = GDELT排名 + NewsAPI排名
        combined_rank_score = gdelt_rank + newsapi_rank
        
        comprehensive_ranking.append({
            "company_name": company_name,
            "gdelt_mentions": gdelt_info["mentions"] if gdelt_info else 0,
            "gdelt_rank": gdelt_rank,
            "newsapi_mentions": newsapi_info["mentions"] if newsapi_info else 0,
            "newsapi_rank": newsapi_rank,
            "combined_rank_score": combined_rank_score
        })
    
    # 按综合排名分数排序（分数越小排名越好）
    comprehensive_ranking.sort(key=lambda x: x["combined_rank_score"])
    
    # 计算正确的最终排名（分数相同的公司拥有相同排名）
    for item in comprehensive_ranking:
        score = item["combined_rank_score"]
        rank = 1
        
        # 计算有多少公司的综合分数比当前公司低（分数越低排名越高）
        for other_item in comprehensive_ranking:
            if other_item["combined_rank_score"] < score:
                rank += 1
        
        item["final_rank"] = rank
    
    return comprehensive_ranking

@router.get("/comprehensive/stats")
async def get_comprehensive_stats(
    target_month: str = Query(..., description="目标月份，格式YYYY-MM"),
    db: Session = Depends(get_db)
):
    """获取综合排名统计信息"""
    
    try:
        # 获取基本统计
        total_companies = db.query(Company).filter(Company.status == "active").count()
        
        # 获取数据源统计
        gdelt_companies = db.query(MonthlyMention).filter(
            MonthlyMention.year_month == target_month,
            MonthlyMention.data_source.in_(["gdelt_doc", "gdelt_event"]),
            MonthlyMention.mention_count > 0
        ).count()
        
        newsapi_companies = db.query(MonthlyMention).filter(
            MonthlyMention.year_month == target_month,
            MonthlyMention.data_source == "newsapi",
            MonthlyMention.mention_count > 0
        ).count()
        
        return {
            "success": True,
            "target_month": target_month,
            "total_companies": total_companies,
            "gdelt_companies_with_data": gdelt_companies,
            "newsapi_companies_with_data": newsapi_companies,
            "data_sources": ["GDELT", "NewsAPI"],
            "coverage_rate": {
                "gdelt": round(gdelt_companies / total_companies * 100, 1) if total_companies > 0 else 0,
                "newsapi": round(newsapi_companies / total_companies * 100, 1) if total_companies > 0 else 0
            }
        }
        
    except Exception as e:
        logger.error(f"获取综合排名统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")

def calculate_ranking_changes(
    db: Session, 
    target_month: str, 
    current_ranking: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """计算排名变化（相较于上个月）"""
    
    # 计算上个月
    year, month = map(int, target_month.split("-"))
    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1
    
    previous_month = f"{prev_year:04d}-{prev_month:02d}"
    
    try:
        # 获取上个月的GDELT和NewsAPI数据
        prev_gdelt_data = get_gdelt_ranking_data(db, previous_month)
        
        newsapi_service = NewsAPIRealDataService(db)
        prev_newsapi_result = newsapi_service.get_newsapi_mom_analysis(previous_month)
        prev_newsapi_data = prev_newsapi_result.get('results', [])
        
        # 计算上个月的综合排名
        prev_comprehensive_ranking = calculate_comprehensive_ranking(prev_gdelt_data, prev_newsapi_data)
        
        # 创建上个月排名映射
        prev_rank_map = {}
        for item in prev_comprehensive_ranking:
            prev_rank_map[item["company_name"]] = item["final_rank"]
        
        # 为当前排名添加变化信息
        ranking_with_changes = []
        for item in current_ranking:
            company_name = item["company_name"]
            current_rank = item["final_rank"]
            prev_rank = prev_rank_map.get(company_name)
            
            # 计算排名变化
            rank_change = None
            rank_change_direction = None
            
            if prev_rank is not None:
                rank_change = prev_rank - current_rank  # 正数表示上升，负数表示下降
                if rank_change > 0:
                    rank_change_direction = "up"
                elif rank_change < 0:
                    rank_change_direction = "down"
                else:
                    rank_change_direction = "same"
            
            # 添加排名变化信息
            enhanced_item = item.copy()
            enhanced_item.update({
                "previous_rank": prev_rank,
                "rank_change": rank_change,
                "rank_change_direction": rank_change_direction
            })
            
            ranking_with_changes.append(enhanced_item)
        
        return ranking_with_changes
        
    except Exception as e:
        logger.error(f"计算排名变化失败: {str(e)}")
        # 如果计算失败，返回原始数据
        return current_ranking