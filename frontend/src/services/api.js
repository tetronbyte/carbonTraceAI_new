import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const getAuthHeader = () => {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export const api = {
  // Auth
  login: (email, password) => 
    axios.post(`${API}/auth/login`, { email, password }),
  
  register: (email, password, fullName) => 
    axios.post(`${API}/auth/register`, { email, password, full_name: fullName }),
  
  getMe: () => 
    axios.get(`${API}/auth/me`, { headers: getAuthHeader() }),
  
  getOrganizations: () => 
    axios.get(`${API}/auth/organizations`, { headers: getAuthHeader() }),
  
  createOrganization: (data) => 
    axios.post(`${API}/auth/organizations`, data, { headers: getAuthHeader() }),

  // Dashboard
  getDashboard: (orgId) => 
    axios.get(`${API}/dashboard/${orgId}`, { headers: getAuthHeader() }),

  // Invoices
  uploadInvoice: (file, organizationId, country = 'default') => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('organization_id', organizationId);
    formData.append('country', country);
    return axios.post(`${API}/invoices/upload`, formData, {
      headers: { ...getAuthHeader(), 'Content-Type': 'multipart/form-data' },
      timeout: 600000  // 10 minutes for single invoice AI processing
    });
  },
  
  batchUploadInvoices: (files, organizationId, country = 'default', quarter = null, year = null) => {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    formData.append('organization_id', organizationId);
    formData.append('country', country);
    if (quarter) formData.append('quarter', quarter);
    if (year) formData.append('year', year);
    return axios.post(`${API}/invoices/batch-upload`, formData, {
      headers: { ...getAuthHeader(), 'Content-Type': 'multipart/form-data' },
      timeout: 10000  // 10 seconds - returns immediately with task_id
    });
  },
  
  getBatchUploadStatus: (taskId) =>
    axios.get(`${API}/invoices/batch-upload/status/${taskId}`, { headers: getAuthHeader() }),
  
  getBatchInvoices: (batchId) =>
    axios.get(`${API}/invoices/batch/${batchId}`, { headers: getAuthHeader() }),
  
  getInvoices: (orgId) => 
    axios.get(`${API}/invoices?organization_id=${orgId}`, { headers: getAuthHeader() }),
  
  getInvoice: (id) => 
    axios.get(`${API}/invoices/${id}`, { headers: getAuthHeader() }),
  
  getInvoiceEmissions: (id) =>
    axios.get(`${API}/invoices/${id}/emissions`, { headers: getAuthHeader() }),
  
  deleteInvoice: (id) =>
    axios.delete(`${API}/invoices/${id}`, { headers: getAuthHeader() }),

  // Carbon Ledger
  recordOnBlockchain: (orgId, recordIds) => 
    axios.post(`${API}/ledger/record`, {
      organization_id: orgId,
      emission_record_ids: recordIds
    }, { headers: getAuthHeader() }),
  
  getLedgerEntries: (orgId) => 
    axios.get(`${API}/ledger?organization_id=${orgId}`, { headers: getAuthHeader() }),
  
  getLedgerEntry: (id) => 
    axios.get(`${API}/ledger/${id}`, { headers: getAuthHeader() }),
  
  getEmissionRecords: (orgId, verifiedOnly = false) => 
    axios.get(`${API}/ledger/emissions/${orgId}?verified_only=${verifiedOnly}`, { headers: getAuthHeader() }),

  // ESG Reports
  getFrameworks: () =>
    axios.get(`${API}/reports/frameworks`, { headers: getAuthHeader() }),
  
  generateReport: (data) => 
    axios.post(`${API}/reports/generate`, data, { 
      headers: getAuthHeader(),
      timeout: 10000  // 10 seconds - returns immediately with task_id
    }),
  
  getReportGenerationStatus: (taskId) =>
    axios.get(`${API}/reports/status/${taskId}`, { headers: getAuthHeader() }),
  
  generateCBAMReport: (data) =>
    axios.post(`${API}/reports/cbam`, data, { 
      headers: getAuthHeader(),
      timeout: 1800000  // 30 minutes for AI report generation
    }),
  
  getReports: (orgId) => 
    axios.get(`${API}/reports?organization_id=${orgId}`, { headers: getAuthHeader() }),
  
  getReport: (id) => 
    axios.get(`${API}/reports/${id}`, { headers: getAuthHeader() }),
  
  downloadReport: (id) => 
    `${API}/reports/${id}/download`,
  
  getReportHtml: (id) => 
    axios.get(`${API}/reports/${id}/html`, { headers: getAuthHeader() }),
  
  deleteReport: (id) =>
    axios.delete(`${API}/reports/${id}`, { headers: getAuthHeader() }),
};

export default api;
