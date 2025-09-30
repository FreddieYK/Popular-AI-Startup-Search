@echo off
echo 启动AI初创公司新闻监测系统...
echo.

echo [1/4] 检查并安装后端依赖...
cd backend
if not exist ".venv" (
    echo 创建虚拟环境...
    python -m venv .venv
)
call .venv\Scripts\activate
pip install -r requirements.txt
echo 后端依赖安装完成！
echo.

echo [2/4] 启动后端服务...
start "AI新闻监测-后端" cmd /k "cd /d %cd% && .venv\Scripts\activate && python main.py"
echo 后端服务正在启动，等待5秒...
timeout /t 5 > nul
echo.

echo [3/4] 检查并安装前端依赖...
cd ..\frontend
call npm install
echo 前端依赖安装完成！
echo.

echo [4/4] 启动前端服务...
start "AI新闻监测-前端" cmd /k "cd /d %cd% && npm run dev"
echo 前端服务正在启动，等待3秒...
timeout /t 3 > nul
echo.

echo 正在打开浏览器...
timeout /t 2 > nul
start http://localhost:5173

echo.
echo ===================================
echo    AI初创公司新闻监测系统已启动！
echo ===================================
echo 前端地址: http://localhost:5173
echo 后端地址: http://localhost:8004
echo API文档: http://localhost:8004/api/docs
echo.
echo 按任意键关闭此窗口...
pause > nul