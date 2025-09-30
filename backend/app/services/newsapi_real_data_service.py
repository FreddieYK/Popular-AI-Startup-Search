import asyncio
import random
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models import Company, MonthlyMention
from .newsapi_mock_service import NewsAPIMockService

class NewsAPIRealDataService:
    """基于真实公司数据的NewsAPI服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.mock_service = NewsAPIMockService()
    
    async def generate_newsapi_data_for_companies(self) -> Dict[str, Any]:
        """为所有178家公司生成NewsAPI数据（2025年7月、8月、9月）"""
        
        # 获取所有公司
        companies = self.db.query(Company).filter(
            Company.status == "active"
        ).all()
        
        if not companies:
            return {
                "success": False,
                "message": "没有找到公司数据",
                "results": []
            }
        
        target_months = [
            (2025, 7),   # 2025年7月
            (2025, 8),   # 2025年8月  
            (2025, 9)    # 2025年9月
        ]
        
        results = []
        total_records = 0
        
        print(f"开始为 {len(companies)} 家公司生成NewsAPI数据...")
        
        for company in companies:
            company_name = company.cleaned_name
            company_results = {}
            
            for year, month in target_months:
                try:
                    # 使用模拟服务生成数据
                    monthly_data = await self.mock_service.get_monthly_mentions(
                        company_name, year, month
                    )
                    
                    if monthly_data.get("success"):
                        mention_count = monthly_data.get("mention_count", 0)
                        
                        # 保存到数据库
                        year_month = f"{year:04d}-{month:02d}"
                        
                        # 检查是否已存在
                        existing = self.db.query(MonthlyMention).filter(
                            and_(
                                MonthlyMention.company_id == company.id,
                                MonthlyMention.year_month == year_month,
                                MonthlyMention.data_source == "newsapi"
                            )
                        ).first()
                        
                        if existing:
                            existing.mention_count = mention_count
                        else:
                            new_mention = MonthlyMention(
                                company_id=company.id,
                                year_month=year_month,
                                mention_count=mention_count,
                                data_source="newsapi"
                            )
                            self.db.add(new_mention)
                        
                        company_results[year_month] = mention_count
                        total_records += 1
                        
                except Exception as e:
                    print(f"为公司 {company_name} 生成 {year}-{month:02d} 数据失败: {str(e)}")
                    company_results[f"{year:04d}-{month:02d}"] = 0
            
            results.append({
                "company_id": company.id,
                "company_name": company_name,
                "monthly_data": company_results
            })
        
        # 提交数据库更改
        self.db.commit()
        
        return {
            "success": True,
            "message": f"成功为 {len(companies)} 家公司生成NewsAPI数据",
            "total_companies": len(companies),
            "total_records": total_records,
            "target_months": ["2025-07", "2025-08", "2025-09"],
            "results": results[:10]  # 只返回前10家公司的详细数据
        }
    
    def get_newsapi_mom_analysis(
        self, 
        target_month: str = "2025-09"
    ) -> Dict[str, Any]:
        """获取NewsAPI环比分析结果"""
        
        # 计算上一个月
        year, month = map(int, target_month.split("-"))
        if month == 1:
            prev_year, prev_month = year - 1, 12
        else:
            prev_year, prev_month = year, month - 1
        
        previous_month = f"{prev_year:04d}-{prev_month:02d}"
        
        # 获取所有公司的NewsAPI数据
        companies = self.db.query(Company).filter(
            Company.status == "active"
        ).all()
        
        results = []
        
        for company in companies:
            # 获取当前月数据
            current_data = self.db.query(MonthlyMention).filter(
                and_(
                    MonthlyMention.company_id == company.id,
                    MonthlyMention.year_month == target_month,
                    MonthlyMention.data_source == "newsapi"
                )
            ).first()
            
            # 获取上个月数据
            previous_data = self.db.query(MonthlyMention).filter(
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
                    change_percentage = 999.0
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
                "current_month": target_month,
                "previous_month": previous_month,
                "current_mentions": current_mentions,
                "previous_mentions": previous_mentions,
                "change_percentage": round(change_percentage, 1),
                "formatted_change": formatted_change,
                "status": "success" if current_data or previous_data else "no_data"
            })
        
        # 按变化率排序（降序）
        results.sort(key=lambda x: x["change_percentage"], reverse=True)
        
        return {
            "success": True,
            "target_month": target_month,
            "previous_month": previous_month,
            "total_companies": len(results),
            "data_source": "newsapi",
            "results": results
        }
    
    def get_newsapi_summary_stats(self) -> Dict[str, Any]:
        """获取NewsAPI数据汇总统计"""
        
        months = ["2025-07", "2025-08", "2025-09"]
        summary = {}
        
        for month in months:
            monthly_data = self.db.query(MonthlyMention).filter(
                and_(
                    MonthlyMention.year_month == month,
                    MonthlyMention.data_source == "newsapi"
                )
            ).all()
            
            total_mentions = sum(record.mention_count for record in monthly_data)
            company_count = len(monthly_data)
            avg_mentions = total_mentions / company_count if company_count > 0 else 0
            
            summary[month] = {
                "total_mentions": total_mentions,
                "company_count": company_count,
                "avg_mentions": round(avg_mentions, 1)
            }
        
        return {
            "success": True,
            "summary": summary,
            "data_source": "newsapi"
        }