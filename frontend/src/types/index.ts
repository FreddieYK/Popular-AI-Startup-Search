// 公司相关类型
export interface Company {
  id: number;
  name: string;
  cleaned_name: string;
  status: 'active' | 'inactive';
  created_at: string;
  updated_at: string;
}

export interface CompanyCreate {
  name: string;
  cleaned_name: string;
  status?: string;
}

export interface CompanyUpdate {
  name?: string;
  cleaned_name?: string;
  status?: string;
}

export interface CompanyListResponse {
  companies: Company[];
  total: number;
}

export interface ExcelUploadResponse {
  success: boolean;
  companies: Company[];
  errors: string[];
  total_processed: number;
  total_added: number;
  total_skipped: number;
}

// 分析相关类型
export interface MonthlyYoYResult {
  id: number;
  company_id: number;
  company_name: string;
  analysis_month: string;
  current_month_mentions: number | null;
  previous_year_mentions: number | null;
  monthly_change_percentage: number | null;
  formatted_change: string;
  status: 'success' | 'failed';
  created_at: string;
}

export interface MonthlyYoYAnalysisResponse {
  results: MonthlyYoYResult[];
  month: string;
  total_companies: number;
  successful_analyses: number;
  failed_analyses: number;
}

export interface CalculateMonthlyRequest {
  month?: string;
  company_ids?: number[];
}

export interface TaskResponse {
  task_id: string;
  status: string;
  message: string;
}

export interface AutomationStatus {
  next_run: string | null;
  last_run: string | null;
  enabled: boolean;
  total_tasks: number;
  active_tasks: number;
}

// API响应通用类型
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

// 表格分页类型
export interface PaginationParams {
  page: number;
  size: number;
  status?: string;
  search?: string;
}