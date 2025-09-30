import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Table, 
  Tag, 
  Space, 
  Typography, 
  Button, 
  Input, 
  message,
  Tooltip,
  Badge,
  Row,
  Col
} from 'antd';
import { 
  SearchOutlined, 
  ReloadOutlined,
  EyeOutlined,
  TeamOutlined,
  TrophyOutlined
} from '@ant-design/icons';
import { competitorApi } from '../services/api';

const { Title, Text, Paragraph } = Typography;
const { Search } = Input;

interface CompetitorData {
  rank: number;
  company: string;
  core_business: string;
  industry: string;
  competitors: Array<{
    name: string;
    is_overlap: boolean;
    investor_info?: string;
  }>;
  competitors_count: number;
}

interface ApiResponse {
  success: boolean;
  message: string;
  total_companies: number;
  data_source: string;
  data: CompetitorData[];
}

const CompetitorAnalysis: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [competitorData, setCompetitorData] = useState<CompetitorData[]>([]);
  const [filteredData, setFilteredData] = useState<CompetitorData[]>([]);
  const [searchText, setSearchText] = useState('');
  const [selectedCompany, setSelectedCompany] = useState<CompetitorData | null>(null);
  const [investorModal, setInvestorModal] = useState<{
    visible: boolean;
    companyName: string;
    investorInfo: string;
    loading: boolean;
  }>({ visible: false, companyName: '', investorInfo: '', loading: false });

  // 获取竞争对手数据
  const fetchCompetitorData = async () => {
    setLoading(true);
    try {
      const response = await competitorApi.getTop40Competitors();
      
      if (response.success) {
        setCompetitorData(response.data);
        setFilteredData(response.data);
        message.success(`成功加载${response.total_companies}家公司的竞争对手数据`);
      } else {
        message.error('获取竞争对手数据失败');
      }
    } catch (error) {
      console.error('获取竞争对手数据失败:', error);
      message.error('获取竞争对手数据失败');
    } finally {
      setLoading(false);
    }
  };

  // 搜索过滤
  const handleSearch = (value: string) => {
    setSearchText(value);
    
    if (!value) {
      setFilteredData(competitorData);
      return;
    }

    const filtered = competitorData.filter(item =>
      item.company.toLowerCase().includes(value.toLowerCase()) ||
      item.core_business.toLowerCase().includes(value.toLowerCase()) ||
      item.industry.toLowerCase().includes(value.toLowerCase()) ||
      item.competitors.some(comp => comp.name.toLowerCase().includes(value.toLowerCase()))
    );
    
    setFilteredData(filtered);
  };

  // 查看公司详情
  const viewCompanyDetails = (company: CompetitorData) => {
    setSelectedCompany(company);
  };

  // 处理重合公司点击
  const handleOverlapCompanyClick = async (companyName: string) => {
    setInvestorModal({ 
      visible: true, 
      companyName, 
      investorInfo: '', 
      loading: true 
    });
    
    try {
      const response = await competitorApi.getInvestorInfo(companyName);
      if (response.success && response.data) {
        setInvestorModal(prev => ({
          ...prev,
          investorInfo: response.data.investor_names || '暂无投资方信息',
          loading: false
        }));
      } else {
        setInvestorModal(prev => ({
          ...prev,
          investorInfo: '未找到投资方信息',
          loading: false
        }));
      }
    } catch (error) {
      console.error('获取投资方信息失败:', error);
      setInvestorModal(prev => ({
        ...prev,
        investorInfo: '获取投资方信息失败',
        loading: false
      }));
      message.error('获取投资方信息失败');
    }
  };

  // 知名VC列表
  const famousVCs = [
    'Andreessen Horowitz',
    'Benchmark',
    'BVP',
    'Insight Partner',
    'Greylock',
    'Sequoia',
    'Lightspeed',
    'Khosla Ventures',
    'Accel',
    'Kleiner Perkins',
    'SV Angel',
    'Index Ventures',
    'NEA',
    'Founders Fund',
    'General Catalyst',
    'Coatue',
    'Spark Capital',
    'Menlo Ventures',
    'Sapphire Ventures',
    'Foundation Capital'
  ];

  // 检查投资方是否为知名VC
  const isFamousVC = (investorName: string): boolean => {
    const lowerInvestor = investorName.toLowerCase().trim();
    return famousVCs.some(vc => {
      const lowerVC = vc.toLowerCase();
      // 检查包含关系或高度相似性
      return lowerInvestor.includes(lowerVC) || lowerVC.includes(lowerInvestor);
    });
  };

  // 解析和渲染投资方信息
  const renderInvestorInfo = (investorInfo: string) => {
    if (!investorInfo || investorInfo === '暂无投资方信息') {
      return <Text type="secondary">{investorInfo}</Text>;
    }

    // 按逗号分割投资方名称
    const investors = investorInfo.split(',').map(name => name.trim()).filter(name => name.length > 0);
    
    return (
      <Space wrap size={[4, 4]}>
        {investors.map((investor, index) => {
          const isFamous = isFamousVC(investor);
          return (
            <Tag
              key={index}
              color={isFamous ? 'red' : 'blue'}
              style={{
                fontSize: '12px',
                padding: '2px 8px',
                borderRadius: '12px',
                fontWeight: isFamous ? 'bold' : 'normal',
                border: isFamous ? '2px solid #ff4d4f' : undefined
              }}
            >
              {investor}
            </Tag>
          );
        })}
      </Space>
    );
  };

  // 获取排名颜色
  const getRankColor = (rank: number) => {
    if (rank <= 5) return '#ff4d4f';
    if (rank <= 10) return '#fa8c16';
    if (rank <= 20) return '#fadb14';
    if (rank <= 30) return '#52c41a';
    return '#1890ff';
  };

  const columns = [
    {
      title: '排名',
      dataIndex: 'rank',
      key: 'rank',
      width: 80,
      fixed: 'left' as const,
      render: (rank: number) => (
        <Badge 
          count={rank} 
          style={{ 
            backgroundColor: getRankColor(rank),
            fontSize: '14px',
            fontWeight: 'bold'
          }} 
        />
      ),
    },
    {
      title: '公司信息',
      key: 'company_info',
      width: 280,
      fixed: 'left' as const,
      render: (record: CompetitorData) => (
        <div style={{ padding: '8px 0' }}>
          <div style={{ marginBottom: '4px' }}>
            <Text strong style={{ 
              color: '#1890ff', 
              fontSize: '16px'
            }}>
              {record.company}
            </Text>
          </div>
          <Tag color="blue" style={{ fontSize: '12px' }}>
            {record.industry}
          </Tag>
        </div>
      ),
    },
    {
      title: '核心业务',
      dataIndex: 'core_business',
      key: 'core_business',
      width: 350,
      render: (business: string) => (
        <Tooltip title={business} placement="topLeft">
          <Paragraph 
            ellipsis={{ rows: 2, expandable: false, tooltip: false }} 
            style={{ 
              margin: 0, 
              fontSize: '13px',
              lineHeight: '1.4',
              color: '#666'
            }}
          >
            {business}
          </Paragraph>
        </Tooltip>
      ),
    },
    {
      title: '竞争对手一览',
      key: 'competitors_display',
      width: 500,
      render: (record: CompetitorData) => (
        <div style={{ padding: '4px 0' }}>
          <div style={{ 
            display: 'flex', 
            flexWrap: 'wrap', 
            gap: '3px',
            maxHeight: '65px',
            overflow: 'hidden',
            lineHeight: '1.2'
          }}>
            {record.competitors.slice(0, 12).map((competitor, index) => (
              <Tag 
                key={index}
                color={competitor.is_overlap ? undefined : "processing"}
                onClick={competitor.is_overlap ? () => handleOverlapCompanyClick(competitor.name) : undefined}
                style={{ 
                  margin: 0,
                  fontSize: '10px',
                  padding: '1px 5px',
                  borderRadius: '8px',
                  fontWeight: '500',
                  lineHeight: '1.3',
                  height: '18px',
                  display: 'flex',
                  alignItems: 'center',
                  cursor: competitor.is_overlap ? 'pointer' : 'default',
                  border: competitor.is_overlap ? '2px solid #ff4d4f' : undefined,
                  backgroundColor: competitor.is_overlap ? '#fff' : undefined,
                  color: competitor.is_overlap ? '#ff4d4f' : undefined
                }}
              >
                {competitor.name}
              </Tag>
            ))}
            {record.competitors.length > 12 && (
              <Tag 
                style={{ 
                  margin: 0,
                  fontSize: '10px',
                  padding: '1px 5px',
                  borderRadius: '8px',
                  backgroundColor: '#f0f0f0',
                  color: '#999',
                  border: '1px dashed #d9d9d9'
                }}
              >
                +{record.competitors_count - 12}
              </Tag>
            )}
            {record.competitors.length === 0 && (
              <Text type="secondary" style={{ fontSize: '11px' }}>
                暂无竞争对手信息
              </Text>
            )}
          </div>
        </div>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (record: CompetitorData) => (
        <Button 
          type="primary"
          size="small"
          icon={<EyeOutlined />}
          onClick={() => viewCompanyDetails(record)}
          style={{ borderRadius: '16px' }}
        >
          查看详情
        </Button>
      ),
    },
  ];

  return (
    <div style={{ padding: '0 0 24px 0' }}>
      <Card 
        bordered={false}
        style={{ borderRadius: '12px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}
      >
        {/* 页面标题 */}
        <div style={{ marginBottom: '24px', textAlign: 'center' }}>
          <Title level={2} style={{ 
            marginBottom: '8px',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            fontSize: '28px'
          }}>
            <TrophyOutlined style={{ marginRight: '12px', color: '#fadb14' }} />
            前四十竞争对手分析
          </Title>
          <Paragraph type="secondary" style={{ fontSize: '16px', margin: 0 }}>
            基于综合排名前40的公司，手动整理的竞争对手信息展示
          </Paragraph>
        </div>

        {/* 搜索和操作区 */}
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          marginBottom: '24px',
          padding: '16px 24px',
          backgroundColor: '#f0f9ff',
          borderRadius: '12px',
          border: '1px solid #e6f4ff'
        }}>
          <Search
            placeholder="搜索公司名称、业务描述或竞争对手"
            allowClear
            size="large"
            style={{ 
              width: 400,
              borderRadius: '20px'
            }}
            onSearch={handleSearch}
            onChange={(e) => handleSearch(e.target.value)}
            enterButton={<SearchOutlined />}
          />
          
          <Button 
            type="primary" 
            size="large"
            icon={<ReloadOutlined />} 
            onClick={fetchCompetitorData}
            loading={loading}
            style={{ 
              borderRadius: '20px',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              border: 'none'
            }}
          >
            刷新数据
          </Button>
        </div>

        {/* 数据表格 */}
        <Table
          columns={columns}
          dataSource={filteredData}
          rowKey="rank"
          loading={loading}
          pagination={{
            total: filteredData.length,
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `第 ${range[0]}-${range[1]} 条/共 ${total} 条`,
            style: { marginTop: '24px' }
          }}
          scroll={{ x: 1350 }}
          style={{ 
            backgroundColor: 'white',
            borderRadius: '12px',
            overflow: 'hidden'
          }}
          rowClassName={(_, index) => 
            index % 2 === 0 ? 'table-row-light' : 'table-row-dark'
          }
        />
      </Card>

      {/* 公司详情模态框 */}
      {selectedCompany && (
        <>
          <div 
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'rgba(0,0,0,0.6)',
              zIndex: 1000,
              backdropFilter: 'blur(4px)'
            }}
            onClick={() => setSelectedCompany(null)}
          />
          
          <Card 
            style={{ 
              position: 'fixed', 
              top: '50%', 
              left: '50%', 
              transform: 'translate(-50%, -50%)',
              width: '600px',
              maxHeight: '80vh',
              overflow: 'auto',
              zIndex: 1001,
              borderRadius: '16px',
              boxShadow: '0 20px 40px rgba(0,0,0,0.3)'
            }}
            title={
              <div style={{ 
                display: 'flex', 
                alignItems: 'center',
                padding: '8px 0'
              }}>
                <Badge 
                  count={selectedCompany.rank} 
                  style={{ 
                    backgroundColor: getRankColor(selectedCompany.rank),
                    marginRight: '12px'
                  }} 
                />
                <div>
                  <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
                    {selectedCompany.company}
                  </div>
                  <Tag color="blue" style={{ marginTop: '4px' }}>
                    {selectedCompany.industry}
                  </Tag>
                </div>
              </div>
            }
            extra={
              <Button 
                type="text" 
                onClick={() => setSelectedCompany(null)}
                style={{ fontSize: '16px' }}
              >
                ✕
              </Button>
            }
          >
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              <div>
                <Text strong style={{ fontSize: '16px', color: '#1890ff' }}>
                  核心业务：
                </Text>
                <Paragraph style={{ 
                  marginTop: '8px', 
                  padding: '16px', 
                  backgroundColor: '#f8f9fa', 
                  borderRadius: '8px',
                  lineHeight: '1.6',
                  fontSize: '14px'
                }}>
                  {selectedCompany.core_business}
                </Paragraph>
              </div>
              
              <div>
                <Text strong style={{ fontSize: '16px', color: '#1890ff' }}>
                  竞争对手：
                </Text>
                <div style={{ marginTop: '12px' }}>
                  <Row gutter={[8, 8]}>
                    {selectedCompany.competitors.map((competitor, index) => (
                      <Col key={index}>
                        <Tag 
                          color={competitor.is_overlap ? undefined : "processing"}
                          onClick={competitor.is_overlap ? () => handleOverlapCompanyClick(competitor.name) : undefined}
                          style={{ 
                            margin: 0,
                            fontSize: '13px', 
                            padding: '6px 12px',
                            borderRadius: '16px',
                            fontWeight: '500',
                            cursor: competitor.is_overlap ? 'pointer' : 'default',
                            border: competitor.is_overlap ? '2px solid #ff4d4f' : undefined,
                            backgroundColor: competitor.is_overlap ? '#fff' : undefined,
                            color: competitor.is_overlap ? '#ff4d4f' : undefined
                          }}
                        >
                          {competitor.name}
                        </Tag>
                      </Col>
                    ))}
                  </Row>
                </div>
              </div>
            </Space>
          </Card>
        </>
      )}
      
      {/* 投资方信息弹窗 */}
      {investorModal.visible && (
        <>
          <div 
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'rgba(0,0,0,0.6)',
              zIndex: 1002,
              backdropFilter: 'blur(4px)'
            }}
            onClick={() => setInvestorModal({ visible: false, companyName: '', investorInfo: '', loading: false })}
          />
          
          <Card 
            title={
              <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#ff4d4f' }}>
                {investorModal.companyName} - 投资方信息
              </div>
            }
            extra={
              <Button 
                type="text" 
                onClick={() => setInvestorModal({ visible: false, companyName: '', investorInfo: '', loading: false })}
              >
                ✕
              </Button>
            }
            style={{ 
              position: 'fixed', 
              top: '50%', 
              left: '50%', 
              transform: 'translate(-50%, -50%)',
              width: '500px',
              zIndex: 1003,
              borderRadius: '16px'
            }}
          >
            {investorModal.loading ? (
              <div style={{ textAlign: 'center', padding: '20px' }}>
                <Text>加载中...</Text>
              </div>
            ) : (
              <div style={{ 
                padding: '16px', 
                backgroundColor: '#f8f9fa', 
                borderRadius: '8px',
                lineHeight: '1.6'
              }}>
                {renderInvestorInfo(investorModal.investorInfo)}
              </div>
            )}
          </Card>
        </>
      )}
      
      <style>{`
        .table-row-light {
          background-color: #fafafa;
        }
        .table-row-dark {
          background-color: #ffffff;
        }
        .ant-table-thead > tr > th {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
          color: white !important;
          font-weight: bold !important;
          border: none !important;
        }
        .ant-table-tbody > tr:hover > td {
          background-color: #e6f4ff !important;
        }
        .ant-table-tbody > tr > td {
          padding: 12px 16px !important;
          vertical-align: top !important;
        }
        .ant-table-tbody > tr {
          height: auto !important;
          min-height: 90px !important;
        }
      `}</style>
    </div>
  );
};

export default CompetitorAnalysis;