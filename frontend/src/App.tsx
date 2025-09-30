import React from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { ConfigProvider, Layout, Menu, theme } from 'antd';
import { 
  HomeOutlined, 
  FileTextOutlined, 
  // BarChartOutlined,
  // SettingOutlined,
  // ApiOutlined,
  TrophyOutlined,
  TeamOutlined
} from '@ant-design/icons';
import zhCN from 'antd/locale/zh_CN';

import HomePage from './pages/HomePage';
import CompanyManagement from './pages/CompanyManagement';
// import AnalysisResults from './pages/AnalysisResults';
// import NewsAPIAnalysis from './pages/NewsAPIAnalysis';
import ComprehensiveRanking from './pages/ComprehensiveRanking';
import CompetitorAnalysis from './pages/CompetitorAnalysis';
import './App.css';

const { Header, Content, Sider } = Layout;

const AppContent: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  const menuItems = [
    {
      key: '/',
      icon: <HomeOutlined />,
      label: '首页',
    },
    {
      key: '/companies',
      icon: <FileTextOutlined />,
      label: '公司管理',
    },
    // {
    //   key: '/analysis',
    //   icon: <BarChartOutlined />,
    //   label: '同比分析',
    // },
    // {
    //   key: '/newsapi',
    //   icon: <ApiOutlined />,
    //   label: 'NewsAPI分析',
    // },
    {
      key: '/comprehensive',
      icon: <TrophyOutlined />,
      label: '综合排名',
    },
    {
      key: '/competitors',
      icon: <TeamOutlined />,
      label: '竞争对手分析',
    },
    // {
    //   key: '/settings',
    //   icon: <SettingOutlined />,
    //   label: '系统设置',
    // },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible theme="light">
        <div style={{ 
          height: 32, 
          margin: 16, 
          background: 'rgba(255, 255, 255, 0.2)',
          borderRadius: borderRadiusLG,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#1890ff',
          fontWeight: 'bold'
        }}>
          AI新闻监测
        </div>
        <Menu
          theme="light"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => {
            navigate(key);
          }}
        />
      </Sider>
      
      <Layout>
        <Header style={{ 
          background: colorBgContainer,
          padding: '0 24px',
          display: 'flex',
          alignItems: 'center'
        }}>
          <h1 style={{ 
            margin: 0, 
            color: '#1890ff',
            fontSize: '24px'
          }}>
            AI初创公司新闻监测系统
          </h1>
        </Header>
        
        <Content style={{ 
          margin: '24px 16px', 
          padding: 24, 
          background: colorBgContainer,
          borderRadius: borderRadiusLG,
          minHeight: 280 
        }}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/companies" element={<CompanyManagement />} />
            {/* <Route path="/analysis" element={<AnalysisResults />} /> */}
            {/* <Route path="/newsapi" element={<NewsAPIAnalysis />} /> */}
            <Route path="/comprehensive" element={<ComprehensiveRanking />} />
            <Route path="/competitors" element={<CompetitorAnalysis />} />
            {/* <Route path="/settings" element={<div>系统设置页面开发中...</div>} /> */}
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
};

const App: React.FC = () => {
  return (
    <ConfigProvider locale={zhCN}>
      <Router>
        <AppContent />
      </Router>
    </ConfigProvider>
  );
};

export default App;