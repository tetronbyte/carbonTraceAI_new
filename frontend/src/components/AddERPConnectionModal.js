import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { X, Loader, CheckCircle, XCircle } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const ERP_TYPES = [
  { value: 'odoo', label: 'Odoo', type: 'api' },
  { value: 'syspro', label: 'SYSPRO', type: 'sql' },
  { value: 'sap_b1', label: 'SAP Business One', type: 'api' },
  { value: 'erpnext', label: 'ERPNext', type: 'api' },
  { value: 'sage_bc', label: 'Sage Business Cloud', type: 'api' },
  { value: 'dynamics365', label: 'Dynamics 365 Business Central', type: 'api' }
];

const CBAM_SECTORS = [
  'Cement',
  'Iron and Steel',
  'Aluminium',
  'Fertilizers',
  'Electricity',
  'Hydrogen'
];

const AddERPConnectionModal = ({ tenantId, onClose, onSuccess }) => {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [testingConnection, setTestingConnection] = useState(false);
  const [testResult, setTestResult] = useState(null);
  
  const [formData, setFormData] = useState({
    erp_type: '',
    country: '',
    cbam_sector: '',
    base_url: '',
    connection_string: '',
    credentials: {
      db: '',
      username: '',
      password: '',
      api_key: ''
    }
  });

  const [errors, setErrors] = useState({});

  const selectedERP = ERP_TYPES.find(erp => erp.value === formData.erp_type);

  const handleChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Clear error for this field
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const handleCredentialChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      credentials: {
        ...prev.credentials,
        [field]: value
      }
    }));
  };

  const validateStep1 = () => {
    const newErrors = {};
    
    if (!formData.erp_type) newErrors.erp_type = 'Please select an ERP system';
    if (!formData.country) newErrors.country = 'Country is required';
    if (!formData.cbam_sector) newErrors.cbam_sector = 'CBAM sector is required';
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const validateStep2 = () => {
    const newErrors = {};
    
    if (selectedERP?.type === 'api') {
      if (!formData.base_url) newErrors.base_url = 'Base URL is required';
    } else if (selectedERP?.type === 'sql') {
      if (!formData.connection_string) newErrors.connection_string = 'Connection string is required';
    }
    
    // Validate credentials based on ERP type
    if (formData.erp_type === 'odoo') {
      if (!formData.credentials.db) newErrors.credentials_db = 'Database name is required';
      if (!formData.credentials.username) newErrors.credentials_username = 'Username is required';
      if (!formData.credentials.password && !formData.credentials.api_key) {
        newErrors.credentials_auth = 'Either password or API key is required';
      }
    } else {
      if (!formData.credentials.username) newErrors.credentials_username = 'Username is required';
      if (!formData.credentials.password) newErrors.credentials_password = 'Password is required';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const testConnection = async () => {
    if (!validateStep2()) return;
    
    try {
      setTestingConnection(true);
      setTestResult(null);
      
      const token = localStorage.getItem('token');
      
      // Prepare credentials object - only include non-empty fields
      const credentials = {};
      Object.entries(formData.credentials).forEach(([key, value]) => {
        if (value.trim()) {
          credentials[key] = value;
        }
      });
      
      const payload = {
        erp_type: formData.erp_type,
        country: formData.country,
        cbam_sector: formData.cbam_sector,
        credentials
      };
      
      if (selectedERP?.type === 'api') {
        payload.base_url = formData.base_url;
      } else {
        payload.connection_string = formData.connection_string;
      }
      
      const response = await axios.post(
        `${API_URL}/api/erp/connections/${tenantId}`,
        payload,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      
      setTestResult({ success: true, message: 'Connection successful!' });
      
      // Auto-proceed to success after 2 seconds
      setTimeout(() => {
        onSuccess();
      }, 2000);
      
    } catch (error) {
      console.error('Connection test failed:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Connection failed';
      setTestResult({ success: false, message: errorMessage });
    } finally {
      setTestingConnection(false);
    }
  };

  const nextStep = () => {
    if (step === 1 && validateStep1()) {
      setStep(2);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Add ERP Connection</h2>
            <p className="text-sm text-gray-600 mt-1">
              Step {step} of 2: {step === 1 ? 'Select ERP System' : 'Configure Connection'}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6">
          {step === 1 && (
            <div className="space-y-6">
              {/* ERP Type Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  ERP System *
                </label>
                <select
                  value={formData.erp_type}
                  onChange={(e) => handleChange('erp_type', e.target.value)}
                  className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 ${
                    errors.erp_type ? 'border-red-500' : 'border-gray-300'
                  }`}
                >
                  <option value="">Select ERP System</option>
                  {ERP_TYPES.map(erp => (
                    <option key={erp.value} value={erp.value}>
                      {erp.label}
                    </option>
                  ))}
                </select>
                {errors.erp_type && (
                  <p className="mt-1 text-sm text-red-600">{errors.erp_type}</p>
                )}
              </div>

              {/* Country */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Country *
                </label>
                <input
                  type="text"
                  value={formData.country}
                  onChange={(e) => handleChange('country', e.target.value)}
                  placeholder="e.g., Kenya, South Africa"
                  className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 ${
                    errors.country ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {errors.country && (
                  <p className="mt-1 text-sm text-red-600">{errors.country}</p>
                )}
              </div>

              {/* CBAM Sector */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  CBAM Sector *
                </label>
                <select
                  value={formData.cbam_sector}
                  onChange={(e) => handleChange('cbam_sector', e.target.value)}
                  className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 ${
                    errors.cbam_sector ? 'border-red-500' : 'border-gray-300'
                  }`}
                >
                  <option value="">Select CBAM Sector</option>
                  {CBAM_SECTORS.map(sector => (
                    <option key={sector} value={sector}>
                      {sector}
                    </option>
                  ))}
                </select>
                {errors.cbam_sector && (
                  <p className="mt-1 text-sm text-red-600">{errors.cbam_sector}</p>
                )}
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-6">
              {/* Base URL (for API-based ERPs) */}
              {selectedERP?.type === 'api' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Base URL *
                  </label>
                  <input
                    type="url"
                    value={formData.base_url}
                    onChange={(e) => handleChange('base_url', e.target.value)}
                    placeholder="https://your-erp-instance.com"
                    className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 ${
                      errors.base_url ? 'border-red-500' : 'border-gray-300'
                    }`}
                  />
                  {errors.base_url && (
                    <p className="mt-1 text-sm text-red-600">{errors.base_url}</p>
                  )}
                </div>
              )}

              {/* Connection String (for SQL-based ERPs) */}
              {selectedERP?.type === 'sql' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Connection String *
                  </label>
                  <input
                    type="text"
                    value={formData.connection_string}
                    onChange={(e) => handleChange('connection_string', e.target.value)}
                    placeholder="Driver={ODBC Driver 17 for SQL Server};Server=..."
                    className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 ${
                      errors.connection_string ? 'border-red-500' : 'border-gray-300'
                    }`}
                  />
                  {errors.connection_string && (
                    <p className="mt-1 text-sm text-red-600">{errors.connection_string}</p>
                  )}
                </div>
              )}

              {/* Credentials Section */}
              <div className="border-t border-gray-200 pt-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Credentials
                </h3>

                {/* Database Name (Odoo specific) */}
                {formData.erp_type === 'odoo' && (
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Database Name *
                    </label>
                    <input
                      type="text"
                      value={formData.credentials.db}
                      onChange={(e) => handleCredentialChange('db', e.target.value)}
                      placeholder="database_name"
                      className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 ${
                        errors.credentials_db ? 'border-red-500' : 'border-gray-300'
                      }`}
                    />
                    {errors.credentials_db && (
                      <p className="mt-1 text-sm text-red-600">{errors.credentials_db}</p>
                    )}
                  </div>
                )}

                {/* Username */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Username *
                  </label>
                  <input
                    type="text"
                    value={formData.credentials.username}
                    onChange={(e) => handleCredentialChange('username', e.target.value)}
                    placeholder="username"
                    className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 ${
                      errors.credentials_username ? 'border-red-500' : 'border-gray-300'
                    }`}
                  />
                  {errors.credentials_username && (
                    <p className="mt-1 text-sm text-red-600">{errors.credentials_username}</p>
                  )}
                </div>

                {/* Password */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Password {formData.erp_type === 'odoo' && '(or use API Key below)'}
                  </label>
                  <input
                    type="password"
                    value={formData.credentials.password}
                    onChange={(e) => handleCredentialChange('password', e.target.value)}
                    placeholder="••••••••"
                    className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 ${
                      errors.credentials_password ? 'border-red-500' : 'border-gray-300'
                    }`}
                  />
                  {errors.credentials_password && (
                    <p className="mt-1 text-sm text-red-600">{errors.credentials_password}</p>
                  )}
                </div>

                {/* API Key (optional for Odoo) */}
                {formData.erp_type === 'odoo' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      API Key (optional)
                    </label>
                    <input
                      type="password"
                      value={formData.credentials.api_key}
                      onChange={(e) => handleCredentialChange('api_key', e.target.value)}
                      placeholder="API key for authentication"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                    />
                  </div>
                )}

                {errors.credentials_auth && (
                  <p className="mt-1 text-sm text-red-600">{errors.credentials_auth}</p>
                )}
              </div>

              {/* Test Result */}
              {testResult && (
                <div className={`flex items-center gap-3 p-4 rounded-lg ${
                  testResult.success ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
                }`}>
                  {testResult.success ? (
                    <CheckCircle className="w-5 h-5 flex-shrink-0" />
                  ) : (
                    <XCircle className="w-5 h-5 flex-shrink-0" />
                  )}
                  <span className="text-sm">{testResult.message}</span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-6 py-4 flex justify-between">
          <button
            onClick={step === 1 ? onClose : () => setStep(1)}
            className="px-4 py-2 text-gray-700 hover:text-gray-900 transition-colors"
            disabled={loading || testingConnection}
          >
            {step === 1 ? 'Cancel' : 'Back'}
          </button>
          
          <div className="flex gap-3">
            {step === 1 ? (
              <button
                onClick={nextStep}
                className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                Next
              </button>
            ) : (
              <button
                onClick={testConnection}
                disabled={testingConnection || testResult?.success}
                className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {testingConnection && <Loader className="w-4 h-4 animate-spin" />}
                {testResult?.success ? 'Connected!' : 'Test & Connect'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AddERPConnectionModal;
