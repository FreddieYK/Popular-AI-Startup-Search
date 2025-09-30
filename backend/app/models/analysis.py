from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base

class MonthlyYoYAnalysis(Base):
    __tablename__ = "monthly_yoy_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, comment="公司ID")
    analysis_month = Column(String(7), nullable=False, index=True, comment="分析月份，格式：YYYY-MM")
    current_month_mentions = Column(Integer, comment="当前月提及数")
    previous_year_mentions = Column(Integer, comment="去年同月提及数")
    monthly_change_percentage = Column(Numeric(8, 2), comment="月度同比变化比例")
    status = Column(String(20), default="success", comment="计算状态：success/failed")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    # 关联关系
    company = relationship("Company")
    
    def __repr__(self):
        return f"<MonthlyYoYAnalysis(company_id={self.company_id}, month='{self.analysis_month}', change={self.monthly_change_percentage}%)>"
    
    @property
    def formatted_change(self) -> str:
        """格式化显示变化百分比"""
        if self.monthly_change_percentage is None:
            return "N/A"
        
        percentage = float(self.monthly_change_percentage) if self.monthly_change_percentage is not None else 0.0
        if percentage > 0:
            return f"+{percentage:.1f}%"
        elif percentage < 0:
            return f"{percentage:.1f}%"
        else:
            return "0.0%"

class MonthlyMoMAnalysis(Base):
    """月度环比分析模型"""
    __tablename__ = "monthly_mom_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, comment="公司ID")
    analysis_month = Column(String(7), nullable=False, index=True, comment="分析月份，格式：YYYY-MM")
    current_month_mentions = Column(Integer, comment="当前月提及数")
    previous_month_mentions = Column(Integer, comment="上月提及数")
    monthly_change_percentage = Column(Numeric(8, 2), comment="月度环比变化比例")
    status = Column(String(20), default="success", comment="计算状态：success/failed")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    # 关联关系
    company = relationship("Company")
    
    def __repr__(self):
        return f"<MonthlyMoMAnalysis(company_id={self.company_id}, month='{self.analysis_month}', change={self.monthly_change_percentage}%)>"
    
    @property
    def formatted_change(self) -> str:
        """格式化显示变化百分比"""
        if self.monthly_change_percentage is None:
            return "N/A"
        
        try:
            percentage = float(str(self.monthly_change_percentage)) if self.monthly_change_percentage is not None else 0.0
            if percentage > 0:
                return f"+{percentage:.1f}%"
            elif percentage < 0:
                return f"{percentage:.1f}%"
            else:
                return "0.0%"
        except (ValueError, TypeError):
            return "N/A"

class ScheduledTask(Base):
    __tablename__ = "scheduled_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_type = Column(String(50), nullable=False, comment="任务类型")
    company_ids = Column(String(1000), comment="公司ID列表（JSON格式）")
    schedule_pattern = Column(String(100), comment="调度模式")
    last_run = Column(DateTime(timezone=True), comment="上次运行时间")
    next_run = Column(DateTime(timezone=True), comment="下次运行时间")
    status = Column(String(20), default="active", comment="任务状态：active/inactive")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    def __repr__(self):
        return f"<ScheduledTask(type='{self.task_type}', status='{self.status}')>"