from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models import Company, MonthlyMention

logger = logging.getLogger(__name__)

class NewsAPIAnalysisService:
    """NewsAPI分析服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_monthly_mom_analysis(
        self, 
        target_month: str, 
        company_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """计算基于NewsAPI数据的月度环比分析"""
        
        # 验证月份格式
        try:
            target_year, target_month_num = map(int, target_month.split("-"))
        except ValueError:
            raise ValueError("月份格式错误，应为YYYY-MM")
        
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
            companies = self.db.query(Company).filter(
                Company.id.in_(company_ids),
                Company.status == "active"
            ).all()
        else:
            companies = self.db.query(Company).filter(
                Company.status == "active"
            ).all()
        
        results = []
        successful_count = 0
        failed_count = 0
        
        for company in companies:
            try:
                result = self._calculate_company_mom(
                    company, target_month, previous_month
                )
                results.append(result)
                
                if result["status"] == "success":
                    successful_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"计算公司 {company.cleaned_name} 环比分析失败: {str(e)}")
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
            "results": results
        }
    
    def _calculate_company_mom(
        self, 
        company: Company, 
        target_month: str, 
        previous_month: str
    ) -> Dict[str, Any]:
        """计算单个公司的月度环比变化"""
        # 获取当前月NewsAPI数据
        current_data = self.db.query(MonthlyMention).filter(
            and_(
                MonthlyMention.company_id == company.id,
                MonthlyMention.year_month == target_month,
                MonthlyMention.data_source == "newsapi"
            )
        ).first()
        
        # 获取上个月NewsAPI数据
        previous_data = self.db.query(MonthlyMention).filter(
            and_(
                MonthlyMention.company_id == company.id,
                MonthlyMention.year_month == previous_month,
                MonthlyMention.data_source == "newsapi"
            )
        ).first()
        
        current_mentions = current_data.mention_count if current_data else 0
        previous_mentions = previous_data.mention_count if previous_data else 0
        
        # 确保类型正确
        current_mentions = int(current_mentions) if current_mentions is not None else 0
        previous_mentions = int(previous_mentions) if previous_mentions is not None else 0
        
        # 计算环比变化百分比
        change_percentage = self._calculate_percentage_change(
            current_mentions, previous_mentions
        )
        
        return {
            "company_id": company.id,
            "company_name": company.cleaned_name,
            "analysis_month": target_month,
            "current_month_mentions": current_mentions,
            "previous_month_mentions": previous_mentions,
            "monthly_change_percentage": float(change_percentage) if change_percentage else None,
            "formatted_change": self._format_percentage_change(change_percentage),
            "status": "success",
            "data_source": "newsapi"
        }
    
    def _calculate_percentage_change(
        self, 
        current_value: int, 
        previous_value: int
    ) -> Optional[Decimal]:
        """计算百分比变化"""
        if previous_value == 0:
            if current_value == 0:
                return Decimal('0.0')
            else:
                # 如果上月为0，当前月有数据，则为无穷大增长
                return Decimal('999.0')
        
        change = ((current_value - previous_value) / previous_value) * 100
        # 保留1位小数
        return Decimal(str(change)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
    
    def _format_percentage_change(self, percentage: Optional[Decimal]) -> str:
        """格式化百分比变化显示"""
        if percentage is None:
            return "N/A"
        
        value = float(percentage)
        if value > 0:
            return f"+{value:.1f}%"
        elif value < 0:
            return f"{value:.1f}%"
        else:
            return "0.0%"
    
    def get_newsapi_monthly_summary(
        self, 
        month: str, 
        company_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """获取NewsAPI月度数据汇总"""
        
        query = self.db.query(MonthlyMention).filter(
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
    
    def get_three_months_comparison(
        self, 
        company_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """获取3个月（7月、8月、9月）的对比数据"""
        
        months = ["2025-07", "2025-08", "2025-09"]
        comparison_data = {}
        
        for month in months:
            monthly_summary = self.get_newsapi_monthly_summary(month, company_ids)
            comparison_data[month] = monthly_summary
        
        # 计算环比数据
        mom_analyses = []
        
        # 8月与7月对比
        if "2025-08" in comparison_data and "2025-07" in comparison_data:
            august_mom = self.calculate_monthly_mom_analysis("2025-08", company_ids)
            mom_analyses.append(august_mom)
        
        # 9月与8月对比
        if "2025-09" in comparison_data and "2025-08" in comparison_data:
            september_mom = self.calculate_monthly_mom_analysis("2025-09", company_ids)
            mom_analyses.append(september_mom)
        
        return {
            "success": True,
            "message": "3个月NewsAPI数据对比完成",
            "target_months": months,
            "monthly_summaries": comparison_data,
            "mom_analyses": mom_analyses
        }