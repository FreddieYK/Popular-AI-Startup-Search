from .company import Company
from .news_data import MonthlyMention, NewsData
from .analysis import MonthlyYoYAnalysis, MonthlyMoMAnalysis, ScheduledTask
from .heat_index import HeatIndex
from ..core.database import Base

# 为了确保关联关系正确设置，需要在Company模型中添加反向关系
from sqlalchemy.orm import relationship

# 为Company添加反向关系
Company.monthly_mentions = relationship("MonthlyMention", back_populates="company")
Company.heat_indices = relationship("HeatIndex", back_populates="company")

__all__ = [
    "Company",
    "MonthlyMention", 
    "NewsData",
    "MonthlyYoYAnalysis",
    "MonthlyMoMAnalysis",
    "ScheduledTask",
    "HeatIndex",
    "Base"
]