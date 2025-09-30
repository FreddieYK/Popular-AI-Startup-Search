import React, { useState, useEffect } from 'react';
import {
  Card, Table, Button, DatePicker, Select, Space, 
  Statistic, Row, Col, message, Spin, Alert, Radio, Modal, InputNumber, Switch
} from 'antd';
import {
  DownloadOutlined, SyncOutlined, BarChartOutlined,
  ArrowUpOutlined, ArrowDownOutlined, CalendarOutlined, TableOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import { analysisApi, downloadFile } from '../services/api';

const { Option } = Select;

type AnalysisType = 'yoy' | 'mom';

const AnalysisResults: React.FC = () => {
  const [analysisType, setAnalysisType] = useState<AnalysisType>('mom'); // 默认使用环比分析
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [calculating, setCalculating] = useState(false);
  const [selectedMonth, setSelectedMonth] = useState<string>(
    dayjs().format('YYYY-MM')
  );
  const [analysisStats, setAnalysisStats] = useState<{
    total: number;
    successful: number;
    failed: number;
  }>({ total: 0, successful: 0, failed: 0 });
  
  // 多月导出相关状态
  const [showRangeExportModal, setShowRangeExportModal] = useState(false);
  const [exportMonths, setExportMonths] = useState(6);
  
  // 新增矩阵显示模式相关状态
  const [displayMode, setDisplayMode] = useState<'list' | 'matrix'>('list');
  const [matrixData, setMatrixData] = useState<any[]>([]);
  const [matrixMonths, setMatrixMonths] = useState<string[]>([]);
  const [matrixMonthsCount, setMatrixMonthsCount] = useState(6);

  useEffect(() => {
    if (displayMode === 'list') {
      loadAnalysisResults();
    } else {
      loadMatrixData();
    }
  }, [selectedMonth, analysisType, displayMode, matrixMonthsCount]);

  const loadAnalysisResults = async () => {
    try {
      setLoading(true);
      let result: any;
      
      if (analysisType === 'mom') {
        // 环比分析
        const response = await fetch(`/api/analysis/monthly-mom?month=${selectedMonth}`);
        result = await response.json();
      } else {
        // 同比分析
        result = await analysisApi.getMonthlyYoYAnalysis(selectedMonth);
      }
      
      setResults((result.results || []).sort((a: any, b: any) => {
        const aVal = a.current_month_mentions || 0;
        const bVal = b.current_month_mentions || 0;
        return bVal - aVal; // 降序排列，提及数多的排名靠前
      }));
      setAnalysisStats({
        total: result.total_companies || 0,
        successful: result.successful_analyses || 0,
        failed: result.failed_analyses || 0,
      });
    } catch (error) {
      console.error('加载分析结果失败:', error);
      message.error('加载分析结果失败');
    } finally {
      setLoading(false);
    }
  };
  
  const loadMatrixData = async () => {
    try {
      setLoading(true);
      const result = await analysisApi.getMonthlyMoMMatrix(matrixMonthsCount);
      
      setMatrixData((result.matrix_data || []).sort((a: any, b: any) => {
        // 按照最新月份的当前月提及数排序
        const latestMonth = result.months && result.months.length > 0 ? result.months[result.months.length - 1] : null;
        if (latestMonth && a.monthly_changes && b.monthly_changes) {
          const aData = a.monthly_changes[latestMonth];
          const bData = b.monthly_changes[latestMonth];
          const aVal = (aData && aData.status !== 'no_data') ? aData.current_month_mentions || 0 : 0;
          const bVal = (bData && bData.status !== 'no_data') ? bData.current_month_mentions || 0 : 0;
          return bVal - aVal; // 降序排列
        }
        return 0;
      }));
      setMatrixMonths(result.months || []);
      setAnalysisStats({
        total: result.total_companies || 0,
        successful: result.total_companies || 0,
        failed: 0,
      });
    } catch (error) {
      console.error('加载矩阵数据失败:', error);
      message.error('加载矩阵数据失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCalculateAnalysis = async () => {
    try {
      setCalculating(true);
      await analysisApi.calculateMonthlyAnalysis({
        month: selectedMonth,
      });
      message.success('分析任务已启动，请稍后刷新查看结果');
      
      // 延迟刷新结果
      setTimeout(() => {
        loadAnalysisResults();
      }, 3000);
    } catch (error) {
      console.error('启动分析任务失败:', error);
      message.error('启动分析任务失败');
    } finally {
      setCalculating(false);
    }
  };

  const handleExportCSV = async () => {
    try {
      const blob = await analysisApi.exportMonthlyCSV(selectedMonth, undefined, analysisType);
      downloadFile(blob, `月度${analysisType === 'mom' ? '环比' : '同比'}分析_${selectedMonth}.csv`);
      message.success('导出成功');
    } catch (error) {
      console.error('导出失败:', error);
      message.error('导出失败');
    }
  };
  
  const handleRangeExport = async () => {
    try {
      const blob = await analysisApi.exportMonthlyRangeCSV(exportMonths, undefined, analysisType);
      downloadFile(blob, `月度${analysisType === 'mom' ? '环比' : '同比'}分析_近${exportMonths}个月.csv`);
      message.success(`成功导出近${exportMonths}个月数据`);
      setShowRangeExportModal(false);
    } catch (error) {
      console.error('导出失败:', error);
      message.error('导出失败');
    }
  };

  // 计算正确的排名（提及数相同的公司拥有相同排名）
  const calculateRanking = (data: any[], currentIndex: number) => {
    if (data.length === 0) return currentIndex + 1;
    
    const currentMentions = data[currentIndex].current_month_mentions || 0;
    let rank = 1;
    
    // 计算有多少公司的提及数比当前公司高
    for (let i = 0; i < data.length; i++) {
      const mentions = data[i].current_month_mentions || 0;
      if (mentions > currentMentions) {
        rank++;
      }
    }
    
    return rank;
  };

  const columns: ColumnsType<any> = [
    {
      title: '排名',
      dataIndex: 'index',
      key: 'index',
      width: 80,
      render: (text: any, record: any, index: number) => {
        return displayMode === 'list' ? calculateRanking(results, index) : index + 1;
      },
    },
    {
      title: '公司名称',
      dataIndex: 'company_name',
      key: 'company_name',
      fixed: 'left',
      width: 200,
      ellipsis: true,
    },
    {
      title: '分析月份',
      dataIndex: 'analysis_month',
      key: 'analysis_month',
      width: 120,
    },
    {
      title: '当前月提及数',
      dataIndex: 'current_month_mentions',
      key: 'current_month_mentions',
      width: 120,
      render: (value: number | null) => value || 0,
      sorter: (a, b) => {
        const aVal = a.current_month_mentions || 0;
        const bVal = b.current_month_mentions || 0;
        return aVal - bVal;
      },
      sortDirections: ['descend' as const, 'ascend' as const],
    },
    {
      title: analysisType === 'mom' ? '上月提及数' : '去年同月提及数',
      dataIndex: analysisType === 'mom' ? 'previous_month_mentions' : 'previous_year_mentions',
      key: analysisType === 'mom' ? 'previous_month_mentions' : 'previous_year_mentions',
      width: 140,
      render: (value: number | null) => value || 0,
      sorter: (a, b) => {
        const dataIndex = analysisType === 'mom' ? 'previous_month_mentions' : 'previous_year_mentions';
        const aVal = a[dataIndex] || 0;
        const bVal = b[dataIndex] || 0;
        return aVal - bVal;
      },
      sortDirections: ['descend' as const, 'ascend' as const],
    },
    {
      title: analysisType === 'mom' ? '月度环比变化' : '月度同比变化',
      dataIndex: 'formatted_change',
      key: 'formatted_change',
      width: 140,
      render: (change: string, record) => {
        const percentage = record.monthly_change_percentage;
        let color = '#666';
        let icon = null;
        
        if (percentage !== null) {
          if (percentage > 0) {
            color = '#52c41a';
            icon = <ArrowUpOutlined />;
          } else if (percentage < 0) {
            color = '#ff4d4f';
            icon = <ArrowDownOutlined />;
          }
        }
        
        return (
          <span style={{ color, fontWeight: 'bold' }}>
            {icon} {change}
          </span>
        );
      },
      sorter: (a, b) => {
        const aVal = a.monthly_change_percentage || 0;
        const bVal = b.monthly_change_percentage || 0;
        return aVal - bVal;
      },
      defaultSortOrder: 'descend',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <span style={{ 
          color: status === 'success' ? '#52c41a' : '#ff4d4f' 
        }}>
          {status === 'success' ? '成功' : '失败'}
        </span>
      ),
    },
    {
      title: 'GDELT热度',
      dataIndex: 'heat_index',
      key: 'heat_index',
      width: 120,
      render: (heat_index: number | null) => {
        if (heat_index === null || heat_index === undefined) {
          return (
            <span style={{ 
              color: '#999',
              backgroundColor: '#f0f0f0',
              padding: '4px 8px',
              borderRadius: '4px',
              fontSize: '12px'
            }}>
              N/A
            </span>
          );
        }
        
        // 根据TimelineVol值设置颜色
        let color = '#666';
        let bgColor = '#f5f5f5';
        
        if (heat_index >= 1.0) {
          color = '#fff';
          bgColor = '#ff4d4f';  // 红色 - 极高
        } else if (heat_index >= 0.5) {
          color = '#fff';
          bgColor = '#ff7a45';  // 橙红 - 很高
        } else if (heat_index >= 0.2) {
          color = '#fff';
          bgColor = '#ffa940';  // 橙色 - 较高
        } else if (heat_index >= 0.1) {
          color = '#333';
          bgColor = '#faad14';  // 黄色 - 中等
        } else if (heat_index > 0) {
          color = '#333';
          bgColor = '#fadb14';  // 浅黄 - 较低
        } else {
          color = '#999';
          bgColor = '#f0f0f0';  // 灰色 - 无数据
        }
        
        return (
          <span style={{ 
            color,
            backgroundColor: bgColor,
            padding: '4px 8px',
            borderRadius: '4px',
            fontSize: '12px',
            fontWeight: 'bold'
          }}>
            {heat_index.toFixed(6)}
          </span>
        );
      },
      sorter: (a, b) => {
        const aVal = a.heat_index || 0;
        const bVal = b.heat_index || 0;
        return aVal - bVal;
      },
      sortDirections: ['descend' as const, 'ascend' as const],
    },
  ];
  
  // 计算矩阵视图的排名（基于最新月份的提及数）
  const calculateMatrixRanking = (data: any[], currentIndex: number) => {
    if (data.length === 0 || matrixMonths.length === 0) return currentIndex + 1;
    
    const latestMonth = matrixMonths[matrixMonths.length - 1];
    const currentRecord = data[currentIndex];
    const currentData = currentRecord.monthly_changes && currentRecord.monthly_changes[latestMonth];
    const currentMentions = (currentData && currentData.status !== 'no_data') ? currentData.current_month_mentions || 0 : 0;
    
    let rank = 1;
    
    // 计算有多少公司的提及数比当前公司高
    for (let i = 0; i < data.length; i++) {
      const record = data[i];
      const monthData = record.monthly_changes && record.monthly_changes[latestMonth];
      const mentions = (monthData && monthData.status !== 'no_data') ? monthData.current_month_mentions || 0 : 0;
      if (mentions > currentMentions) {
        rank++;
      }
    }
    
    return rank;
  };

  // 矩阵显示的列定义
  const matrixColumns: ColumnsType<any> = [
    {
      title: '排名',
      dataIndex: 'index',
      key: 'index',
      width: 80,
      render: (text: any, record: any, index: number) => {
        return calculateMatrixRanking(matrixData, index);
      },
    },
    {
      title: '公司名称',
      dataIndex: 'company_name',
      key: 'company_name',
      fixed: 'left',
      width: 200,
      ellipsis: true,
    },
    ...matrixMonths.map((month) => ({
      title: month,
      key: month,
      width: 120,
      render: (record: any) => {
        const monthData = record.monthly_changes[month];
        if (!monthData || monthData.status === 'no_data') {
          return <span style={{ color: '#ccc' }}>N/A</span>;
        }
        
        const percentage = monthData.monthly_change_percentage;
        let color = '#666';
        let icon = null;
        
        if (percentage !== null && percentage !== 0) {
          if (percentage > 0) {
            color = '#52c41a';
            icon = <ArrowUpOutlined />;
          } else if (percentage < 0) {
            color = '#ff4d4f';
            icon = <ArrowDownOutlined />;
          }
        }
        
        return (
          <span style={{ color, fontWeight: 'bold', fontSize: '12px' }}>
            {icon} {monthData.formatted_change}
          </span>
        );
      },
      sorter: (a: any, b: any) => {
        const aData = a.monthly_changes[month];
        const bData = b.monthly_changes[month];
        const aVal = (aData && aData.status !== 'no_data') ? aData.current_month_mentions || 0 : 0;
        const bVal = (bData && bData.status !== 'no_data') ? bData.current_month_mentions || 0 : 0;
        return aVal - bVal;
      },
      sortDirections: ['descend' as const, 'ascend' as const],
    })),
  ];

  return (
    <div>
      <div className="page-header">
        <h2>月度{analysisType === 'mom' ? '环比' : '同比'}分析</h2>
        <p>查看AI初创公司新闻提及的月度{analysisType === 'mom' ? '环比' : '同比'}变化趋势，为投资决策提供数据支撑。</p>
      </div>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="分析公司总数"
              value={analysisStats.total}
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="成功分析"
              value={analysisStats.successful}
              prefix={<ArrowUpOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="分析失败"
              value={analysisStats.failed}
              prefix={<ArrowDownOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
      </Row>

      <Card>
        {/* 操作工具栏 */}
        <div className="action-buttons">
          <Space wrap>
            <Radio.Group 
              value={analysisType} 
              onChange={(e) => setAnalysisType(e.target.value)}
              buttonStyle="solid"
              style={{ marginRight: 16 }}
            >
              <Radio.Button value="mom">环比分析</Radio.Button>
              <Radio.Button value="yoy">同比分析</Radio.Button>
            </Radio.Group>
            
            {/* 显示模式切换 */}
            <Space>
              <span>显示模式：</span>
              <Switch
                checked={displayMode === 'matrix'}
                onChange={(checked) => setDisplayMode(checked ? 'matrix' : 'list')}
                checkedChildren="矩阵视图"
                unCheckedChildren="列表视图"
              />
            </Space>
            
            {displayMode === 'list' ? (
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
            ) : (
              <Space>
                <span>显示月份：</span>
                <InputNumber
                  min={1}
                  max={12}
                  value={matrixMonthsCount}
                  onChange={(value) => setMatrixMonthsCount(value || 6)}
                  addonAfter="个月"
                  style={{ width: '120px' }}
                />
              </Space>
            )}
            
            {analysisType === 'yoy' && displayMode === 'list' && (
              <Button 
                type="primary"
                icon={<SyncOutlined />}
                loading={calculating}
                onClick={handleCalculateAnalysis}
              >
                开始分析
              </Button>
            )}
            
            <Button 
              icon={<DownloadOutlined />}
              onClick={handleExportCSV}
              disabled={(displayMode === 'list' ? results.length : matrixData.length) === 0}
            >
              导出当前CSV
            </Button>
            
            <Button 
              icon={<CalendarOutlined />}
              onClick={() => setShowRangeExportModal(true)}
              disabled={(displayMode === 'list' ? results.length : matrixData.length) === 0}
            >
              导出多月数据
            </Button>
            
            <Button 
              icon={<SyncOutlined />}
              onClick={displayMode === 'list' ? loadAnalysisResults : loadMatrixData}
              loading={loading}
            >
              刷新结果
            </Button>
          </Space>
        </div>

        {/* 分析说明 */}
        <Alert
          message="分析说明"
          description={
            <div>
              {analysisType === 'mom' ? (
                <>
                  <p><strong>计算公式：</strong>月度环比变化 = (当前月提及数 - 上月提及数) / 上月提及数 × 100%</p>
                  <p><strong>数据范围：</strong>近6个月的月度数据，支持178家公司</p>
                </>
              ) : (
                <>
                  <p><strong>计算公式：</strong>月度同比变化 = (当前月提及数 - 去年同月提及数) / 去年同月提及数 × 100%</p>
                </>
              )}
              <p><strong>数据来源：</strong>GDELT全球数据库，涵盖全球主要媒体和新闻源</p>
              <p><strong>更新频率：</strong>系统每月1日自动执行分析，也可手动触发</p>
            </div>
          }
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />

        {/* 结果表格 */}
        <Spin spinning={loading}>
          {displayMode === 'list' ? (
            <Table
              columns={columns}
              dataSource={results}
              rowKey="id"
              scroll={{ x: 800 }}
              pagination={{
                pageSize: 50,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
              }}
            />
          ) : (
            <div>
              <div style={{ marginBottom: 16, color: '#666' }}>
                <TableOutlined /> 矩阵视图：显示每家公司在近{matrixMonthsCount}个月的环比变化
              </div>
              <Table
                columns={matrixColumns}
                dataSource={matrixData}
                rowKey="company_id"
                scroll={{ x: 280 + matrixMonths.length * 120 }}
                pagination={{
                  pageSize: 20,
                  showSizeChanger: true,
                  showQuickJumper: true,
                  showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
                }}
              />
            </div>
          )}
        </Spin>
      </Card>
      
      {/* 多月导出对话框 */}
      <Modal
        title="导出多月环比数据"
        open={showRangeExportModal}
        onOk={handleRangeExport}
        onCancel={() => setShowRangeExportModal(false)}
        okText="导出"
        cancelText="取消"
      >
        <div style={{ padding: '20px 0' }}>
          <p>请选择要导出的月份数量：</p>
          <InputNumber
            min={1}
            max={12}
            value={exportMonths}
            onChange={(value) => setExportMonths(value || 6)}
            addonAfter="个月"
            style={{ width: '200px' }}
          />
          <p style={{ marginTop: '10px', color: '#666' }}>
            将导出近{exportMonths}个月的{analysisType === 'mom' ? '环比' : '同比'}分析数据，
            包括所有公司的每月变化情况。
          </p>
        </div>
      </Modal>
    </div>
  );
};

export default AnalysisResults;