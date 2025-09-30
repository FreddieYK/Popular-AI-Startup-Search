import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Button, Space, Alert, Spin, message } from 'antd';
import { 
  FileTextOutlined, 
  BarChartOutlined, 
  ClockCircleOutlined,
  SyncOutlined
} from '@ant-design/icons';
import { companyApi, analysisApi } from '../services/api';
import { AutomationStatus } from '../types';

const HomePage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [companiesCount, setCompaniesCount] = useState(0);
  const [analysisCount, setAnalysisCount] = useState(0);
  const [automationStatus, setAutomationStatus] = useState<AutomationStatus | null>(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // 并行加载数据
      const [companiesResult, analysisResult, automationResult] = await Promise.allSettled([
        companyApi.getCompanies({ page: 1, size: 1 }),
        analysisApi.getMonthlyYoYAnalysis(),
        analysisApi.getAutomationStatus()
      ]);

      // 处理公司数据
      if (companiesResult.status === 'fulfilled') {
        setCompaniesCount(companiesResult.value.total);
      }

      // 处理分析数据
      if (analysisResult.status === 'fulfilled') {
        setAnalysisCount(analysisResult.value.total_companies);
      }

      // 处理自动化状态
      if (automationResult.status === 'fulfilled') {
        setAutomationStatus(automationResult.value);
      }

    } catch (error) {
      console.error('加载仪表板数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDateTime = (dateString: string | null) => {
    if (!dateString) return '未设置';
    return new Date(dateString).toLocaleString('zh-CN');
  };

  return (
    <div>
      <div className="page-header">
        <h2>系统概览</h2>
        <p>欢迎使用AI初创公司新闻监测系统，基于GDELT数据库为您提供精准的市场洞察。</p>
      </div>

      <Spin spinning={loading}>
        <Row gutter={[16, 16]}>
          {/* 统计卡片 */}
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="监测公司总数"
                value={companiesCount}
                prefix={<FileTextOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>

          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="已分析公司"
                value={analysisCount}
                prefix={<BarChartOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>

          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="自动化任务"
                value={automationStatus?.active_tasks || 0}
                suffix={`/ ${automationStatus?.total_tasks || 0}`}
                prefix={<SyncOutlined />}
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Col>

          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="系统状态"
                value={automationStatus?.enabled ? '运行中' : '已停止'}
                prefix={<ClockCircleOutlined />}
                valueStyle={{ 
                  color: automationStatus?.enabled ? '#52c41a' : '#ff4d4f' 
                }}
              />
            </Card>
          </Col>
        </Row>

        {/* 自动化状态详情 */}
        {automationStatus && (
          <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
            <Col span={24}>
              <Card title="自动化任务状态" size="small">
                <Row gutter={16}>
                  <Col xs={24} md={12}>
                    <div style={{ marginBottom: 16 }}>
                      <strong>下次运行时间：</strong>
                      <br />
                      {formatDateTime(automationStatus.next_run)}
                    </div>
                  </Col>
                  <Col xs={24} md={12}>
                    <div style={{ marginBottom: 16 }}>
                      <strong>上次运行时间：</strong>
                      <br />
                      {formatDateTime(automationStatus.last_run)}
                    </div>
                  </Col>
                </Row>
                
                <Space>
                  <Button 
                    type={automationStatus.enabled ? "default" : "primary"}
                    onClick={async () => {
                      try {
                        if (automationStatus.enabled) {
                          await analysisApi.disableAutomation();
                        } else {
                          await analysisApi.enableAutomation();
                        }
                        loadDashboardData();
                      } catch (error) {
                        console.error('切换自动化状态失败:', error);
                      }
                    }}
                  >
                    {automationStatus.enabled ? '禁用自动化' : '启用自动化'}
                  </Button>
                  <Button onClick={loadDashboardData}>
                    刷新状态
                  </Button>
                </Space>
              </Card>
            </Col>
          </Row>
        )}

        {/* 快速操作 */}
        <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
          <Col span={24}>
            <Card title="快速操作" size="small">
              <Space wrap>
                <Button 
                  type="primary" 
                  icon={<FileTextOutlined />}
                  onClick={() => window.location.href = '/companies'}
                >
                  管理公司列表
                </Button>
                <Button 
                  icon={<BarChartOutlined />}
                  onClick={() => window.location.href = '/analysis'}
                >
                  查看分析结果
                </Button>

                <Button 
                  icon={<SyncOutlined />}
                  onClick={async () => {
                    try {
                      await analysisApi.calculateMonthlyAnalysis({});
                      message.success('分析任务已启动');
                    } catch (error) {
                      console.error('启动分析任务失败:', error);
                    }
                  }}
                >
                  手动分析
                </Button>
              </Space>
            </Card>
          </Col>
        </Row>

        {/* 系统说明 */}
        <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
          <Col span={24}>
            <Alert
              message="系统功能说明"
              description={
                <div>
                  <p><strong>1. 公司管理：</strong>上传Excel文件导入公司列表，支持批量操作</p>
                  <p><strong>2. 数据采集：</strong>自动调用GDELT API获取全球新闻数据</p>
                  <p><strong>3. 同比分析：</strong>计算月度同比变化，为投资决策提供数据支撑</p>
                  <p><strong>4. 自动化任务：</strong>每月自动执行数据采集和分析，无需手动干预</p>
                </div>
              }
              type="info"
              showIcon
            />
          </Col>
        </Row>
      </Spin>
    </div>
  );
};

export default HomePage;