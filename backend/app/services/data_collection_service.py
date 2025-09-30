from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import json
import logging

from ..models import Company, MonthlyMention, NewsData
from .gdelt_service import GDELTAPIService

logger = logging.getLogger(__name__)

class DataCollectionService:
    """数据采集服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.gdelt_service = GDELTAPIService()
    
    async def collect_monthly_data(
        self, 
        year: int, 
        month: int, 
        company_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """采集指定月份的数据"""
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
        
        company_names = [company.cleaned_name for company in companies]
        
        # 计算月份范围
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)
        
        # 批量查询GDELT数据
        gdelt_results = await self.gdelt_service.batch_query_companies(
            company_names, start_date, end_date
        )
        
        # 处理和存储结果
        results = []
        year_month = f"{year:04d}-{month:02d}"
        
        for company in companies:
            company_name = company.cleaned_name
            gdelt_data = gdelt_results.get(company_name, {})
            
            try:
                # 检查是否已存在该月的数据
                existing = self.db.query(MonthlyMention).filter(
                    MonthlyMention.company_id == company.id,
                    MonthlyMention.year_month == year_month
                ).first()
                
                mention_count = gdelt_data.get("mention_count", 0)
                
                if existing:
                    # 更新现有记录
                    existing.mention_count = mention_count
                    existing.data_source = "gdelt_doc"
                    self.db.commit()
                    
                    results.append({
                        "company_id": company.id,
                        "company_name": company_name,
                        "action": "updated",
                        "mention_count": mention_count,
                        "success": gdelt_data.get("success", False)
                    })
                else:
                    # 创建新记录
                    monthly_mention = MonthlyMention(
                        company_id=company.id,
                        year_month=year_month,
                        mention_count=mention_count,
                        data_source="gdelt_doc"
                    )
                    
                    self.db.add(monthly_mention)
                    self.db.commit()
                    
                    results.append({
                        "company_id": company.id,
                        "company_name": company_name,
                        "action": "created",
                        "mention_count": mention_count,
                        "success": gdelt_data.get("success", False)
                    })
                
                # 存储详细的新闻数据（可选）
                if gdelt_data.get("success") and mention_count > 0:
                    self._save_news_data(company.id, gdelt_data, start_date)
                
            except Exception as e:
                logger.error(f"保存公司 {company_name} 数据失败: {str(e)}")
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
            "message": f"数据采集完成，成功处理 {successful_count}/{len(results)} 家公司",
            "year_month": year_month,
            "total_companies": len(results),
            "successful_companies": successful_count,
            "results": results
        }
    
    def _save_news_data(self, company_id: int, gdelt_data: Dict, query_date: datetime):
        """保存详细的新闻数据"""
        try:
            news_data = NewsData(
                company_id=company_id,
                query_date=query_date,
                mention_count=gdelt_data.get("mention_count", 0),
                volume_percent=gdelt_data.get("volume_percent", 0.0),
                articles=json.dumps(gdelt_data.get("timeline", [])[:10]),  # 只保存前10条
                raw_response=json.dumps(gdelt_data.get("raw_response", {}))
            )
            
            self.db.add(news_data)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"保存新闻数据失败: {str(e)}")
    
    async def collect_current_month_data(self, company_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """采集当前月份的数据"""
        now = datetime.now()
        return await self.collect_monthly_data(now.year, now.month, company_ids)
    
    async def collect_historical_data(
        self, 
        months_back: int = 12, 
        company_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """采集历史数据"""
        results = []
        now = datetime.now()
        
        for i in range(months_back):
            target_date = now - timedelta(days=30 * i)
            year = target_date.year
            month = target_date.month
            
            try:
                result = await self.collect_monthly_data(year, month, company_ids)
                results.append({
                    "year_month": f"{year:04d}-{month:02d}",
                    "result": result
                })
                
                # 添加延迟以避免API限流
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"采集 {year}-{month} 数据失败: {str(e)}")
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
            "message": f"历史数据采集完成，成功处理 {successful_months}/{len(results)} 个月",
            "total_months": len(results),
            "successful_months": successful_months,
            "results": results
        }
    
    def get_collection_status(self) -> Dict[str, Any]:
        """获取数据采集状态"""
        # 获取最近的数据记录
        latest_record = self.db.query(MonthlyMention).order_by(
            MonthlyMention.created_at.desc()
        ).first()
        
        # 统计总体数据
        total_records = self.db.query(MonthlyMention).count()
        total_companies = self.db.query(Company).filter(Company.status == "active").count()
        
        # 统计最近一个月的数据
        now = datetime.now()
        current_month = f"{now.year:04d}-{now.month:02d}"
        current_month_records = self.db.query(MonthlyMention).filter(
            MonthlyMention.year_month == current_month
        ).count()
        
        return {
            "total_records": total_records,
            "total_companies": total_companies,
            "current_month_records": current_month_records,
            "latest_record_time": latest_record.created_at if latest_record else None,
            "coverage_percentage": (current_month_records / total_companies * 100) if total_companies > 0 else 0
        }