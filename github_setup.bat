@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo ==========================================
echo       AI项目 GitHub 上传脚本
echo ==========================================
echo.

:: 检查是否已经有Git仓库
if not exist .git (
    echo [1/5] 初始化Git仓库...
    git init
    echo.
) else (
    echo [1/5] Git仓库已存在，跳过初始化
    echo.
)

:: 添加所有文件
echo [2/5] 添加文件到Git暂存区...
git add .
echo.

:: 提交文件
echo [3/5] 提交文件...
set /p commit_message="请输入提交信息 (默认: Initial commit): "
if "!commit_message!"=="" set commit_message=Initial commit
git commit -m "!commit_message!"
echo.

:: 设置远程仓库
echo [4/5] 设置远程仓库...
set remote_url=https://github.com/FreddieYK/Popular-AI-Startup-Search.git
echo 使用仓库地址: !remote_url!

:: 添加远程仓库
git remote add origin !remote_url! 2>nul
if errorlevel 1 (
    echo 远程仓库已存在，尝试更新...
    git remote set-url origin !remote_url!
)
echo.

:: 推送到GitHub
echo [5/5] 推送到GitHub...
git branch -M main
git push -u origin main
echo.

if errorlevel 0 (
    echo ✅ 成功上传到GitHub！
    echo.
    echo 🌟 项目地址: !remote_url!
    echo 📁 已清理的文件类型:
    echo    - 测试文件 (test_*.py)
    echo    - 调试文件 (debug_*.py) 
    echo    - 临时文件 (*.tmp, *.temp)
    echo    - 开发环境文件 (.venv/, .qoder/)
    echo    - 过期文档文件
    echo.
    echo 📋 保留的核心文件:
    echo    - 🚀 启动工具.bat (一键启动脚本)
    echo    - 📦 创建分享包.bat (分享包生成脚本)
    echo    - 📖 README.md (项目说明文档)
    echo    - 📊 功能演示指南.md (使用指南)
    echo    - 📈 Excel数据文件 (项目核心数据)
    echo    - 💻 完整的前后端代码
    echo.
) else (
    echo ❌ 上传失败，请检查网络连接和仓库权限
)

echo 按任意键退出...
pause > nul