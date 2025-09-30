from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import logging

from ..models import Company, MonthlyMention, MonthlyYoYAnalysis, MonthlyMoMAnalysis
from ..schemas import MonthlyYoYResult

logger = logging.getLogger(__name__)

class AnalysisService:
    """分析服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_monthly_yoy_analysis(
        self, 
        target_month: Optional[str] = None, 
        company_ids: Optional[List[int]] = None,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """计算月度同比分析"""
        # 确定分析月份
        if not target_month:
            now = datetime.now()
            target_month = f"{now.year:04d}-{now.month:02d}"
        
        # 验证月份格式
        try:
            target_year, target_month_num = map(int, target_month.split("-"))
        except ValueError:
            raise ValueError("月份格式错误，应为YYYY-MM")
        
        # 计算去年同月
        previous_year = target_year - 1
        previous_month = f"{previous_year:04d}-{target_month_num:02d}"
        
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
                result = self._calculate_company_yoy(
                    company, target_month, previous_month
                )
                results.append(result)
                
                if result["status"] == "success":
                    successful_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"计算公司 {company.cleaned_name} 同比分析失败: {str(e)}")
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
            "results": results,
            "task_id": task_id
        }
    
    def _calculate_company_yoy(
        self, 
        company: Company, 
        target_month: str, 
        previous_month: str
    ) -> Dict[str, Any]:
        """计算单个公司的月度同比变化"""
        # 获取当前月数据
        current_data = self.db.query(MonthlyMention).filter(
            and_(
                MonthlyMention.company_id == company.id,
                MonthlyMention.year_month == target_month
            )
        ).first()
        
        # 获取去年同月数据
        previous_data = self.db.query(MonthlyMention).filter(
            and_(
                MonthlyMention.company_id == company.id,
                MonthlyMention.year_month == previous_month
            )
        ).first()
        
        current_mentions = current_data.mention_count if current_data else 0
        previous_mentions = previous_data.mention_count if previous_data else 0
        
        # 计算同比变化百分比
        change_percentage = self._calculate_percentage_change(
            current_mentions, previous_mentions
        )
        
        # 检查是否已存在分析结果
        existing_analysis = self.db.query(MonthlyYoYAnalysis).filter(
            and_(
                MonthlyYoYAnalysis.company_id == company.id,
                MonthlyYoYAnalysis.analysis_month == target_month
            )
        ).first()
        
        if existing_analysis:
            # 更新现有记录
            existing_analysis.current_month_mentions = current_mentions
            existing_analysis.previous_year_mentions = previous_mentions
            existing_analysis.monthly_change_percentage = change_percentage
            existing_analysis.status = "success"
            self.db.commit()
            analysis_record = existing_analysis
        else:
            # 创建新记录
            analysis_record = MonthlyYoYAnalysis(
                company_id=company.id,
                analysis_month=target_month,
                current_month_mentions=current_mentions,
                previous_year_mentions=previous_mentions,
                monthly_change_percentage=change_percentage,
                status="success"
            )
            self.db.add(analysis_record)
            self.db.commit()
        
        return {
            "company_id": company.id,
            "company_name": company.cleaned_name,
            "analysis_month": target_month,
            "current_month_mentions": current_mentions,
            "previous_year_mentions": previous_mentions,
            "monthly_change_percentage": float(change_percentage) if change_percentage else None,
            "formatted_change": self._format_percentage_change(change_percentage),
            "status": "success"
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
                # 如果去年同月为0，当前月有数据，则为无穷大增长
                # 这里使用一个很大的数值表示，比如999%
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
    
    def get_monthly_yoy_results(
        self, 
        month: str, 
        company_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """获取月度同比分析结果"""
        query = self.db.query(MonthlyYoYAnalysis).join(Company).filter(
            MonthlyYoYAnalysis.analysis_month == month
        )
        
        if company_ids:
            query = query.filter(MonthlyYoYAnalysis.company_id.in_(company_ids))
        
        analyses = query.all()
        
        results = []
        successful_count = 0
        failed_count = 0
        
        for analysis in analyses:
            # 构建结果对象
            result = MonthlyYoYResult(
                id=analysis.id,
                company_id=analysis.company_id,
                company_name=analysis.company.cleaned_name,
                analysis_month=analysis.analysis_month,
                current_month_mentions=analysis.current_month_mentions,
                previous_year_mentions=analysis.previous_year_mentions,
                monthly_change_percentage=analysis.monthly_change_percentage,
                status=analysis.status,
                created_at=analysis.created_at,
                formatted_change=analysis.formatted_change
            )
            results.append(result)
            
            if analysis.status == "success":
                successful_count += 1
            else:
                failed_count += 1
        
        # 按变化百分比排序（降序）
        results.sort(
            key=lambda x: float(x.monthly_change_percentage or 0), 
            reverse=True
        )
        
        return {
            "results": results,
            "total_companies": len(results),
            "successful_analyses": successful_count,
            "failed_analyses": failed_count
        }
    
    def get_company_trend_analysis(
        self, 
        company_id: int, 
        months_back: int = 12
    ) -> Dict[str, Any]:
        """获取公司的趋势分析"""
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise ValueError("公司不存在")
        
        # 获取最近N个月的数据
        monthly_data = self.db.query(MonthlyMention).filter(
            MonthlyMention.company_id == company_id
        ).order_by(MonthlyMention.year_month.desc()).limit(months_back).all()
        
        # 获取同比分析数据
        yoy_data = self.db.query(MonthlyYoYAnalysis).filter(
            MonthlyYoYAnalysis.company_id == company_id
        ).order_by(MonthlyYoYAnalysis.analysis_month.desc()).limit(months_back).all()
        
        return {
            "company_id": company_id,
            "company_name": company.cleaned_name,
            "monthly_mentions": [
                {
                    "year_month": data.year_month,
                    "mention_count": data.mention_count,
                    "created_at": data.created_at
                }
                for data in monthly_data
            ],
            "yoy_analysis": [
                {
                    "analysis_month": data.analysis_month,
                    "current_mentions": data.current_month_mentions,
                    "previous_year_mentions": data.previous_year_mentions,
                    "change_percentage": float(data.monthly_change_percentage) if data.monthly_change_percentage else None,
                    "formatted_change": data.formatted_change
                }
                for data in yoy_data
            ]
        }
    
    def get_monthly_mom_results(
        self, 
        month: str, 
        company_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """获取月度环比分析结果"""
        query = self.db.query(MonthlyMoMAnalysis).join(Company).filter(
            MonthlyMoMAnalysis.analysis_month == month
        )
        
        if company_ids:
            query = query.filter(MonthlyMoMAnalysis.company_id.in_(company_ids))
        
        analyses = query.all()
        
        results = []
        successful_count = 0
        failed_count = 0
        
        for analysis in analyses:
            # 构建结果对象
            result = {
                "id": analysis.id,
                "company_id": analysis.company_id,
                "company_name": analysis.company.cleaned_name,
                "analysis_month": analysis.analysis_month,
                "current_month_mentions": analysis.current_month_mentions,
                "previous_month_mentions": analysis.previous_month_mentions,
                "monthly_change_percentage": analysis.monthly_change_percentage,
                "status": analysis.status,
                "created_at": analysis.created_at,
                "formatted_change": analysis.formatted_change
            }
            results.append(result)
            
            if analysis.status == "success":
                successful_count += 1
            else:
                failed_count += 1
        
        # 按变化百分比排序（降序）
        results.sort(
            key=lambda x: float(x["monthly_change_percentage"] or 0), 
            reverse=True
        )
        
        return {
            "results": results,
            "total_companies": len(results),
            "successful_analyses": successful_count,
            "failed_analyses": failed_count
        }