import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Table, 
  Button, 
  Space, 
  Statistic, 
  Row, 
  Col, 
  Select, 
  message, 
  Spin, 
  Alert,
  Progress,
  Tag
} from 'antd';
import { 
  ReloadOutlined, 
  DownloadOutlined, 
  RiseOutlined, 
  FallOutlined,
  LineChartOutlined,
  ApiOutlined
} from '@ant-design/icons';
import { analysisApi } from '../services/api';

interface NewsAPICompanyData {
  company_id: number;
  company_name: string;
  current_month: string;
  previous_month: string;
  current_mentions: number;
  previous_mentions: number;
  change_percentage: number;
  formatted_change: string;
  status: string;
}

interface NewsAPISummary {
  [month: string]: {
    total_mentions: number;
    company_count: number;
    avg_mentions: number;
  };
}

const NewsAPIAnalysis: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [dataGenerating, setDataGenerating] = useState(false);
  const [analysisData, setAnalysisData] = useState<NewsAPICompanyData[]>([]);
  const [summaryData, setSummaryData] = useState<NewsAPISummary>({});
  const [targetMonth, setTargetMonth] = useState('2025-09');
  const [totalCompanies, setTotalCompanies] = useState(0);

  useEffect(() => {
    loadData();
  }, [targetMonth]);

  const loadData = async () => {
    setLoading(true);
    try {
      // 并行加载分析数据和汇总数据
      const [analysisResponse, summaryResponse] = await Promise.allSettled([
        fetch(`/api/newsapi/company-analysis?target_month=${targetMonth}`),
        fetch('/api/newsapi/company-summary')
      ]);

      // 处理分析数据
      if (analysisResponse.status === 'fulfilled' && analysisResponse.value.ok) {
        const analysisResult = await analysisResponse.value.json();
        if (analysisResult.success) {
          setAnalysisData(analysisResult.results || []);
          setTotalCompanies(analysisResult.total_companies || 0);
        }
      }

      // 处理汇总数据
      if (summaryResponse.status === 'fulfilled' && summaryResponse.value.ok) {
        const summaryResult = await summaryResponse.value.json();
        if (summaryResult.success) {
          setSummaryData(summaryResult.summary || {});
        }
      }

    } catch (error) {
      console.error('加载NewsAPI数据失败:', error);
      message.error('加载数据失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const generateNewsAPIData = async () => {
    setDataGenerating(true);
    try {
      const response = await fetch('/api/newsapi/generate-company-data', {
        method: 'POST'
      });
      
      if (response.ok) {
        const result = await response.json();
        message.success('NewsAPI数据生成任务已启动，请稍候...');
        
        // 等待一段时间后重新加载数据
        setTimeout(() => {
          loadData();
          setDataGenerating(false);
        }, 30000); // 30秒后重新加载
        
      } else {
        throw new Error('启动数据生成任务失败');
      }
    } catch (error) {
      console.error('生成NewsAPI数据失败:', error);
      message.error('生成数据失败，请重试');
      setDataGenerating(false);
    }
  };

  const exportData = () => {
    // 创建CSV数据
    const csvHeaders = ['公司名称', '当前月份', '上个月份', '当前提及数', '上月提及数', '环比变化', '变化百分比'];
    const csvData = analysisData.map(item => [
      item.company_name,
      item.current_month,
      item.previous_month,
      item.current_mentions,
      item.previous_mentions,
      item.formatted_change,
      `${item.change_percentage}%`
    ]);

    const csvContent = [csvHeaders, ...csvData]
      .map(row => row.map(cell => `"${cell}"`).join(','))
      .join('\n');

    // 下载文件
    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `NewsAPI分析结果_${targetMonth}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    message.success('数据导出成功');
  };

  const getChangeColor = (change: number) => {
    if (change > 0) return '#52c41a';
    if (change < 0) return '#ff4d4f';
    return '#666';
  };

  const getChangeIcon = (change: number) => {
    if (change > 0) return <RiseOutlined style={{ color: '#52c41a' }} />;
    if (change < 0) return <FallOutlined style={{ color: '#ff4d4f' }} />;
    return null;
  };

  // 计算正确的排名（提及数相同的公司拥有相同排名）
  const calculateRanking = (data: NewsAPICompanyData[], currentIndex: number) => {
    if (data.length === 0) return currentIndex + 1;
    
    const currentMentions = data[currentIndex].current_mentions;
    let rank = 1;
    
    // 计算有多少公司的提及数比当前公司高
    for (let i = 0; i < data.length; i++) {
      if (data[i].current_mentions > currentMentions) {
        rank++;
      }
    }
    
    return rank;
  };

  const columns = [
    {
      title: '排名',
      dataIndex: 'index',
      key: 'index',
      width: 80,
      render: (text: any, record: any, index: number) => {
        return calculateRanking(analysisData, index);
      },
    },
    {
      title: '公司名称',
      dataIndex: 'company_name',
      key: 'company_name',
      width: 200,
      sorter: (a: NewsAPICompanyData, b: NewsAPICompanyData) => 
        a.company_name.localeCompare(b.company_name),
    },
    {
      title: `${targetMonth} 提及数`,
      dataIndex: 'current_mentions',
      key: 'current_mentions',
      width: 120,
      sorter: (a: NewsAPICompanyData, b: NewsAPICompanyData) => 
        a.current_mentions - b.current_mentions,
      render: (value: number) => value.toLocaleString(),
    },
    {
      title: '上月提及数',
      dataIndex: 'previous_mentions',
      key: 'previous_mentions',
      width: 120,
      sorter: (a: NewsAPICompanyData, b: NewsAPICompanyData) => 
        a.previous_mentions - b.previous_mentions,
      render: (value: number) => value.toLocaleString(),
    },
    {
      title: '环比变化',
      dataIndex: 'change_percentage',
      key: 'change_percentage',
      width: 150,
      sorter: (a: NewsAPICompanyData, b: NewsAPICompanyData) => 
        a.change_percentage - b.change_percentage,
      render: (value: number, record: NewsAPICompanyData) => (
        <Space>
          {getChangeIcon(value)}
          <span style={{ color: getChangeColor(value), fontWeight: 'bold' }}>
            {record.formatted_change}
          </span>
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      filters: [
        { text: '成功', value: 'success' },
        { text: '无数据', value: 'no_data' },
      ],
      onFilter: (value: any, record: NewsAPICompanyData) => record.status === value,
      render: (status: string) => (
        <Tag color={status === 'success' ? 'green' : 'orange'}>
          {status === 'success' ? '成功' : '无数据'}
        </Tag>
      ),
    },
  ];

  const monthOptions = [
    { label: '2025年9月', value: '2025-09' },
    { label: '2025年8月', value: '2025-08' },
    { label: '2025年7月', value: '2025-07' },
  ];

  // 计算统计数据
  const positiveChanges = analysisData.filter(item => item.change_percentage > 0).length;
  const negativeChanges = analysisData.filter(item => item.change_percentage < 0).length;
  const noChanges = analysisData.filter(item => item.change_percentage === 0).length;

  const hasData = analysisData.length > 0;

  return (
    <div>
      <div className="page-header">
        <h2>📊 NewsAPI 环比分析</h2>
        <p>基于NewsAPI数据的178家AI公司新闻提及次数月度环比分析</p>
      </div>

      {!hasData && (
        <Alert
          message="数据准备提示"
          description="如果这是首次使用，请先生成NewsAPI数据。数据生成需要30-60秒时间。"
          type="info"
          showIcon
          action={
            <Button 
              type="primary" 
              icon={<ApiOutlined />}
              loading={dataGenerating}
              onClick={generateNewsAPIData}
            >
              {dataGenerating ? '生成中...' : '生成NewsAPI数据'}
            </Button>
          }
          style={{ marginBottom: 24 }}
        />
      )}

      {dataGenerating && (
        <Card style={{ marginBottom: 24 }}>
          <div style={{ textAlign: 'center' }}>
            <Spin size="large" />
            <div style={{ marginTop: 16 }}>
              <h3>正在生成NewsAPI数据...</h3>
              <p>为178家公司生成2025年7月、8月、9月的数据，预计需要30-60秒</p>
              <Progress percent={50} status="active" />
            </div>
          </div>
        </Card>
      )}

      {/* 汇总统计 */}
      {Object.keys(summaryData).length > 0 && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          {Object.entries(summaryData).map(([month, stats]) => (
            <Col xs={24} sm={8} key={month}>
              <Card>
                <Statistic
                  title={`${month} 汇总`}
                  value={stats.total_mentions}
                  suffix="次提及"
                  prefix={<LineChartOutlined />}
                />
                <div style={{ marginTop: 8, fontSize: '12px', color: '#666' }}>
                  {stats.company_count} 家公司 • 平均 {stats.avg_mentions} 次/公司
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      )}

      {/* 变化统计 */}
      {hasData && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={6}>
            <Card>
              <Statistic
                title="上升公司"
                value={positiveChanges}
                suffix="家"
                valueStyle={{ color: '#52c41a' }}
                prefix={<RiseOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card>
              <Statistic
                title="下降公司"
                value={negativeChanges}
                suffix="家"
                valueStyle={{ color: '#ff4d4f' }}
                prefix={<FallOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card>
              <Statistic
                title="无变化公司"
                value={noChanges}
                suffix="家"
                valueStyle={{ color: '#666' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card>
              <Statistic
                title="总公司数"
                value={totalCompanies}
                suffix="家"
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 主要操作区 */}
      <Card 
        title="环比分析结果" 
        extra={
          <Space>
            <Select
              value={targetMonth}
              onChange={setTargetMonth}
              options={monthOptions}
              style={{ width: 120 }}
            />
            <Button 
              icon={<ReloadOutlined />} 
              onClick={loadData}
              loading={loading}
            >
              刷新
            </Button>
            <Button 
              icon={<DownloadOutlined />} 
              onClick={exportData}
              disabled={!hasData}
            >
              导出CSV
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={analysisData}
          rowKey="company_id"
          loading={loading}
          pagination={{
            total: analysisData.length,
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `第 ${range[0]}-${range[1]} 条，共 ${total} 条记录`,
          }}
          scroll={{ x: 800 }}
          size="middle"
        />
      </Card>

      {/* 说明信息 */}
      <Alert
        message="数据说明"
        description={
          <div>
            <p><strong>数据源：</strong>NewsAPI.org (模拟数据)</p>
            <p><strong>分析方法：</strong>月度环比分析 (当前月 vs 上一月)</p>
            <p><strong>更新频率：</strong>手动触发更新</p>
            <p><strong>覆盖范围：</strong>178家AI领域初创公司</p>
            <p><strong>时间范围：</strong>2025年7月、8月、9月</p>
          </div>
        }
        type="info"
        style={{ marginTop: 24 }}
      />
    </div>
  );
};

export default NewsAPIAnalysis;