# AI初创公司新闻监测系统

基于GDELT全球数据库的AI领域初创公司新闻监测与竞争对手分析系统，用于追踪特定公司在全球新闻报道中的出现频率和竞争对手关系分析，为投资决策提供数据支撑。

## ✨ 主要功能

- 📊 **综合排名**：基于新闻提及频次的公司热度排名
- 🔍 **竞争对手分析**：基于手动整理的40强公司竞争对手关系展示
- 🏢 **公司管理**：Excel文件导入和公司信息管理
- 💰 **投资方分析**：重合公司的投资方信息查询与知名VC标识

## 🚀 快速开始

### 一键启动（推荐）
直接运行根目录下的`启动工具.bat`脚本即可自动完成所有配置并启动系统。

### 手动启动

#### 后端启动
```bash
cd backend
pip install -r ../requirements.txt
python app.py
```

#### 前端启动
```bash
cd frontend
npm install
npm run dev
```

## 🏗️ 技术架构

### 后端技术栈
- **Web框架**: FastAPI + Uvicorn
- **数据库**: SQLite + SQLAlchemy
- **数据处理**: Pandas + NumPy
- **Excel处理**: OpenPyXL
- **HTTP客户端**: HTTPX + Requests

### 前端技术栈
- **框架**: React + TypeScript
- **UI组件**: Ant Design
- **状态管理**: React Hooks
- **构建工具**: Vite

## 📊 核心页面

### 1. 首页
系统概览和快速导航入口

### 2. 公司管理
- Excel文件上传导入
- 公司列表查看和管理
- 支持"清洗后公司名"工作表解析

### 3. 综合排名
- 基于GDELT数据的公司热度排名
- 月度新闻提及数统计
- 排名变化趋势分析

### 4. 竞争对手分析
- 前40强公司竞争对手关系展示
- 基于手动整理的Excel"前四十竞争对手"表格
- 重合公司标红显示（与项目列表重合的竞争对手）
- 重合公司投资方信息查询
- 知名VC投资方标红标识

## 🔄 API接口

### 公司管理
- `POST /api/companies/upload` - 上传Excel文件导入公司列表
- `GET /api/companies` - 获取公司列表

### 综合排名
- `GET /api/comprehensive-ranking` - 获取综合排名数据

### 竞争对手分析
- `GET /api/top40-competitors` - 获取前40强竞争对手数据
- `GET /api/investor-info/{company_name}` - 获取公司投资方信息

## 📁 项目结构

```
AI初创公司新闻监测系统/
├── backend/                    # 后端代码
│   ├── app/                   
│   │   ├── api/               # API路由
│   │   │   ├── companies.py   # 公司管理API
│   │   │   ├── ranking.py     # 综合排名API
│   │   │   └── competitors.py # 竞争对手分析API
│   │   ├── core/              # 核心配置
│   │   ├── models/            # 数据模型
│   │   └── utils/             # 工具函数
│   └── app.py                 # 应用入口
├── frontend/                   # 前端代码
│   ├── src/                   
│   │   ├── pages/             # 页面组件
│   │   │   ├── HomePage.tsx           # 首页
│   │   │   ├── CompanyManagement.tsx  # 公司管理
│   │   │   ├── ComprehensiveRanking.tsx # 综合排名
│   │   │   └── CompetitorAnalysis.tsx # 竞争对手分析
│   │   ├── services/          # API服务
│   │   └── types/             # TypeScript类型
│   └── package.json           
├── requirements.txt           # Python依赖
├── .env                       # 环境配置（需要配置GDELT_API_KEY等）
├── 启动工具.bat               # 一键启动脚本
├── 创建分享包.bat             # 分享包生成脚本
├── 功能演示指南.md            # 功能使用说明
└── README.md                  # 项目说明
```

## 🛠️ 使用说明

### 1. 基础设置
1. 运行`启动工具.bat`一键启动系统
2. 在"公司管理"页面上传包含"清洗后公司名"工作表的Excel文件
3. 确保Excel文件包含"前四十竞争对手"和"去重后公司信息"工作表

### 2. 综合排名查看
1. 进入"综合排名"页面
2. 查看基于GDELT数据的公司热度排名
3. 分析公司在新闻报道中的提及频次变化

### 3. 竞争对手分析
1. 进入"竞争对手分析"页面  
2. 查看前40强公司的竞争对手关系
3. 识别红框标识的重合公司（与项目列表重合的竞争对手）
4. 点击重合公司查看其投资方信息
5. 观察知名VC投资方的红色标识

## 🎯 特色功能

### 竞争对手重合检测
- 自动识别竞争对手中与项目列表重合的公司
- 重合公司用红框特殊标识
- 支持点击查看详细投资方信息

### 知名VC识别
- 系统内置20家知名VC列表
- 投资方信息中自动标红知名VC
- 包括：Andreessen Horowitz、Sequoia、Coatue、General Catalyst、Kleiner Perkins等

### Excel数据驱动
- 完全基于手动整理的Excel数据
- 支持"前四十竞争对手"、"去重后公司信息"、"项目列表"等多工作表
- 灵活的数据更新机制

## 📈 数据源

- **GDELT全球数据库**: 提供全球新闻事件数据
- **手动整理Excel文件**: 包含竞争对手关系和投资方信息
- **项目内部数据库**: 存储分析结果和历史数据

## 🔒 环境配置

请在`.env`文件中配置以下环境变量：
```env
GDELT_API_KEY=your_gdelt_api_key
DATABASE_URL=sqlite:///./ai_news_monitor.db
```

## 📞 支持

如有问题或建议，请提交Issue或联系开发团队。

---

© 2024 AI初创公司新闻监测系统 - 为投资决策提供数据支撑