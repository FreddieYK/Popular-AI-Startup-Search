import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
import random

logger = logging.getLogger(__name__)

class NewsAPIMockService:
    """NewsAPI模拟服务 - 用于演示和测试"""
    
    def __init__(self, api_key: str = "mock_key"):
        self.api_key = api_key
        self.timeout = 30.0
        
    async def query_company_mentions(
        self, 
        company_name: str, 
        start_date: datetime, 
        end_date: datetime,
        language: str = "en"
    ) -> Dict[str, Any]:
        """模拟查询公司在指定时间范围内的新闻提及"""
        
        # 模拟API延迟
        await asyncio.sleep(0.5)
        
        # 基于公司名称和日期生成模拟数据
        days_diff = (end_date - start_date).days + 1
        
        # 模拟不同公司的不同热度
        company_multipliers = {
            "OpenAI": 100,
            "Anthropic": 50,
            "DeepMind": 40,
            "Cohere": 20,
            "Hugging Face": 30,
            "Stability AI": 25,
            "Midjourney": 35,
            "Runway": 15,
            "Character.AI": 20,
            "Perplexity": 25
        }
        
        base_mentions = company_multipliers.get(company_name, 10)
        
        # 添加随机因子（模拟新闻事件的影响）
        random_factor = random.uniform(0.5, 2.0)
        total_mentions = int(base_mentions * random_factor * (days_diff / 30))
        
        # 生成模拟文章样本
        sample_articles = self._generate_sample_articles(company_name, total_mentions)
        
        return {
            "success": True,
            "company_name": company_name,
            "mention_count": total_mentions,
            "articles_returned": min(100, total_mentions),  # NewsAPI限制
            "articles_sample": sample_articles[:10],
            "raw_response": {
                "status": "ok",
                "totalResults": total_mentions,
                "articles_count": min(100, total_mentions),
                "mock_data": True
            }
        }
    
    def _generate_sample_articles(self, company_name: str, total_count: int) -> List[Dict]:
        """生成模拟文章样本"""
        sample_titles = [
            f"{company_name} announces breakthrough in AI technology",
            f"New partnership announced by {company_name}",
            f"{company_name} raises funding for AI development",
            f"Industry experts discuss {company_name}'s latest innovation",
            f"{company_name} expands team with key hires",
            f"Market analysis: {company_name}'s growth trajectory",
            f"{company_name} addresses AI safety concerns",
            f"Competition heats up as {company_name} launches new product"
        ]
        
        sample_sources = [
            "TechCrunch", "Wired", "The Verge", "VentureBeat", 
            "MIT Technology Review", "Forbes", "Bloomberg", "Reuters"
        ]
        
        articles = []
        num_samples = min(10, total_count)
        
        for i in range(num_samples):
            article = {
                "title": random.choice(sample_titles),
                "source": {"name": random.choice(sample_sources)},
                "publishedAt": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
                "url": f"https://example.com/article-{i+1}",
                "description": f"Mock article about {company_name}"
            }
            articles.append(article)
        
        return articles
    
    async def get_monthly_mentions(
        self, 
        company_name: str, 
        year: int, 
        month: int
    ) -> Dict[str, Any]:
        """获取公司在指定月份的新闻提及数据"""
        # 计算月份的开始和结束日期
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)
        
        return await self.query_company_mentions(company_name, start_date, end_date)
    
    async def batch_query_companies(
        self, 
        company_names: List[str], 
        start_date: datetime, 
        end_date: datetime,
        batch_size: int = 3
    ) -> Dict[str, Dict[str, Any]]:
        """批量查询多个公司的新闻提及"""
        results = {}
        
        # 分批处理
        for i in range(0, len(company_names), batch_size):
            batch = company_names[i:i + batch_size]
            
            # 并发请求当前批次
            tasks = [
                self.query_company_mentions(name, start_date, end_date)
                for name in batch
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            for name, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"公司 {name} 查询失败: {str(result)}")
                    results[name] = self._create_error_response(str(result))
                else:
                    results[name] = result
            
            # 模拟API延迟
            await asyncio.sleep(1)
        
        return results
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """创建错误响应"""
        return {
            "success": False,
            "error": error_message,
            "mention_count": 0,
            "articles_returned": 0,
            "articles_sample": [],
            "raw_response": None
        }
    
    async def test_api_connection(self) -> Dict[str, Any]:
        """测试API连接（模拟）"""
        await asyncio.sleep(0.1)  # 模拟网络延迟
        
        return {
            "success": True,
            "status_code": 200,
            "message": "NewsAPI模拟服务连接正常",
            "api_status": "ok",
            "mock_service": True
        }
    
    def get_api_limits(self) -> Dict[str, Any]:
        """获取API限制信息"""
        return {
            "requests_per_day": 1000,  # 模拟免费版限制
            "requests_per_hour": 100,  # 建议限制
            "max_page_size": 100,
            "timeout_seconds": 30,
            "batch_size": 3,
            "delay_between_requests": 1,
            "mock_service": True
        }