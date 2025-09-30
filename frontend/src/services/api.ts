import axios, { AxiosResponse } from 'axios';
import { 
  Company, 
  CompanyListResponse, 
  ExcelUploadResponse,
  MonthlyYoYAnalysisResponse,
  CalculateMonthlyRequest,
  TaskResponse,
  AutomationStatus,
  PaginationParams
} from '../types';

// 创建axios实例
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 这里可以添加认证token等
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error) => {
    console.error('API请求错误:', error);
    return Promise.reject(error);
  }
);

// 公司管理API
export const companyApi = {
  // 上传Excel文件
  uploadExcel: async (file: File): Promise<ExcelUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/companies/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // 获取公司列表
  getCompanies: async (params: PaginationParams): Promise<CompanyListResponse> => {
    const response = await api.get('/companies', { params });
    return response.data;
  },

  // 获取单个公司
  getCompany: async (id: number): Promise<Company> => {
    const response = await api.get(`/companies/${id}`);
    return response.data;
  },

  // 更新公司
  updateCompany: async (id: number, data: any): Promise<Company> => {
    const response = await api.put(`/companies/${id}`, data);
    return response.data;
  },

  // 删除公司
  deleteCompany: async (id: number): Promise<void> => {
    await api.delete(`/companies/${id}`);
  },

  // 批量删除公司
  batchDeleteCompanies: async (ids: number[]): Promise<void> => {
    await api.post('/companies/batch-delete', { company_ids: ids });
  },
};

// 分析API
export const analysisApi = {
  // 获取月度同比分析结果
  getMonthlyYoYAnalysis: async (
    month?: string, 
    companyIds?: number[]
  ): Promise<MonthlyYoYAnalysisResponse> => {
    const params: any = {};
    if (month) params.month = month;
    if (companyIds) params.company_ids = companyIds;
    
    const response = await api.get('/analysis/monthly-yoy', { params });
    return response.data;
  },

  // 手动触发月度同比计算
  calculateMonthlyAnalysis: async (
    request: CalculateMonthlyRequest
  ): Promise<TaskResponse> => {
    const response = await api.post('/analysis/calculate-monthly', request);
    return response.data;
  },

  // 导出月度分析CSV
  exportMonthlyCSV: async (
    month?: string, 
    companyIds?: number[], 
    analysisType: string = 'mom'
  ): Promise<Blob> => {
    const params: any = {};
    if (month) params.month = month;
    if (companyIds) params.company_ids = companyIds;
    params.analysis_type = analysisType;
    
    const response = await api.get('/export/monthly-csv', {
      params,
      responseType: 'blob',
    });
    return response.data;
  },
  
  // 导出近n个月月度分析CSV
  exportMonthlyRangeCSV: async (
    months: number = 6,
    companyIds?: number[], 
    analysisType: string = 'mom'
  ): Promise<Blob> => {
    const params: any = {
      months: months,
      analysis_type: analysisType
    };
    if (companyIds) params.company_ids = companyIds;
    
    const response = await api.get('/export/monthly-range-csv', {
      params,
      responseType: 'blob',
    });
    return response.data;
  },
  
  // 获取矩阵形式的月度环比分析结果
  getMonthlyMoMMatrix: async (
    months: number = 6,
    companyIds?: number[]
  ): Promise<any> => {
    const params: any = {
      months: months
    };
    if (companyIds) params.company_ids = companyIds;
    
    const response = await api.get('/analysis/monthly-mom-matrix', { params });
    return response.data;
  },

  // 获取自动化状态
  getAutomationStatus: async (): Promise<AutomationStatus> => {
    const response = await api.get('/automation/status');
    return response.data;
  },

  // 启用自动化
  enableAutomation: async (): Promise<void> => {
    await api.post('/automation/enable');
  },

  // 禁用自动化
  disableAutomation: async (): Promise<void> => {
    await api.post('/automation/disable');
  },
};

// 工具函数
export const downloadFile = (blob: Blob, filename: string) => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};

// 竞争对手分析API
export const competitorApi = {
  // 获取前四十竞争对手数据
  getTop40Competitors: async (): Promise<any> => {
    const response = await api.get('/top40-competitors');
    return response.data;
  },

  // 获取指定公司的竞争对手详情
  getCompetitorDetails: async (companyName: string): Promise<any> => {
    const response = await api.get(`/competitor-details/${encodeURIComponent(companyName)}`);
    return response.data;
  },

  // 获取指定公司的投资方信息
  getInvestorInfo: async (companyName: string): Promise<any> => {
    const response = await api.get(`/investor-info/${encodeURIComponent(companyName)}`);
    return response.data;
  },
};

export default api;