@echo off
chcp 65001
echo ====================================
echo    AI初创公司新闻监测系统 启动工具
echo ====================================

echo.
echo [1/4] 检查并激活虚拟环境...
if not exist ".venv" (
    echo 创建虚拟环境...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

echo.
echo [2/4] 安装/更新依赖...
pip install fastapi uvicorn[standard] sqlalchemy python-multipart httpx pydantic pydantic-settings pandas openpyxl apscheduler > nul 2>&1

cd frontend
if not exist "node_modules" (
    echo 安装前端依赖...
    npm install > nul 2>&1
)
cd ..

echo.
echo [3/4] 启动后端服务...
cd backend
start "后端服务" cmd /k "python main.py"
cd ..

echo 等待后端服务启动...
timeout /t 8 /nobreak > nul

echo.
echo [4/4] 启动前端服务...
cd frontend
start "前端服务" cmd /k "npm run dev"
cd ..

echo 等待前端服务启动...
timeout /t 10 /nobreak > nul

echo.
echo ====================================
echo       系统启动完成！
echo ====================================
echo 后端服务: http://localhost:8000
echo 前端界面: http://localhost:3001
echo NewsAPI分析: http://localhost:3001/newsapi
echo API文档: http://localhost:8000/api/docs
echo.
echo 正在自动打开浏览器...
timeout /t 2 /nobreak > nul

start http://localhost:3001

echo.
echo 系统已启动完成！
echo 如需停止服务，请关闭相应的命令行窗口
pause
