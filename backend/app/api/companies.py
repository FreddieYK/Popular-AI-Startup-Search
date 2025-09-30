from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import pandas as pd
import io
from pathlib import Path

from ..core.database import get_db
from ..models import Company
from ..schemas import (
    CompanyCreate, CompanyUpdate, Company as CompanySchema,
    CompanyListResponse, ExcelUploadResponse
)
from ..services.company_service import CompanyService

router = APIRouter()

@router.post("/companies/upload", response_model=ExcelUploadResponse)
async def upload_excel_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传Excel文件并导入公司列表"""
    if not file.filename or not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="只支持Excel文件格式（.xlsx, .xls）")
    
    try:
        # 读取Excel文件内容
        contents = await file.read()
        
        # 使用pandas读取Excel文件
        excel_data = pd.read_excel(io.BytesIO(contents), sheet_name=None)
        
        # 检查可用的工作表，优先使用包含更多公司数据的表
        possible_sheets = ["去重后公司信息", "清洗后公司名", "去重公司名", "公司名", "项目列表"]
        target_sheet = None
        
        for sheet_name in possible_sheets:
            if sheet_name in excel_data:
                target_sheet = sheet_name
                break
        
        if not target_sheet:
            # 如果没有找到标准名称，选择数据最多的工作表
            max_rows = 0
            for sheet_name, df in excel_data.items():
                if df.shape[0] > max_rows:
                    max_rows = df.shape[0]
                    target_sheet = sheet_name
        
        if not target_sheet:
            raise HTTPException(status_code=400, detail="Excel文件中未找到有效的公司数据工作表")
        
        # 获取公司名称数据
        company_df = excel_data[target_sheet]
        
        # 查找包含公司名称的列
        company_column = None
        for col in company_df.columns:
            if any(keyword in str(col).lower() for keyword in ['company', '公司', 'name', '名称']):
                company_column = col
                break
        
        if company_column is None:
            company_column = company_df.columns[0]  # 使用第一列
        
        # 假设第一列或指定列包含公司名称
        company_names = company_df[company_column].dropna().astype(str).unique().tolist()
        # 过滤掉无效的公司名称
        company_names = [name.strip() for name in company_names if name.strip() and name.strip().lower() != 'nan']
        
        if not company_names:
            raise HTTPException(status_code=400, detail="未找到有效的公司名称数据")
        
        # 使用服务层处理公司数据
        company_service = CompanyService(db)
        result = company_service.batch_create_companies(company_names)
        
        return ExcelUploadResponse(
            success=True,
            companies=result["companies"],
            errors=result["errors"],
            total_processed=len(company_names),
            total_added=len(result["companies"]),
            total_skipped=result["skipped_count"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理Excel文件时出错: {str(e)}")

@router.get("/companies", response_model=CompanyListResponse)
async def get_companies(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="状态筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db)
):
    """获取公司列表"""
    company_service = CompanyService(db)
    result = company_service.get_companies(
        page=page, 
        size=size, 
        status=status, 
        search=search
    )
    
    return CompanyListResponse(
        companies=result["companies"],
        total=result["total"]
    )

@router.get("/companies/{company_id}", response_model=CompanySchema)
async def get_company(company_id: int, db: Session = Depends(get_db)):
    """获取单个公司信息"""
    company_service = CompanyService(db)
    company = company_service.get_company(company_id)
    
    if not company:
        raise HTTPException(status_code=404, detail="公司未找到")
    
    return company

@router.put("/companies/{company_id}", response_model=CompanySchema)
async def update_company(
    company_id: int, 
    company_update: CompanyUpdate, 
    db: Session = Depends(get_db)
):
    """更新公司信息"""
    company_service = CompanyService(db)
    company = company_service.update_company(company_id, company_update)
    
    if not company:
        raise HTTPException(status_code=404, detail="公司未找到")
    
    return company

@router.delete("/companies/{company_id}")
async def delete_company(company_id: int, db: Session = Depends(get_db)):
    """删除公司"""
    company_service = CompanyService(db)
    success = company_service.delete_company(company_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="公司未找到")
    
    return {"message": "公司删除成功"}

@router.post("/companies/batch-delete")
async def batch_delete_companies(
    company_ids: List[int], 
    db: Session = Depends(get_db)
):
    """批量删除公司"""
    company_service = CompanyService(db)
    deleted_count = company_service.batch_delete_companies(company_ids)
    
    return {
        "message": f"成功删除 {deleted_count} 家公司",
        "deleted_count": deleted_count
    }