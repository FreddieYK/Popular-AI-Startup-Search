from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import json
import logging
from sqlalchemy.orm import Session

from ..models import Company, MonthlyMention, NewsData
from .newsapi_service import NewsAPIService

logger = logging.getLogger(__name__)

class NewsAPIDataCollectionService:
    """NewsAPI数据采集服务"""
    
    def __init__(self, db: Session, api_key: str = "fa8a1799-0089-49f4-beee-dc3a11474140"):
        self.db = db
        self.newsapi_service = NewsAPIService(api_key)
    
    async def collect_monthly_data(
        self, 
        year: int, 
        month: int, 
        company_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """采集指定月份的NewsAPI数据"""
        # 获取要采集的公司列表
        if company_ids:
            companies = self.db.query(Company).filter(
                Company.id.in_(company_ids),
                Company.status == "active"
            ).all()
        else:
            companies = self.db.query(Company).filter(
                Company.status == "active"
            ).all()
        
        if not companies:
            return {
                "success": False,
                "message": "没有找到需要采集数据的公司",
                "results": []
            }
        
        # 正确获取公司名称列表
        company_names = [str(company.cleaned_name) for company in companies]
        
        # 计算月份范围
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)
        
        # 批量查询NewsAPI数据
        newsapi_results = await self.newsapi_service.batch_query_companies(
            company_names, start_date, end_date
        )
        
        # 处理和存储结果
        results = []
        year_month = f"{year:04d}-{month:02d}"
        
        for company in companies:
            company_name = str(company.cleaned_name)
            newsapi_data = newsapi_results.get(company_name, {})
            
            try:
                # 检查是否已存在该月的NewsAPI数据
                existing = self.db.query(MonthlyMention).filter(
                    MonthlyMention.company_id == company.id,
                    MonthlyMention.year_month == year_month,
                    MonthlyMention.data_source == "newsapi"
                ).first()
                
                mention_count = newsapi_data.get("mention_count", 0)
                
                if existing:
                    # 更新现有记录
                    existing.mention_count = mention_count
                    self.db.commit()
                    
                    results.append({
                        "company_id": company.id,
                        "company_name": company_name,
                        "action": "updated",
                        "mention_count": mention_count,
                        "success": newsapi_data.get("success", False)
                    })
                else:
                    # 创建新记录
                    monthly_mention = MonthlyMention(
                        company_id=company.id,
                        year_month=year_month,
                        mention_count=mention_count,
                        data_source="newsapi"
                    )
                    
                    self.db.add(monthly_mention)
                    self.db.commit()
                    
                    results.append({
                        "company_id": company.id,
                        "company_name": company_name,
                        "action": "created",
                        "mention_count": mention_count,
                        "success": newsapi_data.get("success", False)
                    })
                
                # 存储详细的新闻数据（可选）
                if newsapi_data.get("success") and mention_count > 0:
                    self._save_news_data(company.id, newsapi_data, start_date)
                
            except Exception as e:
                logger.error(f"保存公司 {company_name} NewsAPI数据失败: {str(e)}")
                results.append({
                    "company_id": company.id,
                    "company_name": company_name,
                    "action": "failed",
                    "error": str(e),
                    "success": False
                })
        
        successful_count = sum(1 for r in results if r.get("success", False))
        
        return {
            "success": True,
            "message": f"NewsAPI数据采集完成，成功处理 {successful_count}/{len(results)} 家公司",
            "year_month": year_month,
            "total_companies": len(results),
            "successful_companies": successful_count,
            "results": results
        }
    
    async def collect_three_months_data(
        self, 
        company_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """采集过去3个月的数据（2025年7月、8月、9月）"""
        target_months = [
            (2025, 7),   # 2025年7月
            (2025, 8),   # 2025年8月
            (2025, 9)    # 2025年9月
        ]
        
        results = []
        
        for year, month in target_months:
            try:
                logger.info(f"开始采集 {year}-{month:02d} 的数据...")
                result = await self.collect_monthly_data(year, month, company_ids)
                results.append({
                    "year_month": f"{year:04d}-{month:02d}",
                    "result": result
                })
                
                # 添加延迟以避免API限流
                logger.info(f"完成 {year}-{month:02d} 数据采集，等待2秒...")
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"采集 {year}-{month} NewsAPI数据失败: {str(e)}")
                results.append({
                    "year_month": f"{year:04d}-{month:02d}",
                    "result": {
                        "success": False,
                        "error": str(e)
                    }
                })
        
        successful_months = sum(1 for r in results if r["result"].get("success", False))
        
        return {
            "success": True,
            "message": f"3个月NewsAPI数据采集完成，成功处理 {successful_months}/{len(results)} 个月",
            "total_months": len(results),
            "successful_months": successful_months,
            "target_months": ["2025-07", "2025-08", "2025-09"],
            "results": results
        }
    
    def _save_news_data(self, company_id: int, newsapi_data: Dict, query_date: datetime):
        """保存详细的NewsAPI新闻数据"""
        try:
            news_data = NewsData(
                company_id=company_id,
                query_date=query_date,
                mention_count=newsapi_data.get("mention_count", 0),
                volume_percent=None,  # NewsAPI不提供volume信息
                articles=json.dumps(newsapi_data.get("articles_sample", [])[:10]),  # 只保存前10条
                raw_response=json.dumps(newsapi_data.get("raw_response", {}))
            )
            
            self.db.add(news_data)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"保存NewsAPI新闻数据失败: {str(e)}")
    
    async def calculate_monthly_mom_analysis(
        self,
        company_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """计算基于NewsAPI数据的月度环比分析"""
        # from .newsapi_analysis_service import NewsAPIAnalysisService
        # 
        # analysis_service = NewsAPIAnalysisService(self.db)
        
        # 直接返回数据采集结果，略过分析部分
        return {
            "success": True,
            "message": "NewsAPI数据采集完成，分析功能尚未实现",
            "note": "请先完成数据采集，再创建分析服务"
        }
    
    def get_collection_status(self) -> Dict[str, Any]:
        """获取采集状态统计"""
        try:
            # 统计NewsAPI数据
            total_newsapi_records = self.db.query(MonthlyMention).filter(
                MonthlyMention.data_source == "newsapi"
            ).count()
            
            # 按月份统计
            from sqlalchemy import func
            monthly_stats = self.db.query(
                MonthlyMention.year_month,
                func.count(MonthlyMention.id).label('count'),
                func.sum(MonthlyMention.mention_count).label('total_mentions')
            ).filter(
                MonthlyMention.data_source == "newsapi"
            ).group_by(MonthlyMention.year_month).all()
            
            monthly_data = [
                {
                    "year_month": stat.year_month,
                    "companies_count": stat.count,
                    "total_mentions": stat.total_mentions or 0
                }
                for stat in monthly_stats
            ]
            
            return {
                "success": True,
                "total_newsapi_records": total_newsapi_records,
                "monthly_breakdown": monthly_data,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取NewsAPI采集状态失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }