import os
import pandas as pd
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.models.company import Company
from app.core.database import get_db


class CompetitorService:
    def __init__(self):
        self.excel_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "北美基金投资策略_项目列表_项目列表.xlsx")
        
    def load_company_info(self) -> pd.DataFrame:
        """加载公司详细信息"""
        try:
            df = pd.read_excel(self.excel_file_path, sheet_name='去重后公司信息')
            return df
        except Exception as e:
            print(f"Error loading Excel file: {e}")
            return pd.DataFrame()
    
    def get_company_details(self, company_name: str) -> Optional[Dict]:
        """获取公司的详细信息（支持模糊匹配）"""
        df = self.load_company_info()
        if df.empty:
            return None
            
        # 首先尝试精确匹配
        company_row = df[df['Company'].str.strip().str.lower() == company_name.strip().lower()]
        
        # 如果精确匹配失败，尝试模糊匹配
        if company_row.empty:
            # 模糊匹配：包含关系
            company_row = df[df['Company'].str.lower().str.contains(company_name.strip().lower(), na=False)]
            
            # 如果还是没找到，尝试反向匹配
            if company_row.empty:
                search_term = company_name.strip().lower()
                company_row = df[df['Company'].str.lower().apply(lambda x: search_term in x if pd.notna(x) else False)]
                
                # 最后尝试部分匹配
                if company_row.empty:
                    # 尝试匹配公司名称的第一个词
                    first_word = company_name.split()[0].lower()
                    if len(first_word) >= 3:  # 只有较长的词才做部分匹配
                        company_row = df[df['Company'].str.lower().str.contains(first_word, na=False)]
        
        if company_row.empty:
            print(f"⚠️ 公司 '{company_name}' 在Excel中未找到（包括模糊匹配）")
            return None
            
        # 如果有多个匹配，选择第一个
        row = company_row.iloc[0]
        matched_name = row['Company']
        
        if matched_name.lower() != company_name.lower():
            print(f"🔍 模糊匹配: '{company_name}' -> '{matched_name}'")
        
        return {
            "company_name": matched_name,  # 使用匹配到的名称
            "original_name": company_name,  # 保存原始查询名称
            "core_business": row.get('Core Business', ''),
            "所处行业": row.get('Investment Area', ''),
            "investor_names": row.get('Investor Names', '')
        }
    
    def load_top40_competitors(self) -> List[Dict]:
        """加载前四十竞争对手数据"""
        try:
            df = pd.read_excel(self.excel_file_path, sheet_name='前四十竞争对手')
            
            # 加载项目列表用于重合检测
            project_df = pd.read_excel(self.excel_file_path, sheet_name='项目列表')
            project_companies = set()
            if 'Company' in project_df.columns:
                project_companies = set(project_df['Company'].str.lower().str.strip())
            
            # 加载投资方信息
            investor_df = pd.read_excel(self.excel_file_path, sheet_name='去重后公司信息')
            investor_info_map = {}
            if 'Company' in investor_df.columns and 'Investor Names' in investor_df.columns:
                for _, row in investor_df.iterrows():
                    company_key = str(row['Company']).lower().strip()
                    investor_names = str(row['Investor Names']) if pd.notna(row['Investor Names']) else ""
                    investor_info_map[company_key] = investor_names
            
            result = []
            
            # 按行处理数据
            for _, row in df.iterrows():
                try:
                    rank = int(row['Rank']) if pd.notna(row['Rank']) else 0
                    company = str(row['Company']) if pd.notna(row['Company']) else ""
                    core_business = str(row['Core Business']) if pd.notna(row['Core Business']) else ""
                    industry = str(row['Industry']) if pd.notna(row['Industry']) else ""
                    
                    # 解析竞争对手列表
                    competitors_str = str(row['Competitors']) if pd.notna(row['Competitors']) else ""
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
                    
                    result.append({
                        "rank": rank,
                        "company": company,
                        "core_business": core_business,
                        "industry": industry,
                        "competitors": competitors_with_overlap,
                        "competitors_count": len(competitors_list)
                    })
                    
                except Exception as e:
                    print(f"处理行数据时出错: {e}")
                    continue
            
            return result
            
        except Exception as e:
            print(f"Error loading competitors data: {e}")
            return []
    
    def get_investor_info(self, company_name: str) -> Optional[Dict]:
        """获取公司的投资方信息"""
        try:
            df = pd.read_excel(self.excel_file_path, sheet_name='去重后公司信息')
            
            # 尝试精确匹配
            company_row = df[df['Company'].str.strip().str.lower() == company_name.strip().lower()]
            
            # 如果精确匹配失败，尝试模糊匹配
            if company_row.empty:
                company_row = df[df['Company'].str.lower().str.contains(company_name.strip().lower(), na=False)]
            
            if company_row.empty:
                return None
            
            row = company_row.iloc[0]
            investor_names = str(row['Investor Names']) if pd.notna(row['Investor Names']) else ""
            
            return {
                "company": str(row['Company']),
                "investor_names": investor_names
            }
            
        except Exception as e:
            print(f"Error getting investor info: {e}")
            return None