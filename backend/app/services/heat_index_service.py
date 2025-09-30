from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import json
import logging

from ..models import Company, HeatIndex
from .gdelt_service import GDELTAPIService

logger = logging.getLogger(__name__)

class HeatIndexService:
    """公司热度指数分析服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.gdelt_service = GDELTAPIService()
    
    async def calculate_monthly_heat_index(
        self, 
        year: int, 
        month: int, 
        company_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """计算指定月份的公司热度指数"""
        # 获取要分析的公司列表
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
                "message": "没有找到需要分析的公司",
                "results": []
            }
        
        company_names = [company.cleaned_name for company in companies]  # type: ignore
        
        # 计算月份范围
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)
        
        # 批量查询GDELT热度数据
        heat_results = await self.gdelt_service.batch_query_heat_index(
            company_names, start_date, end_date  # type: ignore
        )
        
        # 处理和存储结果
        results = []
        year_month = f"{year:04d}-{month:02d}"
        
        for company in companies:
            company_name = company.cleaned_name  # type: ignore
            heat_data = heat_results.get(company_name, {})  # type: ignore
            
            try:
                # 检查是否已存在该月的热度数据
                existing = self.db.query(HeatIndex).filter(
                    HeatIndex.company_id == company.id,
                    HeatIndex.year_month == year_month
                ).first()
                
                # 直接使用TimelineVol的原始值
                timelinevol_value = heat_data.get("timelinevol_value", 0.0)
                data_points_count = heat_data.get("data_points_count", 0)
                timeline_data = json.dumps(heat_data.get("timeline_data", []))
                
                if existing:
                    # 更新现有记录
                    existing.heat_index = timelinevol_value  # type: ignore
                    existing.avg_volume_percent = timelinevol_value  # type: ignore
                    existing.peak_volume_percent = 0.0  # type: ignore
                    existing.timeline_data = timeline_data  # type: ignore
                    existing.updated_at = datetime.utcnow()  # type: ignore
                    self.db.commit()
                    
                    results.append({
                        "company_id": company.id,
                        "company_name": company_name,
                        "action": "updated",
                        "timelinevol_value": timelinevol_value,  # 返回TimelineVol值
                        "heat_level": existing.heat_level,
                        "success": heat_data.get("success", False)
                    })
                else:
                    # 创建新记录
                    heat_index_record = HeatIndex(
                        company_id=company.id,
                        year_month=year_month,
                        heat_index=timelinevol_value,  # 直接使用TimelineVol值
                        avg_volume_percent=timelinevol_value,  # 保持兼容性
                        peak_volume_percent=0.0,  # 不再需要峰值
                        timeline_data=timeline_data,
                        data_source="gdelt_timelinevol"
                    )
                    
                    self.db.add(heat_index_record)
                    self.db.commit()
                    
                    results.append({
                        "company_id": company.id,
                        "company_name": company_name,
                        "action": "created",
                        "timelinevol_value": timelinevol_value,  # 返回TimelineVol值
                        "heat_level": heat_index_record.heat_level,
                        "success": heat_data.get("success", False)
                    })
                
            except Exception as e:
                logger.error(f"保存公司 {company_name} 热度数据失败: {str(e)}")
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
            "message": f"热度指数计算完成，成功处理 {successful_count}/{len(results)} 家公司",
            "year_month": year_month,
            "total_companies": len(results),
            "successful_companies": successful_count,
            "results": results
        }
    
    def get_monthly_heat_rankings(
        self, 
        year_month: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取指定月份的热度排名"""
        query = (
            self.db.query(HeatIndex, Company)
            .join(Company, HeatIndex.company_id == Company.id)
            .filter(HeatIndex.year_month == year_month)
            .order_by(HeatIndex.heat_index.desc())
            .limit(limit)
        )
        
        rankings = []
        for rank, (heat_index, company) in enumerate(query.all(), 1):
            rankings.append({
                "rank": rank,
                "company_id": company.id,
                "company_name": company.name,
                "cleaned_name": company.cleaned_name,
                "heat_index": heat_index.heat_index,
                "heat_level": heat_index.heat_level,
                "avg_volume_percent": heat_index.avg_volume_percent,
                "peak_volume_percent": heat_index.peak_volume_percent,
                "calculated_at": heat_index.calculated_at
            })
        
        return rankings
    
    def get_heat_trend(
        self, 
        company_id: int,
        months_back: int = 6
    ) -> List[Dict[str, Any]]:
        """获取公司的热度趋势"""
        # 计算起始月份
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months_back * 30)
        
        query = (
            self.db.query(HeatIndex)
            .filter(
                HeatIndex.company_id == company_id,
                HeatIndex.calculated_at >= start_date
            )
            .order_by(HeatIndex.year_month.asc())
        )
        
        trend_data = []
        for heat_index in query.all():
            trend_data.append({
                "year_month": heat_index.year_month,
                "heat_index": heat_index.heat_index,
                "heat_level": heat_index.heat_level,
                "avg_volume_percent": heat_index.avg_volume_percent,
                "peak_volume_percent": heat_index.peak_volume_percent,
                "calculated_at": heat_index.calculated_at
            })
        
        return trend_data