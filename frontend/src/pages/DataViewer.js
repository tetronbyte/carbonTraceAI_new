import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';
import { 
  ArrowLeft, 
  Database, 
  FileText, 
  Download,
  Filter,
  Eye,
  Table as TableIcon
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const DataViewer = () => {
  const navigate = useNavigate();
  const { tenantId, jobId } = useParams();
  
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('raw'); // 'raw' or 'normalized'
  const [rawData, setRawData] = useState([]);
  const [normalizedData, setNormalizedData] = useState([]);
  const [jobInfo, setJobInfo] = useState(null);
  const [filterModule, setFilterModule] = useState('all');

  useEffect(() => {
    if (tenantId && jobId) {
      fetchJobInfo();
      fetchData();
    }
  }, [tenantId, jobId]);

  const fetchJobInfo = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API_URL}/api/erp/jobs/${jobId}/status`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setJobInfo(response.data);
    } catch (error) {
      console.error('Error fetching job info:', error);
    }
  };

  const fetchData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      // Fetch raw data
      const rawResponse = await axios.get(
        `${API_URL}/api/erp/data/raw/${tenantId}?job_id=${jobId}`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setRawData(rawResponse.data.records || []);
      
      // Fetch normalized data
      const normalizedResponse = await axios.get(
        `${API_URL}/api/erp/data/normalized/${tenantId}?job_id=${jobId}`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setNormalizedData(normalizedResponse.data.records || []);
      
    } catch (error) {
      console.error('Error fetching data:', error);
      // Set empty arrays on error
      setRawData([]);
      setNormalizedData([]);
    } finally {
      setLoading(false);
    }
  };

  const exportToCBAM = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_URL}/api/erp/export/cbam/${tenantId}`,
        { job_id: jobId },
        {
          headers: { Authorization: `Bearer ${token}` },
          responseType: 'blob'
        }
      );
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `cbam_export_${jobId}.xml`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
    } catch (error) {
      console.error('Error exporting to CBAM:', error);
      alert('CBAM export feature coming soon!');
    }
  };

  const getModules = () => {
    const modules = new Set();
    normalizedData.forEach(record => {
      if (record.module) modules.add(record.module);
    });
    return Array.from(modules);
  };

  const filteredData = viewMode === 'raw' 
    ? rawData.filter(r => filterModule === 'all' || r.module === filterModule)
    : normalizedData.filter(r => filterModule === 'all' || r.module === filterModule);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Extraction Dashboard
          </button>
          
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Extracted Data Viewer
              </h1>
              <p className="text-gray-600">
                Job ID: <span className="font-mono">{jobId}</span>
              </p>
            </div>
            
            <button
              onClick={exportToCBAM}
              disabled={normalizedData.length === 0}
              className="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              <Download className="w-5 h-5 mr-2" />
              Export to CBAM XML
            </button>
          </div>
        </div>

        {/* Job Info Card */}
        {jobInfo && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-gray-500">Status</p>
                <p className={`text-lg font-semibold ${
                  jobInfo.status === 'completed' ? 'text-green-600' :
                  jobInfo.status === 'failed' ? 'text-red-600' :
                  'text-blue-600'
                }`}>
                  {jobInfo.status?.toUpperCase()}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Progress</p>
                <p className="text-lg font-semibold text-gray-900">{jobInfo.progress || 0}%</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Started</p>
                <p className="text-lg font-semibold text-gray-900">
                  {new Date(jobInfo.created_at).toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Records</p>
                <p className="text-lg font-semibold text-gray-900">
                  {normalizedData.length} normalized
                </p>
              </div>
            </div>
          </div>
        )}

        {/* View Mode & Filter Bar */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
          <div className="flex items-center justify-between">
            {/* View Mode Toggle */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setViewMode('raw')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  viewMode === 'raw'
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <Database className="w-4 h-4" />
                Raw Data ({rawData.length})
              </button>
              <button
                onClick={() => setViewMode('normalized')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  viewMode === 'normalized'
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <TableIcon className="w-4 h-4" />
                Normalized ({normalizedData.length})
              </button>
            </div>

            {/* Module Filter */}
            <div className="flex items-center gap-2">
              <Filter className="w-5 h-5 text-gray-500" />
              <select
                value={filterModule}
                onChange={(e) => setFilterModule(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
              >
                <option value="all">All Modules</option>
                {getModules().map(module => (
                  <option key={module} value={module}>
                    {module}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Data Display */}
        {filteredData.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
            <Eye className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              No Data Available
            </h3>
            <p className="text-gray-600">
              {jobInfo?.status === 'processing' 
                ? 'Extraction job is still in progress. Data will appear here once completed.'
                : 'No records found for this extraction job.'}
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {viewMode === 'raw' ? (
              // Raw Data View
              filteredData.map((record, index) => (
                <div
                  key={index}
                  className="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <span className="inline-block px-3 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded-full">
                        {record.module || 'Unknown Module'}
                      </span>
                      <p className="text-sm text-gray-500 mt-2">
                        Source Record ID: {record.source_record_id}
                      </p>
                    </div>
                    <span className="text-xs text-gray-500">
                      {new Date(record.extracted_at).toLocaleString()}
                    </span>
                  </div>
                  
                  <div className="bg-gray-50 rounded-lg p-4 overflow-x-auto">
                    <pre className="text-xs text-gray-800 whitespace-pre-wrap">
                      {JSON.stringify(record.raw_payload, null, 2)}
                    </pre>
                  </div>
                </div>
              ))
            ) : (
              // Normalized Data Table
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50 border-b border-gray-200">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Module
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Activity Date
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Item Code
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Quantity
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Unit
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          CO₂ Estimate
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {filteredData.map((record, index) => (
                        <tr key={index} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            <span className="inline-block px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded">
                              {record.module}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                            {new Date(record.activity_date).toLocaleDateString()}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                            {record.item_code || 'N/A'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {record.quantity?.toLocaleString() || 'N/A'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                            {record.unit_normalized || 'N/A'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {record.co2_kg_estimate 
                              ? `${record.co2_kg_estimate.toFixed(2)} kg`
                              : 'Pending'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default DataViewer;
