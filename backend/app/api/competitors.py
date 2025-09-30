from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from typing import Dict, List
import pandas as pd
import os
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/top40-competitors")
async def get_top40_competitors() -> Dict:
    """
    获取前四十竞争对手数据（基于Excel文件）
    """
    try:
        # Excel文件路径（相对于项目根目录）
        excel_file = os.path.join("..", "北美基金投资策略_项目列表_项目列表.xlsx")
        
        if not os.path.exists(excel_file):
            raise HTTPException(
                status_code=404,
                detail="Excel文件不存在"
            )
        
        # 读取前四十竞争对手数据
        df = pd.read_excel(excel_file, sheet_name='前四十竞争对手')
        
        # 转换为列表格式
        competitors_data = []
        
        # 读取去重后公司信息表以获取投资方信息
        try:
            df_company_info = pd.read_excel(excel_file, sheet_name='去重后公司信息')
            investor_info_map = {}
            if 'Company' in df_company_info.columns and 'Investor Names' in df_company_info.columns:
                company_records = df_company_info.to_dict('records')
                for record in company_records:
                    company_name = str(record.get('Company', '')).strip() if pd.notna(record.get('Company', '')) else ""
                    investor_names = str(record.get('Investor Names', '')).strip() if pd.notna(record.get('Investor Names', '')) else ""
                    if company_name and investor_names:
                        investor_info_map[company_name.lower()] = investor_names
        except Exception as e:
            logger.warning(f"读取去重后公司信息表失败: {str(e)}")
            investor_info_map = {}
        
        # 读取项目列表以进行重合检测
        try:
            df_projects = pd.read_excel(excel_file, sheet_name='项目列表')
            project_companies = set()
            if 'Company' in df_projects.columns:
                project_companies = set(df_projects['Company'].dropna().str.lower().str.strip())
        except Exception as e:
            logger.warning(f"读取项目列表失败: {str(e)}")
            project_companies = set()
        
        # 转换为dict列表以避免类型问题
        records = df.to_dict('records')
        
        for idx, record in enumerate(records):
            try:
                # 解析竞争对手列表
                competitor_value = record.get('competitor', '')
                competitors_str = str(competitor_value) if pd.notna(competitor_value) else ""
                competitors_list = [comp.strip() for comp in competitors_str.split(',') if comp.strip()]
                
                # 检测竞争对手中是否有与项目列表重合的公司
                competitors_with_overlap = []
                for comp in competitors_list:
                    comp_lower = comp.lower().strip()
                    is_overlap = comp_lower in project_companies
                    investor_info = investor_info_map.get(comp_lower, "") if is_overlap else ""
                    
                    competitors_with_overlap.append({
                        "name": comp,
                        "is_overlap": is_overlap,
                        "investor_info": investor_info
                    })
                
                # 安全获取字段值
                company = str(record.get('Company', '')) if pd.notna(record.get('Company', '')) else ""
                core_business = str(record.get('Core Business', '')) if pd.notna(record.get('Core Business', '')) else ""
                industry = str(record.get('所处行业', '')) if pd.notna(record.get('所处行业', '')) else ""
                
                competitor_info = {
                    "rank": idx + 1,
                    "company": company,
                    "core_business": core_business,
                    "industry": industry,
                    "competitors": competitors_with_overlap,
                    "competitors_count": len(competitors_list)
                }
                
                competitors_data.append(competitor_info)
            except Exception as e:
                logger.warning(f"处理第{idx+1}行数据时出错: {str(e)}")
                continue
        
        return {
            "success": True,
            "message": f"成功获取前{len(competitors_data)}名公司竞争对手数据",
            "total_companies": len(competitors_data),
            "data_source": "手动整理Excel文件",
            "data": competitors_data
        }
        
    except Exception as e:
        logger.error(f"获取前四十竞争对手数据失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取竞争对手数据失败: {str(e)}"
        )

@router.get("/competitor-details/{company_name}")
async def get_competitor_details(company_name: str) -> Dict:
    """
    获取指定公司的竞争对手详情
    """
    try:
        # Excel文件路径（相对于项目根目录）
        excel_file = os.path.join("..", "北美基金投资策略_项目列表_项目列表.xlsx")
        
        if not os.path.exists(excel_file):
            raise HTTPException(
                status_code=404,
                detail="Excel文件不存在"
            )
        
        # 读取前四十竞争对手数据
        df = pd.read_excel(excel_file, sheet_name='前四十竞争对手')
        
        # 查找指定公司
        matching_rows = df[df['Company'].astype(str).str.contains(company_name, case=False, na=False)]
        
        if matching_rows.empty:
            return {
                "success": False,
                "message": f"未找到公司 {company_name} 的竞争对手信息",
                "data": None
            }
        
        # 获取第一个匹配的公司信息，转换为dict
        row_dict = matching_rows.iloc[0].to_dict()
        
        competitor_value = row_dict.get('competitor', '')
        competitors_str = str(competitor_value) if pd.notna(competitor_value) else ""
        competitors_list = [comp.strip() for comp in competitors_str.split(',') if comp.strip()]
        
        result = {
            "company": str(row_dict.get('Company', '')) if pd.notna(row_dict.get('Company', '')) else "",
            "core_business": str(row_dict.get('Core Business', '')) if pd.notna(row_dict.get('Core Business', '')) else "",
            "industry": str(row_dict.get('所处行业', '')) if pd.notna(row_dict.get('所处行业', '')) else "",
            "competitors": competitors_list,
            "competitors_count": len(competitors_list)
        }
        
        return {
            "success": True,
            "message": f"成功获取 {company_name} 的竞争对手信息",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"获取公司 {company_name} 竞争对手详情失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取竞争对手详情失败: {str(e)}"
        )

@router.get("/investor-info/{company_name}")
async def get_investor_info(company_name: str) -> Dict:
    """
    获取指定公司的投资方信息
    """
    try:
        # Excel文件路径（相对于项目根目录）
        excel_file = os.path.join("..", "北美基金投资策略_项目列表_项目列表.xlsx")
        
        if not os.path.exists(excel_file):
            raise HTTPException(
                status_code=404,
                detail="Excel文件不存在"
            )
        
        # 读取去重后公司信息数据
        df = pd.read_excel(excel_file, sheet_name='去重后公司信息')
        
        # 查找指定公司
        matching_rows = df[df['Company'].astype(str).str.contains(company_name, case=False, na=False)]
        
        if matching_rows.empty:
            return {
                "success": False,
                "message": f"未找到公司 {company_name} 的投资方信息",
                "data": None
            }
        
        # 获取第一个匹配的公司信息，转换为dict
        row_dict = matching_rows.iloc[0].to_dict()
        
        investor_names = str(row_dict.get('Investor Names', '')) if pd.notna(row_dict.get('Investor Names', '')) else ""
        
        result = {
            "company": str(row_dict.get('Company', '')) if pd.notna(row_dict.get('Company', '')) else "",
            "investor_names": investor_names,
            "core_business": str(row_dict.get('Core Business', '')) if pd.notna(row_dict.get('Core Business', '')) else "",
            "investment_area": str(row_dict.get('Investment Area', '')) if pd.notna(row_dict.get('Investment Area', '')) else ""
        }
        
        return {
            "success": True,
            "message": f"成功获取 {company_name} 的投资方信息",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"获取公司 {company_name} 竞争对手详情失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取竞争对手详情失败: {str(e)}"
        )