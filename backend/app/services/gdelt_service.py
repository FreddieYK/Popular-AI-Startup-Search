import httpx
import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from urllib.parse import urlencode

from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class GDELTAPIService:
    """GDELT API调用服务"""
    
    def __init__(self):
        self.doc_api_url = settings.gdelt_doc_api_url
        self.event_api_url = settings.gdelt_event_api_url
        self.timeout = httpx.Timeout(30.0)
        
    async def query_company_heat_index(
        self, 
        company_name: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """查询公司热度指数（使用TimelineVol模式）"""
        try:
            # 构建查询参数，使用TimelineVol模式获取热度比例
            # GDELT API对时间范围有限制，使用预定义的timespan
            days_diff = (end_date - start_date).days
            if days_diff <= 1:
                timespan = "1d"
            elif days_diff <= 7:
                timespan = "1w"
            elif days_diff <= 30:
                timespan = "1month"
            else:
                timespan = "3months"  # 最大支持范围
            
            params = {
                "query": company_name,
                "mode": "timelinevol",  # 使用TimelineVol模式
                "timespan": timespan,
                "format": "json",
                "maxrecords": 1000
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.doc_api_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                return self._process_heat_index_response(data, company_name)
                
        except httpx.TimeoutException:
            logger.error(f"GDELT API请求超时: {company_name}")
            return self._create_heat_error_response("请求超时")
        except httpx.HTTPStatusError as e:
            logger.error(f"GDELT API HTTP错误 {e.response.status_code}: {company_name}")
            return self._create_heat_error_response(f"API请求失败: {e.response.status_code}")
        except Exception as e:
            logger.error(f"GDELT API请求异常: {company_name}, {str(e)}")
            return self._create_heat_error_response(f"API请求异常: {str(e)}")

    async def query_company_mentions(
        self, 
        company_name: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """查询公司在指定时间范围内的新闻提及"""
        try:
            # 构建查询参数
            params = {
                "query": company_name,
                "mode": "timelinevolinfo",
                "timespan": self._format_timespan(start_date, end_date),
                "format": "json",
                "maxrecords": 1000
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.doc_api_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                return self._process_doc_api_response(data, company_name)
                
        except httpx.TimeoutException:
            logger.error(f"GDELT API请求超时: {company_name}")
            return self._create_error_response("API请求超时")
        except httpx.HTTPStatusError as e:
            logger.error(f"GDELT API HTTP错误 {e.response.status_code}: {company_name}")
            return self._create_error_response(f"API请求失败: {e.response.status_code}")
        except Exception as e:
            logger.error(f"GDELT API请求异常: {company_name}, {str(e)}")
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
    
    async def batch_query_heat_index(
        self, 
        company_names: List[str], 
        start_date: datetime, 
        end_date: datetime,
        batch_size: int = 5
    ) -> Dict[str, Dict[str, Any]]:
        """批量查询多个公司的热度指数"""
        results = {}
        
        # 分批处理以避免过多并发请求
        for i in range(0, len(company_names), batch_size):
            batch = company_names[i:i + batch_size]
            
            # 并发请求当前批次
            tasks = [
                self.query_company_heat_index(name, start_date, end_date)
                for name in batch
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            for name, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"公司 {name} 热度指数查询失败: {str(result)}")
                    results[name] = self._create_heat_error_response(str(result))
                else:
                    results[name] = result
            
            # 添加延迟以避免API限流
            await asyncio.sleep(1)
        
        return results

    async def batch_query_companies(
        self, 
        company_names: List[str], 
        start_date: datetime, 
        end_date: datetime,
        batch_size: int = 5
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
            await asyncio.sleep(1)
        
        return results
    
    def _format_timespan(self, start_date: datetime, end_date: datetime) -> str:
        """格式化时间范围为GDELT API需要的格式"""
        start_str = start_date.strftime("%Y%m%d%H%M%S")
        end_str = end_date.strftime("%Y%m%d%H%M%S")
        return f"{start_str}-{end_str}"
    
    def _process_doc_api_response(self, data: Dict, company_name: str) -> Dict[str, Any]:
        """处理GDELT DOC API响应"""
        try:
            if not data or "timeline" not in data:
                return {
                    "success": True,
                    "company_name": company_name,
                    "mention_count": 0,
                    "volume_percent": 0.0,
                    "timeline": [],
                    "raw_response": data
                }
            
            timeline = data.get("timeline", [])
            total_mentions = 0
            total_volume = 0.0
            
            # 聚合时间线数据
            for entry in timeline:
                if isinstance(entry, dict):
                    mentions = entry.get("numarts", 0)
                    volume = entry.get("volumeintensity", 0.0)
                    
                    if isinstance(mentions, (int, float)):
                        total_mentions += int(mentions)
                    
                    if isinstance(volume, (int, float)):
                        total_volume += float(volume)
            
            return {
                "success": True,
                "company_name": company_name,
                "mention_count": total_mentions,
                "volume_percent": total_volume / len(timeline) if timeline else 0.0,
                "timeline": timeline[:100],  # 限制时间线数据大小
                "raw_response": {
                    "timeline_length": len(timeline),
                    "sample_data": timeline[:5] if timeline else []
                }
            }
            
        except Exception as e:
            logger.error(f"处理GDELT API响应失败: {company_name}, {str(e)}")
            return self._create_error_response(f"响应处理失败: {str(e)}")
    
    def _process_heat_index_response(self, data: Dict, company_name: str) -> Dict[str, Any]:
        """处理GDELT TimelineVol API响应，直接返回TimelineVol的原始值"""
        try:
            if not data or "timeline" not in data:
                return {
                    "success": True,
                    "company_name": company_name,
                    "timelinevol_value": 0.0,  # 直接使用TimelineVol值
                    "timeline_data": [],
                    "raw_response": data
                }
            
            timeline = data.get("timeline", [])
            volume_values = []
            
            # TimelineVol模式返回的数据结构
            # 格式: {"timeline": [{"series": "Volume Intensity", "data": [{"date": "...", "value": 0.4608}]}]}
            for timeline_item in timeline:
                if isinstance(timeline_item, dict) and "data" in timeline_item:
                    data_points = timeline_item.get("data", [])
                    for point in data_points:
                        if isinstance(point, dict) and "value" in point:
                            volume_value = point.get("value", 0.0)
                            if isinstance(volume_value, (int, float)):
                                volume_values.append(float(volume_value))
            
            if not volume_values:
                return {
                    "success": True,
                    "company_name": company_name,
                    "timelinevol_value": 0.0,
                    "timeline_data": [],
                    "raw_response": data
                }
            
            # 直接使用平均TimelineVol值作为热度指数
            avg_timelinevol = sum(volume_values) / len(volume_values)
            
            return {
                "success": True,
                "company_name": company_name,
                "timelinevol_value": round(avg_timelinevol, 6),  # 保疙6位小数
                "data_points_count": len(volume_values),
                "timeline_data": timeline[:5],  # 保留样本数据
                "raw_response": {
                    "timeline_length": len(timeline),
                    "data_points_count": len(volume_values),
                    "sample_values": volume_values[:5]
                }
            }
            
        except Exception as e:
            logger.error(f"处理GDELT TimelineVol响应失败: {company_name}, {str(e)}")
            return self._create_heat_error_response(f"响应处理失败: {str(e)}")
    
    def _create_heat_error_response(self, error_message: str) -> Dict[str, Any]:
        """创建热度指数错误响应"""
        return {
            "success": False,
            "error": error_message,
            "timelinevol_value": 0.0,  # 更新为TimelineVol值
            "timeline_data": [],
            "raw_response": None
        }

    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """创建错误响应"""
        return {
            "success": False,
            "error": error_message,
            "mention_count": 0,
            "volume_percent": 0.0,
            "timeline": [],
            "raw_response": None
        }
    
    async def test_api_connection(self) -> Dict[str, Any]:
        """测试API连接"""
        try:
            # 使用一个简单的查询测试连接
            test_params = {
                "query": "test",
                "mode": "timelinevolinfo", 
                "timespan": "1d",
                "format": "json",
                "maxrecords": 1
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.doc_api_url, params=test_params)
                response.raise_for_status()
                
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "message": "API连接正常"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "API连接失败"
            }
    
    def get_api_limits(self) -> Dict[str, Any]:
        """获取API限制信息"""
        return {
            "requests_per_minute": 10,  # GDELT API建议限制
            "max_records_per_request": 1000,
            "timeout_seconds": 30,
            "batch_size": 5
        }