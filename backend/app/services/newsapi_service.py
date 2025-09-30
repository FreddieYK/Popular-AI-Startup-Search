import httpx
import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

class NewsAPIService:
    """NewsAPI.org API调用服务"""
    
    def __init__(self, api_key: str = "fa8a1799-0089-49f4-beee-dc3a11474140"):
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2"
        self.everything_url = f"{self.base_url}/everything"
        self.timeout = httpx.Timeout(30.0)
        
    async def query_company_mentions(
        self, 
        company_name: str, 
        start_date: datetime, 
        end_date: datetime,
        language: str = "en"
    ) -> Dict[str, Any]:
        """查询公司在指定时间范围内的新闻提及"""
        try:
            # 构建查询参数
            params = {
                "q": f'"{company_name}"',  # 使用引号进行精确匹配
                "from": start_date.strftime("%Y-%m-%d"),
                "to": end_date.strftime("%Y-%m-%d"),
                "language": language,
                "sortBy": "relevancy",
                "pageSize": 100,  # 最大100条
                "apiKey": self.api_key
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.everything_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                return self._process_newsapi_response(data, company_name)
                
        except httpx.TimeoutException:
            logger.error(f"NewsAPI请求超时: {company_name}")
            return self._create_error_response("API请求超时")
        except httpx.HTTPStatusError as e:
            logger.error(f"NewsAPI HTTP错误 {e.response.status_code}: {company_name}")
            if e.response.status_code == 401:
                return self._create_error_response("API密钥无效")
            elif e.response.status_code == 429:
                return self._create_error_response("API请求频率超限")
            else:
                return self._create_error_response(f"API请求失败: {e.response.status_code}")
        except Exception as e:
            logger.error(f"NewsAPI请求异常: {company_name}, {str(e)}")
            return self._create_error_response(f"API请求异常: {str(e)}")
    
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
        batch_size: int = 3  # NewsAPI有更严格的速率限制
    ) -> Dict[str, Dict[str, Any]]:
        """批量查询多个公司的新闻提及"""
        results = {}
        
        # 分批处理以避免过多并发请求
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
            
            # 添加延迟以避免API限流
            await asyncio.sleep(2)  # NewsAPI建议更长的延迟
        
        return results
    
    async def batch_query_monthly_data(
        self,
        company_names: List[str],
        months: List[tuple]  # [(year, month), ...]
    ) -> Dict[str, Dict[str, Any]]:
        """批量查询多个公司多个月份的数据"""
        results = {}
        
        for company_name in company_names:
            company_results = {}
            
            for year, month in months:
                try:
                    monthly_data = await self.get_monthly_mentions(company_name, year, month)
                    month_key = f"{year}-{month:02d}"
                    company_results[month_key] = monthly_data
                    
                    # 每个请求之间添加延迟
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"查询 {company_name} {year}-{month:02d} 数据失败: {str(e)}")
                    month_key = f"{year}-{month:02d}"
                    company_results[month_key] = self._create_error_response(str(e))
            
            results[company_name] = company_results
            
        return results
    
    def _process_newsapi_response(self, data: Dict, company_name: str) -> Dict[str, Any]:
        """处理NewsAPI响应"""
        try:
            if data.get("status") != "ok":
                error_message = data.get("message", "未知错误")
                return self._create_error_response(f"API返回错误: {error_message}")
            
            total_results = data.get("totalResults", 0)
            articles = data.get("articles", [])
            
            # 提取文章基本信息
            article_summary = []
            for article in articles[:10]:  # 只保留前10篇文章的摘要
                article_info = {
                    "title": article.get("title", ""),
                    "source": article.get("source", {}).get("name", ""),
                    "publishedAt": article.get("publishedAt", ""),
                    "url": article.get("url", "")
                }
                article_summary.append(article_info)
            
            return {
                "success": True,
                "company_name": company_name,
                "mention_count": total_results,
                "articles_returned": len(articles),
                "articles_sample": article_summary,
                "raw_response": {
                    "status": data.get("status"),
                    "totalResults": total_results,
                    "articles_count": len(articles)
                }
            }
            
        except Exception as e:
            logger.error(f"处理NewsAPI响应失败: {company_name}, {str(e)}")
            return self._create_error_response(f"响应处理失败: {str(e)}")
    
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
        """测试API连接"""
        try:
            # 使用一个简单的查询测试连接
            test_params = {
                "q": "test",
                "from": datetime.now().strftime("%Y-%m-%d"),
                "to": datetime.now().strftime("%Y-%m-%d"),
                "pageSize": 1,
                "apiKey": self.api_key
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.everything_url, params=test_params)
                response.raise_for_status()
                
                data = response.json()
                
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "message": "NewsAPI连接正常",
                    "api_status": data.get("status", "unknown")
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "NewsAPI连接失败"
            }
    
    def get_api_limits(self) -> Dict[str, Any]:
        """获取API限制信息"""
        return {
            "requests_per_day": 1000,  # 免费版限制
            "requests_per_hour": 100,  # 建议限制
            "max_page_size": 100,
            "timeout_seconds": 30,
            "batch_size": 3,
            "delay_between_requests": 1
        }