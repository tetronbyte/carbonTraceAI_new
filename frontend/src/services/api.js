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
  uploadInvoice: (file, organizationId) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('organization_id', organizationId);
    return axios.post(`${API}/invoices/upload`, formData, {
      headers: { ...getAuthHeader(), 'Content-Type': 'multipart/form-data' }
    });
  },
  
  getInvoices: (orgId) => 
    axios.get(`${API}/invoices?organization_id=${orgId}`, { headers: getAuthHeader() }),
  
  getInvoice: (id) => 
    axios.get(`${API}/invoices/${id}`, { headers: getAuthHeader() }),

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

  // Greenwashing
  analyzeGreenwashing: (orgId, text, name, type, useAi = false) => 
    axios.post(`${API}/greenwashing/analyze`, {
      organization_id: orgId,
      document_text: text,
      document_name: name,
      document_type: type,
      use_ai_enhancement: useAi
    }, { headers: getAuthHeader() }),
  
  getGreenwashingAnalyses: (orgId) => 
    axios.get(`${API}/greenwashing?organization_id=${orgId}`, { headers: getAuthHeader() }),
  
  getGreenwashingAnalysis: (id) => 
    axios.get(`${API}/greenwashing/${id}`, { headers: getAuthHeader() }),

  // Carbon Estimator
  startEstimatorSession: (orgId) => 
    axios.post(`${API}/estimator/start`, { organization_id: orgId }, { headers: getAuthHeader() }),
  
  sendEstimatorMessage: (sessionId, message) => 
    axios.post(`${API}/estimator/chat`, { session_id: sessionId, message }, { headers: getAuthHeader() }),
  
  generateEstimate: (sessionId) => 
    axios.post(`${API}/estimator/generate`, { session_id: sessionId }, { headers: getAuthHeader() }),
  
  getEstimatorSession: (sessionId) => 
    axios.get(`${API}/estimator/session/${sessionId}`, { headers: getAuthHeader() }),
  
  getEstimatorSessions: (orgId) => 
    axios.get(`${API}/estimator/sessions/${orgId}`, { headers: getAuthHeader() }),

  // ESG Reports
  generateReport: (data) => 
    axios.post(`${API}/reports/generate`, data, { headers: getAuthHeader() }),
  
  getReports: (orgId) => 
    axios.get(`${API}/reports?organization_id=${orgId}`, { headers: getAuthHeader() }),
  
  getReport: (id) => 
    axios.get(`${API}/reports/${id}`, { headers: getAuthHeader() }),
  
  downloadReport: (id) => 
    `${API}/reports/${id}/download`,
  
  getReportHtml: (id) => 
    axios.get(`${API}/reports/${id}/html`, { headers: getAuthHeader() }),
};

export default api;
