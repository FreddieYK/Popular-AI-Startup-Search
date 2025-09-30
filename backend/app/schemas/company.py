from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class CompanyBase(BaseModel):
    name: str = Field(..., description="原始公司名称")
    cleaned_name: str = Field(..., description="清洗后公司名称")
    status: str = Field(default="active", description="监测状态")

class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    cleaned_name: Optional[str] = None
    status: Optional[str] = None

class Company(CompanyBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CompanyListResponse(BaseModel):
    companies: List[Company]
    total: int

class ExcelUploadResponse(BaseModel):
    success: bool
    companies: List[Company]
    errors: List[str] = []
    total_processed: int
    total_added: int
    total_skipped: int