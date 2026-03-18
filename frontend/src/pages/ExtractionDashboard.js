import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';
import { 
  Play, 
  Clock, 
  CheckCircle, 
  XCircle, 
  Loader,
  ArrowLeft,
  Calendar,
  Filter
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const ExtractionDashboard = () => {
  const navigate = useNavigate();
  const { tenantId, erpType } = useParams();
  
  const [loading, setLoading] = useState(false);
  const [jobs, setJobs] = useState([]);
  const [connection, setConnection] = useState(null);
  const [showTriggerModal, setShowTriggerModal] = useState(false);
  const [filterStatus, setFilterStatus] = useState('all');

  useEffect(() => {
    if (tenantId && erpType) {
      fetchConnection();
      fetchJobs();
      
      // Poll for job updates every 5 seconds
      const interval = setInterval(fetchJobs, 5000);
      return () => clearInterval(interval);
    }
  }, [tenantId, erpType]);

  const fetchConnection = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API_URL}/api/erp/connections/${tenantId}`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      
      const conn = response.data.connections?.find(c => c.erp_type === erpType);
      setConnection(conn);
    } catch (error) {
      console.error('Error fetching connection:', error);
    }
  };

  const fetchJobs = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API_URL}/api/erp/jobs/${tenantId}?erp_type=${erpType}`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      
      setJobs(response.data.jobs || []);
    } catch (error) {
      console.error('Error fetching jobs:', error);
      // Fallback to empty array on 404
      if (error.response?.status === 404) {
        setJobs([]);
      }
    }
  };

  const triggerExtraction = async (modules, fromDate, toDate) => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const payload = {
        modules,
        from_date: fromDate,
        to_date: toDate
      };
      
      const response = await axios.post(
        `${API_URL}/api/erp/extract/${tenantId}`,
        payload,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      
      // Refresh jobs list
      await fetchJobs();
      setShowTriggerModal(false);
      
      // Show success message
      alert(`Extraction job started! Job ID: ${response.data.job_id}`);
    } catch (error) {
      console.error('Error triggering extraction:', error);
      alert('Failed to start extraction: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'processing':
        return <Loader className="w-5 h-5 text-blue-500 animate-spin" />;
      default:
        return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'processing':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const filteredJobs = jobs.filter(job => 
    filterStatus === 'all' || job.status === filterStatus
  );

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => navigate('/erp')}
            className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to ERP Integrations
          </button>
          
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2 capitalize">
                {erpType?.replace('_', ' ')} Extraction Dashboard
              </h1>
              <p className="text-gray-600">
                Monitor and manage data extraction jobs
              </p>
            </div>
            
            <button
              onClick={() => setShowTriggerModal(true)}
              disabled={!connection}
              className="inline-flex items-center px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              <Play className="w-5 h-5 mr-2" />
              Trigger Extraction
            </button>
          </div>
        </div>

        {/* Connection Info Card */}
        {connection && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-gray-500">Country</p>
                <p className="text-lg font-semibold text-gray-900">{connection.country}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">CBAM Sector</p>
                <p className="text-lg font-semibold text-gray-900">{connection.cbam_sector}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Last Synced</p>
                <p className="text-lg font-semibold text-gray-900">
                  {connection.last_synced_at 
                    ? new Date(connection.last_synced_at).toLocaleString()
                    : 'Never'}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Filter Bar */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Filter className="w-5 h-5 text-gray-500" />
              <span className="text-sm font-medium text-gray-700">Filter by Status:</span>
            </div>
            
            <div className="flex gap-2">
              {['all', 'processing', 'completed', 'failed'].map(status => (
                <button
                  key={status}
                  onClick={() => setFilterStatus(status)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    filterStatus === status
                      ? 'bg-green-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {status.charAt(0).toUpperCase() + status.slice(1)}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Jobs Table */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Job ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Progress
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Started
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Modules
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredJobs.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="px-6 py-12 text-center">
                      <Clock className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                      <p className="text-gray-600">No extraction jobs yet</p>
                      <p className="text-sm text-gray-500 mt-1">
                        Click "Trigger Extraction" to start your first job
                      </p>
                    </td>
                  </tr>
                ) : (
                  filteredJobs.map(job => (
                    <tr key={job.job_id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-mono text-gray-900">
                          {job.job_id.slice(0, 8)}...
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          {getStatusIcon(job.status)}
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(job.status)}`}>
                            {job.status}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <div className="flex-1 bg-gray-200 rounded-full h-2 max-w-[100px]">
                            <div
                              className="bg-green-600 h-2 rounded-full transition-all"
                              style={{ width: `${job.progress || 0}%` }}
                            />
                          </div>
                          <span className="text-sm text-gray-600">{job.progress || 0}%</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {new Date(job.created_at).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {job.metadata?.modules?.join(', ') || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <button
                          onClick={() => navigate(`/erp/data/${tenantId}/${job.job_id}`)}
                          className="text-blue-600 hover:text-blue-800 font-medium"
                        >
                          View Data
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Trigger Extraction Modal */}
      {showTriggerModal && (
        <TriggerExtractionModal
          erpType={erpType}
          onClose={() => setShowTriggerModal(false)}
          onTrigger={triggerExtraction}
          loading={loading}
        />
      )}
    </div>
  );
};

// Trigger Extraction Modal Component
const TriggerExtractionModal = ({ erpType, onClose, onTrigger, loading }) => {
  const [selectedModules, setSelectedModules] = useState(['energy', 'production', 'procurement']);
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');

  const modules = [
    { value: 'energy', label: 'Energy Consumption' },
    { value: 'production', label: 'Production Data' },
    { value: 'procurement', label: 'Procurement Records' },
    { value: 'manufacturing', label: 'Manufacturing' },
    { value: 'accounts_payable', label: 'Accounts Payable' }
  ];

  const toggleModule = (module) => {
    setSelectedModules(prev =>
      prev.includes(module)
        ? prev.filter(m => m !== module)
        : [...prev, module]
    );
  };

  const handleSubmit = () => {
    if (selectedModules.length === 0) {
      alert('Please select at least one module');
      return;
    }
    onTrigger(selectedModules, fromDate, toDate);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-lg w-full">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900">Trigger Data Extraction</h2>
          <p className="text-sm text-gray-600 mt-1">
            Select modules and date range for extraction
          </p>
        </div>

        <div className="p-6 space-y-6">
          {/* Module Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Select Modules to Extract *
            </label>
            <div className="space-y-2">
              {modules.map(module => (
                <label
                  key={module.value}
                  className="flex items-center p-3 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50"
                >
                  <input
                    type="checkbox"
                    checked={selectedModules.includes(module.value)}
                    onChange={() => toggleModule(module.value)}
                    className="w-4 h-4 text-green-600 border-gray-300 rounded focus:ring-green-500"
                  />
                  <span className="ml-3 text-sm text-gray-900">{module.label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Date Range */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                From Date (Optional)
              </label>
              <input
                type="date"
                value={fromDate}
                onChange={(e) => setFromDate(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                To Date (Optional)
              </label>
              <input
                type="date"
                value={toDate}
                onChange={(e) => setToDate(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
              />
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800">
              <strong>Note:</strong> If no date range is specified, the system will perform an incremental sync from the last extraction timestamp.
            </p>
          </div>
        </div>

        <div className="bg-gray-50 px-6 py-4 flex justify-end gap-3 rounded-b-lg">
          <button
            onClick={onClose}
            disabled={loading}
            className="px-4 py-2 text-gray-700 hover:text-gray-900 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={loading || selectedModules.length === 0}
            className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {loading && <Loader className="w-4 h-4 animate-spin" />}
            {loading ? 'Starting...' : 'Start Extraction'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ExtractionDashboard;
