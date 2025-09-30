from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class MonthlyYoYResultBase(BaseModel):
    company_id: int
    company_name: str
    analysis_month: str = Field(..., description="分析月份，格式：YYYY-MM")
    current_month_mentions: Optional[int] = None
    previous_year_mentions: Optional[int] = None
    monthly_change_percentage: Optional[Decimal] = None
    status: str = "success"

class MonthlyYoYResult(MonthlyYoYResultBase):
    id: int
    created_at: datetime
    formatted_change: str = Field(..., description="格式化的变化百分比")
    
    class Config:
        from_attributes = True

class MonthlyYoYAnalysisResponse(BaseModel):
    results: List[MonthlyYoYResult]
    month: str
    total_companies: int
    successful_analyses: int
    failed_analyses: int

class CalculateMonthlyRequest(BaseModel):
    month: Optional[str] = Field(None, description="分析月份，格式：YYYY-MM，默认当前月")
    company_ids: Optional[List[int]] = Field(None, description="公司ID列表，默认全部")

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str

class AutomationStatus(BaseModel):
    next_run: Optional[str] = None
    last_run: Optional[str] = None
    enabled: bool = True
    total_tasks: int = 0
    active_tasks: int = 0