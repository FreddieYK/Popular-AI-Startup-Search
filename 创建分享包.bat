@echo off
chcp 65001 >nul
echo.
echo ================================================
echo      AI初创公司新闻监测系统 - 分享包生成器
echo ================================================
echo.

:: 获取当前日期
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "datestamp=%YYYY%%MM%%DD%"

:: 创建分享包目录
set SHARE_DIR=AI初创公司新闻监测系统_分享包_%datestamp%
echo [1/8] 创建分享包目录: %SHARE_DIR%
if exist "%SHARE_DIR%" (
    echo 正在清理旧的分享包目录...
    rmdir /s /q "%SHARE_DIR%"
)
mkdir "%SHARE_DIR%"
echo [✓] 分享包目录创建完成

:: 复制后端代码
echo [2/8] 复制后端代码...
if exist "backend" (
    xcopy /E /I /Q "backend" "%SHARE_DIR%\backend"
    echo [✓] 后端代码复制完成
) else (
    echo [错误] 未找到backend目录
    goto :error
)

:: 复制前端代码
echo [3/8] 复制前端代码...
if exist "frontend" (
    xcopy /E /I /Q "frontend" "%SHARE_DIR%\frontend"
    :: 排除node_modules目录
    if exist "%SHARE_DIR%\frontend\node_modules" (
        rmdir /s /q "%SHARE_DIR%\frontend\node_modules"
    )
    echo [✓] 前端代码复制完成（已排除node_modules）
) else (
    echo [错误] 未找到frontend目录
    goto :error
)

:: 复制核心配置文件
echo [4/8] 复制配置文件...
copy "requirements.txt" "%SHARE_DIR%\" >nul 2>&1
copy "README.md" "%SHARE_DIR%\" >nul 2>&1
copy ".env" "%SHARE_DIR%\" >nul 2>&1
copy ".gitignore" "%SHARE_DIR%\" >nul 2>&1
copy "启动工具.bat" "%SHARE_DIR%\" >nul 2>&1
echo [✓] 配置文件复制完成

:: 创建示例Excel文件（如果存在）
echo [5/8] 处理示例文件...
if exist "*.xlsx" (
    copy "*.xlsx" "%SHARE_DIR%\示例数据\" >nul 2>&1
    echo [✓] 示例Excel文件已复制
)

:: 创建使用说明文件
echo [6/8] 生成使用说明文件...
(
echo 【AI初创公司新闻监测系统 - 使用说明】
echo.
echo 版本: 1.0.0
echo 构建日期: %YYYY%-%MM%-%DD%
echo.
echo ===============================================
echo 一、系统简介
echo ===============================================
echo 本系统基于GDELT全球数据库，为AI初创公司提供新闻监测和
echo 月度同比分析服务，帮助投资决策者获取准确的市场数据。
echo.
echo ===============================================
echo 二、快速开始
echo ===============================================
echo 1. 运行"启动工具.bat"一键启动系统
echo    - 系统会自动检查环境依赖
echo    - 自动安装所需的Python和Node.js包
echo    - 启动后端和前端服务
echo    - 自动打开浏览器访问界面
echo.
echo 2. 访问系统界面
echo    - 前端界面: http://localhost:3000
echo    - 后端API: http://localhost:8000
echo    - API文档: http://localhost:8000/api/docs
echo.
echo ===============================================
echo 三、系统功能
echo ===============================================
echo 1. 公司管理
echo    - 上传Excel文件批量导入公司列表
echo    - 要求Excel包含"清洗后公司名"工作表
echo    - 支持手动添加、编辑、删除公司
echo.
echo 2. 数据采集
echo    - 自动调用GDELT API获取新闻数据
echo    - 支持手动触发数据采集
echo    - 数据按月度存储和聚合
echo.
echo 3. 同比分析
echo    - 计算月度同比变化百分比
echo    - 公式: （当前月-去年同月）/去年同月 × 100%%
echo    - 支持CSV格式数据导出
echo.
echo 4. 自动化任务
echo    - 每月1日自动执行数据采集（凌晨2点）
echo    - 每月1日自动执行同比分析（早上6点）
echo    - 每月1日自动生成报告（早上8点）
echo.
echo ===============================================
echo 四、环境要求
echo ===============================================
echo 1. Python 3.8+ 
echo    下载地址: https://www.python.org/downloads/
echo.
echo 2. Node.js 16+
echo    下载地址: https://nodejs.org/
echo.
echo 3. 网络连接（用于API调用和包安装）
echo.
echo ===============================================
echo 五、故障排除
echo ===============================================
echo 1. 如果启动失败，请检查：
echo    - Python和Node.js是否正确安装
echo    - 网络连接是否正常
echo    - 防火墙是否阻止了端口访问
echo.
echo 2. 如果包安装失败，可尝试：
echo    - 使用国内镜像源安装依赖
echo    - 检查代理设置
echo.
echo 3. 如果API调用失败，请检查：
echo    - GDELT API是否可访问
echo    - 网络代理设置
echo.
echo ===============================================
echo 六、联系支持
echo ===============================================
echo 如遇到技术问题，请检查README.md文件中的详细说明
echo 或参考API文档获取更多技术细节。
echo.
echo 构建时间: %date% %time%
) > "%SHARE_DIR%\使用说明.txt"
echo [✓] 使用说明文件生成完成

:: 创建快速启动脚本（简化版）
echo [7/8] 创建快速启动脚本...
(
echo @echo off
echo echo 正在启动AI初创公司新闻监测系统...
echo echo.
echo if not exist "backend" ^(
echo     echo [错误] 请确保在项目根目录运行此脚本
echo     pause
echo     exit /b 1
echo ^)
echo.
echo start /min cmd /c "cd backend && python app.py"
echo timeout /t 5 /nobreak ^>nul
echo start /min cmd /c "cd frontend && npm run dev"
echo timeout /t 10 /nobreak ^>nul
echo start http://localhost:3000
echo.
echo echo 系统启动完成！
echo echo 前端: http://localhost:3000
echo echo 后端: http://localhost:8000
echo pause
) > "%SHARE_DIR%\快速启动.bat"
echo [✓] 快速启动脚本创建完成

:: 生成项目信息文件
echo [8/8] 生成项目信息...
(
echo 项目名称: AI初创公司新闻监测系统
echo 版本: 1.0.0
echo 构建日期: %YYYY%-%MM%-%DD%
echo 技术栈: Python FastAPI + React + TypeScript + Ant Design
echo 数据源: GDELT Global Database
echo 主要功能: 新闻监测、月度同比分析、自动化任务调度
echo.
echo 目录结构:
echo ├── backend/          # 后端Python代码
echo ├── frontend/         # 前端React代码
echo ├── requirements.txt  # Python依赖
echo ├── README.md         # 详细说明文档
echo ├── 启动工具.bat      # 一键启动脚本
echo ├── 快速启动.bat      # 简化启动脚本
echo └── 使用说明.txt      # 使用说明文档
) > "%SHARE_DIR%\项目信息.txt"
echo [✓] 项目信息文件生成完成

echo.
echo ================================================
echo              分享包创建成功！
echo ================================================
echo.
echo 分享包位置: %SHARE_DIR%
echo 包含内容:
echo   ✓ 完整的源代码（后端 + 前端）
echo   ✓ 依赖配置文件
echo   ✓ 一键启动脚本
echo   ✓ 详细使用说明
echo   ✓ 项目文档
echo.
echo 使用方法:
echo 1. 将整个"%SHARE_DIR%"文件夹复制给用户
echo 2. 用户运行"启动工具.bat"即可一键部署
echo 3. 或者运行"快速启动.bat"进行快速启动
echo.
echo 注意: 用户需要预先安装Python 3.8+和Node.js 16+
goto :end

:error
echo [错误] 分享包创建失败
pause
exit /b 1

:end
echo.
pause