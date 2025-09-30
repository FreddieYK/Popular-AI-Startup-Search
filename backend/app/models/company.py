from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from ..core.database import Base

class Company(Base):
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, comment="原始公司名称")
    cleaned_name = Column(String(255), nullable=False, index=True, comment="清洗后公司名称")
    status = Column(String(20), default="active", comment="监测状态：active/inactive")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def __repr__(self):
        return f"<Company(id={self.id}, name='{self.cleaned_name}', status='{self.status}')>"