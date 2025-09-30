import React, { useState, useEffect } from 'react';
import {
  Card, Table, Button, Upload, message, Modal, Form,
  Input, Select, Space, Popconfirm, Alert, Spin
} from 'antd';
import {
  UploadOutlined, PlusOutlined, EditOutlined,
  DeleteOutlined, DownloadOutlined, SyncOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { UploadProps } from 'antd';
import { companyApi, downloadFile } from '../services/api';
import { Company, ExcelUploadResponse } from '../types';

const { Search } = Input;
const { Option } = Select;

const CompanyManagement: React.FC = () => {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [searchText, setSearchText] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editingCompany, setEditingCompany] = useState<Company | null>(null);
  const [form] = Form.useForm();

  useEffect(() => {
    loadCompanies();
  }, [currentPage, pageSize, searchText, statusFilter]);

  const loadCompanies = async () => {
    try {
      setLoading(true);
      const result = await companyApi.getCompanies({
        page: currentPage,
        size: pageSize,
        search: searchText || undefined,
        status: statusFilter || undefined,
      });
      setCompanies(result.companies);
      setTotal(result.total);
    } catch (error) {
      console.error('加载公司列表失败:', error);
      message.error('加载公司列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleUpload: UploadProps['customRequest'] = async (options) => {
    const { file, onSuccess, onError } = options;
    
    try {
      setUploadLoading(true);
      const result: ExcelUploadResponse = await companyApi.uploadExcel(file as File);
      
      if (result.success) {
        message.success(
          `导入成功！共处理 ${result.total_processed} 家公司，新增 ${result.total_added} 家，跳过 ${result.total_skipped} 家`
        );
        loadCompanies();
        onSuccess?.(result, file as File);
      } else {
        throw new Error('上传失败');
      }
    } catch (error) {
      console.error('上传Excel文件失败:', error);
      message.error('上传Excel文件失败');
      onError?.(error as Error);
    } finally {
      setUploadLoading(false);
    }
  };

  const handleEdit = (company: Company) => {
    setEditingCompany(company);
    form.setFieldsValue({
      name: company.name,
      cleaned_name: company.cleaned_name,
      status: company.status,
    });
    setEditModalVisible(true);
  };

  const handleEditSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (!editingCompany) return;

      await companyApi.updateCompany(editingCompany.id, values);
      message.success('更新成功');
      setEditModalVisible(false);
      setEditingCompany(null);
      form.resetFields();
      loadCompanies();
    } catch (error) {
      console.error('更新公司失败:', error);
      message.error('更新公司失败');
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await companyApi.deleteCompany(id);
      message.success('删除成功');
      loadCompanies();
    } catch (error) {
      console.error('删除公司失败:', error);
      message.error('删除公司失败');
    }
  };

  const handleBatchDelete = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请选择要删除的公司');
      return;
    }

    try {
      await companyApi.batchDeleteCompanies(selectedRowKeys as number[]);
      message.success(`成功删除 ${selectedRowKeys.length} 家公司`);
      setSelectedRowKeys([]);
      loadCompanies();
    } catch (error) {
      console.error('批量删除失败:', error);
      message.error('批量删除失败');
    }
  };

  const columns: ColumnsType<Company> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '原始公司名',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true,
    },
    {
      title: '清洗后公司名',
      dataIndex: 'cleaned_name',
      key: 'cleaned_name',
      ellipsis: true,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <span style={{ 
          color: status === 'active' ? '#52c41a' : '#ff4d4f' 
        }}>
          {status === 'active' ? '活跃' : '停用'}
        </span>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (time: string) => new Date(time).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, record) => (
        <Space size="small">
          <Button 
            type="link" 
            size="small" 
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这家公司吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button 
              type="link" 
              size="small" 
              danger
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const rowSelection = {
    selectedRowKeys,
    onChange: setSelectedRowKeys,
  };

  return (
    <div>
      <div className="page-header">
        <h2>公司管理</h2>
        <p>管理监测的AI初创公司列表，支持Excel批量导入和手动维护。</p>
      </div>

      <Card>
        {/* 操作工具栏 */}
        <div className="action-buttons">
          <Space wrap>
            <Upload
              name="file"
              accept=".xlsx,.xls"
              showUploadList={false}
              customRequest={handleUpload}
              disabled={uploadLoading}
            >
              <Button 
                type="primary" 
                icon={<UploadOutlined />}
                loading={uploadLoading}
              >
                上传Excel文件
              </Button>
            </Upload>
            
            <Popconfirm
              title={`确定要删除选中的 ${selectedRowKeys.length} 家公司吗？`}
              onConfirm={handleBatchDelete}
              disabled={selectedRowKeys.length === 0}
            >
              <Button 
                danger 
                icon={<DeleteOutlined />}
                disabled={selectedRowKeys.length === 0}
              >
                批量删除
              </Button>
            </Popconfirm>
            
            <Button 
              icon={<SyncOutlined />}
              onClick={loadCompanies}
            >
              刷新
            </Button>
          </Space>
        </div>

        {/* 筛选工具栏 */}
        <div style={{ marginBottom: 16 }}>
          <Space>
            <Search
              placeholder="搜索公司名称"
              style={{ width: 200 }}
              onSearch={setSearchText}
              allowClear
            />
            <Select
              placeholder="筛选状态"
              style={{ width: 120 }}
              value={statusFilter}
              onChange={setStatusFilter}
              allowClear
            >
              <Option value="active">活跃</Option>
              <Option value="inactive">停用</Option>
            </Select>
          </Space>
        </div>

        {/* 使用说明 */}
        <Alert
          message="Excel文件要求"
          description={`请确保Excel文件包含“清洗后公司名”工作表，且公司名称在第一列。支持.xlsx和.xls格式。`}
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />

        {/* 数据表格 */}
        <Table
          columns={columns}
          dataSource={companies}
          rowKey="id"
          loading={loading}
          rowSelection={rowSelection}
          pagination={{
            current: currentPage,
            pageSize: pageSize,
            total: total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
            onChange: (page, size) => {
              setCurrentPage(page);
              setPageSize(size);
            },
          }}
        />
      </Card>

      {/* 编辑弹窗 */}
      <Modal
        title="编辑公司信息"
        open={editModalVisible}
        onOk={handleEditSubmit}
        onCancel={() => {
          setEditModalVisible(false);
          setEditingCompany(null);
          form.resetFields();
        }}
        okText="保存"
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
        >
          <Form.Item
            label="原始公司名"
            name="name"
            rules={[{ required: true, message: '请输入原始公司名' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            label="清洗后公司名"
            name="cleaned_name"
            rules={[{ required: true, message: '请输入清洗后公司名' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            label="状态"
            name="status"
            rules={[{ required: true, message: '请选择状态' }]}
          >
            <Select>
              <Option value="active">活跃</Option>
              <Option value="inactive">停用</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default CompanyManagement;