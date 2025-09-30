import React, { useState, useEffect } from 'react';
import {
  Card, Table, Button, Space, Row, Col, Statistic, Alert, Spin, message,
  Select, DatePicker, Modal, Typography, Tag, Divider
} from 'antd';
import {
  TrophyOutlined, OrderedListOutlined, SyncOutlined, DownloadOutlined,
  ArrowUpOutlined, ArrowDownOutlined, BarChartOutlined, TeamOutlined, SearchOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';

const { Option } = Select;

interface CompanyRankingData {
  company_id: number;
  company_name: string;
  gdelt_mentions: number;
  gdelt_rank: number;
  newsapi_mentions: number;
  newsapi_rank: number;
  combined_rank_score: number;
  final_rank: number;
  previous_rank?: number;
  rank_change?: number;
  rank_change_direction?: 'up' | 'down' | 'same';
}

interface ComprehensiveRankingStats {
  total_companies: number;
  analysis_month: string;
  data_sources: string[];
}

const { Text, Title } = Typography;

interface CompetitorInfo {
  company_name: string;
  competitors: string[];
}

const ComprehensiveRanking: React.FC = () => {
  const [rankingData, setRankingData] = useState<CompanyRankingData[]>([]);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<ComprehensiveRankingStats>({
    total_companies: 0,
    analysis_month: '',
    data_sources: []
  });
  const [selectedMonth, setSelectedMonth] = useState<string>(
    dayjs().format('YYYY-MM')
  );
  const [competitorModalVisible, setCompetitorModalVisible] = useState(false);
  const [currentCompetitors, setCurrentCompetitors] = useState<CompetitorInfo | null>(null);
  const [competitorLoading, setCompetitorLoading] = useState(false);

  useEffect(() => {
    loadComprehensiveRanking();
  }, [selectedMonth]);

  const loadComprehensiveRanking = async () => {
    setLoading(true);
    try {
      // 使用后端的综合排名API
      const response = await fetch(`/api/comprehensive/ranking?target_month=${selectedMonth}`);
      
      if (!response.ok) {
        throw new Error('网络请求失败');
      }
      
      const result = await response.json();
      
      if (result.success) {
        setRankingData(result.results || []);
        setStats({
          total_companies: result.total_companies || 0,
          analysis_month: result.target_month || selectedMonth,
          data_sources: result.data_sources || []
        });
      } else {
        throw new Error(result.message || '数据加载失败');
      }

    } catch (error) {
      console.error('加载综合排名数据失败:', error);
      message.error('加载综合排名数据失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCompanyClick = async (companyName: string) => {
    setCompetitorLoading(true);
    setCompetitorModalVisible(true);
    setCurrentCompetitors(null);
    
    try {
      const response = await fetch(`/api/competitors/${encodeURIComponent(companyName)}`);
      
      if (!response.ok) {
        throw new Error('获取竞争对手信息失败');
      }
      
      const result = await response.json();
      
      if (result.success) {
        setCurrentCompetitors(result.data);
      } else {
        message.error(result.message || '未找到竞争对手信息');
        setCompetitorModalVisible(false);
      }
      
    } catch (error) {
      console.error('获取竞争对手信息失败:', error);
      message.error('获取竞争对手信息失败');
      setCompetitorModalVisible(false);
    } finally {
      setCompetitorLoading(false);
    }
  };

  const handleExportCSV = () => {
    if (rankingData.length === 0) {
      message.warning('暂无数据可导出');
      return;
    }

    const csvHeaders = [
      '最终排名', '公司名称', 'GDELT提及数', 'GDELT排名', 
      'NewsAPI提及数', 'NewsAPI排名', '综合排名分数'
    ];

    const csvData = rankingData.map(item => [
      item.final_rank,
      item.company_name,
      item.gdelt_mentions,
      item.gdelt_rank,
      item.newsapi_mentions,
      item.newsapi_rank,
      item.combined_rank_score
    ]);

    const csvContent = [csvHeaders, ...csvData]
      .map(row => row.map(cell => `"${cell}"`).join(','))
      .join('\n');

    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `综合排名分析_${selectedMonth}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    message.success('数据导出成功');
  };

  // 计算正确的排名（综合排名分数相同的公司拥有相同排名）
  const calculateRanking = (data: CompanyRankingData[], currentIndex: number) => {
    if (data.length === 0) return currentIndex + 1;
    
    const currentScore = data[currentIndex].combined_rank_score;
    let rank = 1;
    
    // 计算有多少公司的综合排名分数比当前公司低（分数越低排名越高）
    for (let i = 0; i < data.length; i++) {
      if (data[i].combined_rank_score < currentScore) {
        rank++;
      }
    }
    
    return rank;
  };

  const getRankBadgeColor = (rank: number) => {
    if (rank <= 10) return '#faad14'; // 金色
    if (rank <= 30) return '#d9d9d9'; // 银色
    if (rank <= 50) return '#cd7f32'; // 铜色
    return '#f5f5f5'; // 默认色
  };

  const columns: ColumnsType<CompanyRankingData> = [
    {
      title: '最终排名',
      dataIndex: 'final_rank',
      key: 'final_rank',
      width: 100,
      render: (rank: number, record: CompanyRankingData, index: number) => {
        const actualRank = calculateRanking(rankingData, index);
        return (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{
              width: 32,
              height: 32,
              borderRadius: '50%',
              backgroundColor: getRankBadgeColor(actualRank),
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 'bold',
              color: actualRank <= 10 ? '#fff' : '#333'
            }}>
              {actualRank}
            </div>
            {actualRank <= 3 && <TrophyOutlined style={{ color: getRankBadgeColor(actualRank) }} />}
          </div>
        );
      },
    },
    {
      title: '公司名称',
      dataIndex: 'company_name',
      key: 'company_name',
      width: 200,
      sorter: (a, b) => a.company_name.localeCompare(b.company_name),
      render: (name: string, record: CompanyRankingData) => (
        <div>
          <div 
            style={{ 
              cursor: 'pointer', 
              color: '#1890ff',
              textDecoration: 'underline',
              display: 'flex',
              alignItems: 'center',
              gap: 4
            }}
            onClick={() => handleCompanyClick(name)}
          >
            {name}
            <TeamOutlined style={{ fontSize: '12px' }} />
          </div>
          {record.rank_change !== null && record.rank_change !== undefined && (
            <div style={{ fontSize: '12px', marginTop: '2px' }}>
              {record.rank_change_direction === 'up' && (
                <span style={{ color: '#ff4d4f' }}>
                  ↑ +{record.rank_change}
                </span>
              )}
              {record.rank_change_direction === 'down' && (
                <span style={{ color: '#52c41a' }}>
                  ↓ {record.rank_change}
                </span>
              )}
              {record.rank_change_direction === 'same' && (
                <span style={{ color: '#666' }}>
                  ↔ 无变化
                </span>
              )}
            </div>
          )}
        </div>
      ),
    },
    {
      title: 'GDELT提及数',
      dataIndex: 'gdelt_mentions',
      key: 'gdelt_mentions',
      width: 120,
      sorter: (a, b) => a.gdelt_mentions - b.gdelt_mentions,
      render: (value: number) => value.toLocaleString(),
    },
    {
      title: 'GDELT排名',
      dataIndex: 'gdelt_rank',
      key: 'gdelt_rank',
      width: 100,
      sorter: (a, b) => a.gdelt_rank - b.gdelt_rank,
      render: (rank: number, record) => (
        <span style={{ 
          color: record.gdelt_mentions === 0 ? '#ccc' : '#666',
          fontWeight: 'bold'
        }}>
          #{rank}
        </span>
      ),
    },
    {
      title: 'NewsAPI提及数',
      dataIndex: 'newsapi_mentions',
      key: 'newsapi_mentions',
      width: 130,
      sorter: (a, b) => a.newsapi_mentions - b.newsapi_mentions,
      render: (value: number) => value.toLocaleString(),
    },
    {
      title: 'NewsAPI排名',
      dataIndex: 'newsapi_rank',
      key: 'newsapi_rank',
      width: 110,
      sorter: (a, b) => a.newsapi_rank - b.newsapi_rank,
      render: (rank: number, record) => (
        <span style={{ 
          color: record.newsapi_mentions === 0 ? '#ccc' : '#666',
          fontWeight: 'bold'
        }}>
          #{rank}
        </span>
      ),
    },
    {
      title: '综合排名分数',
      dataIndex: 'combined_rank_score',
      key: 'combined_rank_score',
      width: 130,
      sorter: (a, b) => a.combined_rank_score - b.combined_rank_score,
      render: (score: number) => (
        <span style={{ 
          color: '#1890ff',
          fontWeight: 'bold',
          backgroundColor: '#e6f7ff',
          padding: '4px 8px',
          borderRadius: '4px'
        }}>
          {score}
        </span>
      ),
    },
  ];

  return (
    <div>
      <div className="page-header">
        <h2>🏆 综合排名分析</h2>
        <p>基于GDELT和NewsAPI双数据源的综合排名分析，通过排名相加计算最终排名</p>
      </div>

      {/* 统计信息 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="分析公司总数"
              value={stats.total_companies}
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="数据源数量"
              value={stats.data_sources.length}
              suffix="个"
              prefix={<OrderedListOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="分析月份"
              value={stats.analysis_month}
              prefix={<TrophyOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 分析说明 */}
      <Alert
        message="综合排名计算方法"
        description={
          <div>
            <p><strong>计算公式：</strong>综合排名分数 = GDELT排名 + NewsAPI排名</p>
            <p><strong>排名规则：</strong>综合排名分数越小，最终排名越高</p>
            <p><strong>排名变化：</strong>显示相较于上个月的排名变化情况</p>
            <p><strong>颜色含义：</strong>🔴红色↑表示排名上升，🟢绿色↓表示排名下降</p>
            <p><strong>竞争对手：</strong>点击公司名称可查看基于Grok AI分析的竞争对手信息</p>
            <p><strong>数据来源：</strong>GDELT全球数据库 + NewsAPI.org</p>
            <p><strong>排名依据：</strong>各数据源中当月新闻提及次数的排名</p>
            <p><strong>处理原则：</strong>如某公司在某数据源中无数据，则给予该数据源最大排名+1</p>
          </div>
        }
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      {/* 主表格 */}
      <Card 
        title="综合排名结果" 
        extra={
          <Space>
            <DatePicker
              picker="month"
              value={dayjs(selectedMonth)}
              onChange={(date) => {
                if (date) {
                  setSelectedMonth(date.format('YYYY-MM'));
                }
              }}
              placeholder="选择分析月份"
            />
            <Button 
              icon={<SyncOutlined />}
              onClick={loadComprehensiveRanking}
              loading={loading}
            >
              刷新数据
            </Button>
            <Button 
              icon={<DownloadOutlined />}
              onClick={handleExportCSV}
              disabled={rankingData.length === 0}
            >
              导出CSV
            </Button>
          </Space>
        }
      >
        <Spin spinning={loading}>
          <Table
            columns={columns}
            dataSource={rankingData}
            rowKey="company_name"
            scroll={{ x: 800 }}
            pagination={{
              pageSize: 20,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) => 
                `第 ${range[0]}-${range[1]} 条，共 ${total} 条记录`,
            }}
            size="middle"
          />
        </Spin>
      </Card>

      {/* 竞争对手信息弹窗 */}
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <TeamOutlined style={{ color: '#1890ff' }} />
            <span>竞争对手分析</span>
          </div>
        }
        open={competitorModalVisible}
        onCancel={() => setCompetitorModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setCompetitorModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={600}
      >
        <Spin spinning={competitorLoading}>
          {currentCompetitors ? (
            <div>
              <div style={{ marginBottom: 16 }}>
                <Title level={4} style={{ margin: 0 }}>
                  {currentCompetitors.company_name}
                </Title>
                <Text type="secondary">基于Grok AI分析的竞争对手</Text>
              </div>
              
              <Divider style={{ margin: '12px 0' }} />
              
              <div>
                <Text strong style={{ marginBottom: 12, display: 'block' }}>
                  🏢 发现的竞争对手：
                </Text>
                {currentCompetitors.competitors.length > 0 ? (
                  <Space direction="vertical" style={{ width: '100%' }}>
                    {currentCompetitors.competitors.map((competitor, index) => (
                      <Tag 
                        key={index}
                        color="blue"
                        style={{ 
                          padding: '8px 12px',
                          fontSize: '14px',
                          borderRadius: '6px',
                          marginBottom: '8px'
                        }}
                      >
                        {competitor}
                      </Tag>
                    ))}
                  </Space>
                ) : (
                  <Text type="secondary">暂未找到相关竞争对手</Text>
                )}
              </div>
              
              <Alert
                style={{ marginTop: 16 }}
                message="分析说明"
                description="竞争对手分析基于公司的核心业务、所处行业和投资方信息，通过Grok AI模型进行智能匹配，重点关注AI领域的初创公司。"
                type="info"
                showIcon
              />
            </div>
          ) : (
            !competitorLoading && (
              <div style={{ textAlign: 'center', padding: '40px 0' }}>
                <SearchOutlined style={{ fontSize: '48px', color: '#d9d9d9' }} />
                <div style={{ marginTop: 16 }}>
                  <Text type="secondary">正在获取竞争对手信息...</Text>
                </div>
              </div>
            )
          )}
        </Spin>
      </Modal>
    </div>
  );
};

export default ComprehensiveRanking;