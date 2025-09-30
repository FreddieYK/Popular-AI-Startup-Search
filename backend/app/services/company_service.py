from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Dict, Optional, Any
import re

from ..models import Company
from ..schemas import CompanyCreate, CompanyUpdate

class CompanyService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_company(self, company_id: int) -> Optional[Company]:
        """获取单个公司"""
        return self.db.query(Company).filter(Company.id == company_id).first()
    
    def get_companies(
        self, 
        page: int = 1, 
        size: int = 20, 
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取公司列表"""
        query = self.db.query(Company)
        
        # 状态筛选
        if status:
            query = query.filter(Company.status == status)
        
        # 搜索功能
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Company.name.ilike(search_pattern),
                    Company.cleaned_name.ilike(search_pattern)
                )
            )
        
        # 计算总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * size
        companies = query.offset(offset).limit(size).all()
        
        return {
            "companies": companies,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }
    
    def create_company(self, company_data: CompanyCreate) -> Company:
        """创建公司"""
        # 检查是否已存在相同的公司名
        existing = self.db.query(Company).filter(
            Company.cleaned_name == company_data.cleaned_name
        ).first()
        
        if existing:
            raise ValueError(f"公司 '{company_data.cleaned_name}' 已存在")
        
        # 创建新公司
        db_company = Company(
            name=company_data.name,
            cleaned_name=company_data.cleaned_name,
            status=company_data.status
        )
        
        self.db.add(db_company)
        self.db.commit()
        self.db.refresh(db_company)
        
        return db_company
    
    def update_company(self, company_id: int, company_update: CompanyUpdate) -> Optional[Company]:
        """更新公司信息"""
        company = self.get_company(company_id)
        if not company:
            return None
        
        # 更新字段
        update_data = company_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(company, field, value)
        
        self.db.commit()
        self.db.refresh(company)
        
        return company
    
    def delete_company(self, company_id: int) -> bool:
        """删除公司"""
        company = self.get_company(company_id)
        if not company:
            return False
        
        self.db.delete(company)
        self.db.commit()
        
        return True
    
    def batch_delete_companies(self, company_ids: List[int]) -> int:
        """批量删除公司"""
        deleted_count = self.db.query(Company).filter(
            Company.id.in_(company_ids)
        ).delete(synchronize_session=False)
        
        self.db.commit()
        return deleted_count
    
    def batch_create_companies(self, company_names: List[str]) -> Dict[str, Any]:
        """批量创建公司"""
        results = {
            "companies": [],
            "errors": [],
            "skipped_count": 0
        }
        
        for name in company_names:
            try:
                # 清洗公司名称
                cleaned_name = self._clean_company_name(name)
                
                if not cleaned_name:
                    results["errors"].append(f"公司名称为空或无效: {name}")
                    continue
                
                # 检查是否已存在
                existing = self.db.query(Company).filter(
                    Company.cleaned_name == cleaned_name
                ).first()
                
                if existing:
                    results["skipped_count"] += 1
                    continue
                
                # 创建新公司
                company_data = CompanyCreate(
                    name=name,
                    cleaned_name=cleaned_name,
                    status="active"
                )
                
                new_company = self.create_company(company_data)
                results["companies"].append(new_company)
                
            except Exception as e:
                results["errors"].append(f"处理公司 '{name}' 时出错: {str(e)}")
        
        return results
    
    def _clean_company_name(self, name: str) -> str:
        """清洗公司名称"""
        if not name or not isinstance(name, str):
            return ""
        
        # 去除首尾空格
        cleaned = name.strip()
        
        # 去除特殊字符，但保留中文、英文、数字、空格和常见标点
        cleaned = re.sub(r'[^\w\s\.\-\(\)（）]', '', cleaned, flags=re.UNICODE)
        
        # 去除多余的空格
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned.strip()
    
    def get_companies_by_names(self, names: List[str]) -> List[Company]:
        """根据名称列表获取公司"""
        return self.db.query(Company).filter(
            Company.cleaned_name.in_(names)
        ).all()
    
    def get_active_companies(self) -> List[Company]:
        """获取所有活跃公司"""
        return self.db.query(Company).filter(
            Company.status == "active"
        ).all()