import pandas as pd
import io
from typing import List, Dict, Any, Optional
from pathlib import Path

class ExcelProcessor:
    """Excel文件处理工具类"""
    
    @staticmethod
    def read_excel_from_bytes(file_content: bytes, sheet_name: str = "清洗后公司名") -> List[str]:
        """从字节内容读取Excel文件并提取公司名称"""
        try:
            # 读取Excel文件的所有工作表
            excel_data = pd.read_excel(io.BytesIO(file_content), sheet_name=None)
            
            # 检查目标工作表是否存在
            if sheet_name not in excel_data:
                available_sheets = list(excel_data.keys())
                raise ValueError(f"未找到工作表 '{sheet_name}'。可用工作表: {available_sheets}")
            
            # 获取目标工作表数据
            df = excel_data[sheet_name]
            
            # 提取第一列的公司名称（假设公司名在第一列）
            if df.empty:
                return []
            
            # 获取第一列数据，去除空值
            company_names = df.iloc[:, 0].dropna().astype(str).tolist()
            
            # 去除空字符串和仅包含空格的值
            company_names = [name.strip() for name in company_names if name.strip()]
            
            # 去重
            unique_names = list(dict.fromkeys(company_names))  # 保持顺序的去重
            
            return unique_names
            
        except Exception as e:
            raise ValueError(f"读取Excel文件失败: {str(e)}")
    
    @staticmethod
    def validate_excel_file(file_content: bytes) -> Dict[str, Any]:
        """验证Excel文件格式和内容"""
        try:
            # 读取所有工作表名称
            excel_data = pd.read_excel(io.BytesIO(file_content), sheet_name=None)
            sheets = list(excel_data.keys())
            
            # 检查是否有目标工作表
            has_target_sheet = "清洗后公司名" in sheets
            
            # 如果有目标工作表，检查数据质量
            data_info = {}
            if has_target_sheet:
                df = excel_data["清洗后公司名"]
                data_info = {
                    "total_rows": len(df),
                    "non_empty_rows": len(df.dropna()),
                    "first_column_name": df.columns[0] if not df.empty else None,
                    "sample_data": df.iloc[:5, 0].tolist() if not df.empty else []
                }
            
            return {
                "valid": True,
                "sheets": sheets,
                "has_target_sheet": has_target_sheet,
                "data_info": data_info,
                "message": "文件验证成功"
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "message": f"文件验证失败: {str(e)}"
            }
    
    @staticmethod
    def export_companies_to_excel(companies: List[Dict], file_path: str) -> bool:
        """将公司数据导出到Excel文件"""
        try:
            df = pd.DataFrame(companies)
            df.to_excel(file_path, index=False, sheet_name="公司列表")
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_supported_formats() -> List[str]:
        """获取支持的文件格式"""
        return [".xlsx", ".xls"]
    
    @staticmethod
    def is_valid_excel_file(filename: str) -> bool:
        """检查文件是否为有效的Excel格式"""
        if not filename:
            return False
        
        file_ext = Path(filename).suffix.lower()
        return file_ext in ExcelProcessor.get_supported_formats()