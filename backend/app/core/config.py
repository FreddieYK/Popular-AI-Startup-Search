from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache

class Settings(BaseSettings):
    # 数据库配置
    database_url: str = "sqlite:///./news_monitoring.db"
    
    # GDELT API配置
    gdelt_doc_api_url: str = "https://api.gdeltproject.org/api/v2/doc/doc"
    gdelt_event_api_url: str = "https://analysis.gdeltproject.org/module-event-exporter.html"
    
    # API配置
    api_host: str = "0.0.0.0"
    api_port: int = 8003
    api_reload: bool = True
    
    # 跨域配置
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # 日志配置
    log_level: str = "INFO"
    log_file: str = "./logs/app.log"
    
    # 任务调度配置
    enable_scheduler: bool = True
    timezone: str = "Asia/Shanghai"
    
    # 文件路径配置
    export_path: str = "./exports/"
    upload_path: str = "./uploads/"
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()