from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from ..core.database import Base

class HeatIndex(Base):
    """公司热度指数表"""
    __tablename__ = "heat_indices"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    year_month = Column(String(7), nullable=False, index=True)  # 格式: 2025-09
    
    # 热度指数相关字段
    heat_index = Column(Float, nullable=False, default=0.0)  # 综合热度指数
    avg_volume_percent = Column(Float, nullable=False, default=0.0)  # 平均占比
    peak_volume_percent = Column(Float, nullable=False, default=0.0)  # 峰值占比
    
    # 元数据
    data_source = Column(String(50), default="gdelt_timelinevol")
    calculated_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 原始响应数据（可选）
    timeline_data = Column(Text, nullable=True)  # JSON格式的时间线数据
    
    # 关联关系
    company = relationship("Company", back_populates="heat_indices")
    
    def __repr__(self):
        return f"<HeatIndex(company_id={self.company_id}, year_month='{self.year_month}', heat_index={self.heat_index})>"
    
    @property
    def heat_level(self) -> str:
        """根据热度指数返回热度等级"""
        if self.heat_index >= 1.0:  # type: ignore
            return "极热"
        elif self.heat_index >= 0.5:  # type: ignore
            return "很热" 
        elif self.heat_index >= 0.2:  # type: ignore
            return "较热"
        elif self.heat_index >= 0.1:  # type: ignore
            return "温热"
        elif self.heat_index > 0:  # type: ignore
            return "微热"
        else:
            return "冷门"
    
    @property
    def formatted_heat_index(self) -> str:
        """格式化的热度指数显示"""
        return f"{self.heat_index:.4f}%"