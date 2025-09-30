from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base

class MonthlyMention(Base):
    __tablename__ = "monthly_mentions"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, comment="公司ID")
    year_month = Column(String(7), nullable=False, index=True, comment="年月，格式：YYYY-MM")
    mention_count = Column(Integer, default=0, comment="提及次数")
    data_source = Column(String(20), comment="数据源：gdelt_doc/gdelt_event")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    # 关联关系
    company = relationship("Company", back_populates="monthly_mentions")
    
    def __repr__(self):
        return f"<MonthlyMention(company_id={self.company_id}, year_month='{self.year_month}', count={self.mention_count})>"

class NewsData(Base):
    __tablename__ = "news_data"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, comment="公司ID")
    query_date = Column(DateTime(timezone=True), nullable=False, comment="查询日期")
    time_period = Column(String(50), comment="时间段")
    mention_count = Column(Integer, default=0, comment="提及次数")
    volume_percent = Column(Numeric(5, 2), comment="覆盖率百分比")
    avg_tone = Column(Numeric(8, 4), comment="平均情感倾向")
    articles = Column(Text, comment="相关文章列表（JSON格式）")
    raw_response = Column(Text, comment="原始API响应（JSON格式）")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    # 关联关系
    company = relationship("Company")
    
    def __repr__(self):
        return f"<NewsData(company_id={self.company_id}, mention_count={self.mention_count})>"