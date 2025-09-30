from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from pathlib import Path

# 导入应用模块
from app.core.config import get_settings
from app.core.database import init_db

# 导入API路由
from app.api.companies import router as companies_router
from app.api.comprehensive import router as comprehensive_router  
from app.api.competitors import router as competitors_router
# from app.api.analysis import router as analysis_router  # 暂时注释掉有问题的模块

# 获取配置
settings = get_settings()

# 创建FastAPI应用
app = FastAPI(
    title="AI初创公司新闻监测系统",
    description="基于GDELT全球数据库的AI领域初创公司新闻监测系统",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(companies_router, prefix="/api", tags=["公司管理"])
app.include_router(comprehensive_router, prefix="/api", tags=["综合排名"])
app.include_router(competitors_router, prefix="/api", tags=["竞争对手分析"])
# app.include_router(analysis_router, prefix="/api", tags=["分析统计"])  # 暂时注释

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "内部服务器错误",
            "message": str(exc),
            "path": str(request.url)
        }
    )

# 健康检查接口
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "AI初创公司新闻监测系统运行正常"}

# 根路径健康检查
@app.get("/")
async def root():
    return {
        "message": "欢迎使用AI初创公司新闻监测系统",
        "docs": "/api/docs",
        "version": "1.0.0",
        "status": "healthy"
    }

# 应用启动事件
@app.on_event("startup")
async def startup_event():
    try:
        # 确保必要的目录存在
        os.makedirs(settings.upload_path, exist_ok=True)
        os.makedirs(settings.export_path, exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        
        # 初始化数据库
        init_db()
        
        print(f"🚀 服务器启动成功")
        print(f"📊 API文档: http://{settings.api_host}:{settings.api_port}/api/docs")
        print(f"🔍 健康检查: http://{settings.api_host}:{settings.api_port}/health")
    except Exception as e:
        print(f"⚠️ 启动警告: {str(e)}")
        # 不要抛出异常，让服务继续运行

if __name__ == "__main__":
    # 支持Railway动态端口分配
    port = int(os.getenv("PORT", settings.api_port))
    host = os.getenv("HOST", settings.api_host)
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=False
    )