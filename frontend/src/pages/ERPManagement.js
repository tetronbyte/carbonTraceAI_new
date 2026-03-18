import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  Plus, 
  Database, 
  AlertCircle, 
  CheckCircle, 
  XCircle,
  RefreshCw,
  Trash2
} from 'lucide-react';
import AddERPConnectionModal from '../components/AddERPConnectionModal';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const ERPManagement = () => {
  const navigate = useNavigate();
  const [connections, setConnections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [healthStatus, setHealthStatus] = useState({});
  const [selectedOrg, setSelectedOrg] = useState(null);

  useEffect(() => {
    // Get selected organization from localStorage
    const org = JSON.parse(localStorage.getItem('selectedOrganization'));
    if (!org) {
      navigate('/dashboard');
      return;
    }
    setSelectedOrg(org);
    fetchConnections(org.id);
  }, [navigate]);

  const fetchConnections = async (tenantId) => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      // Fetch ERP connections
      const response = await axios.get(
        `${API_URL}/api/erp/connections/${tenantId}`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      
      setConnections(response.data.connections || []);
      
      // Fetch health status
      await checkHealth(tenantId);
    } catch (error) {
      console.error('Error fetching connections:', error);
      if (error.response?.status === 404) {
        setConnections([]);
      }
    } finally {
      setLoading(false);
    }
  };

  const checkHealth = async (tenantId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API_URL}/api/erp/health/${tenantId}`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      
      // Convert array to object keyed by erp_type
      const healthMap = {};
      response.data.connectors?.forEach(conn => {
        healthMap[conn.erp_type] = conn;
      });
      setHealthStatus(healthMap);
    } catch (error) {
      console.error('Error checking health:', error);
    }
  };

  const handleDisconnect = async (erpType) => {
    if (!window.confirm(`Are you sure you want to disconnect ${erpType}?`)) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      await axios.delete(
        `${API_URL}/api/erp/connections/${selectedOrg.id}/${erpType}`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      
      // Refresh connections
      fetchConnections(selectedOrg.id);
    } catch (error) {
      console.error('Error disconnecting:', error);
      alert('Failed to disconnect ERP system');
    }
  };

  const getHealthIcon = (erpType) => {
    const health = healthStatus[erpType];
    if (!health) return <AlertCircle className="w-5 h-5 text-gray-400" />;
    
    switch (health.status) {
      case 'healthy':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'unhealthy':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'timeout':
        return <AlertCircle className="w-5 h-5 text-yellow-500" />;
      default:
        return <AlertCircle className="w-5 h-5 text-gray-400" />;
    }
  };

  const getHealthText = (erpType) => {
    const health = healthStatus[erpType];
    if (!health) return 'Unknown';
    
    switch (health.status) {
      case 'healthy':
        return `Healthy (${health.response_time_seconds?.toFixed(2)}s)`;
      case 'unhealthy':
        return 'Connection Failed';
      case 'timeout':
        return 'Timeout';
      default:
        return health.error || 'Error';
    }
  };

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
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            ERP Integrations
          </h1>
          <p className="text-gray-600">
            Connect and manage your ERP systems for automated carbon data extraction
          </p>
        </div>

        {/* Add Connection Button */}
        <div className="mb-6">
          <button
            onClick={() => setShowAddModal(true)}
            className="inline-flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            <Plus className="w-5 h-5 mr-2" />
            Add ERP Connection
          </button>
          
          {selectedOrg && (
            <button
              onClick={() => checkHealth(selectedOrg.id)}
              className="ml-3 inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <RefreshCw className="w-5 h-5 mr-2" />
              Refresh Health
            </button>
          )}
        </div>

        {/* Connections Grid */}
        {connections.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
            <Database className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              No ERP Connections
            </h3>
            <p className="text-gray-600 mb-6">
              Get started by connecting your first ERP system to enable automated data extraction
            </p>
            <button
              onClick={() => setShowAddModal(true)}
              className="inline-flex items-center px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              <Plus className="w-5 h-5 mr-2" />
              Add Your First Connection
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {connections.map((connection) => (
              <div
                key={connection.erp_type}
                className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
              >
                {/* ERP Type Header */}
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 capitalize">
                      {connection.erp_type.replace('_', ' ')}
                    </h3>
                    <p className="text-sm text-gray-500">
                      {connection.country} · {connection.cbam_sector}
                    </p>
                  </div>
                  {getHealthIcon(connection.erp_type)}
                </div>

                {/* Connection Details */}
                <div className="space-y-2 mb-4">
                  <div className="text-sm">
                    <span className="text-gray-500">Status:</span>
                    <span className="ml-2 text-gray-900">
                      {getHealthText(connection.erp_type)}
                    </span>
                  </div>
                  
                  {connection.base_url && (
                    <div className="text-sm">
                      <span className="text-gray-500">URL:</span>
                      <span className="ml-2 text-gray-900 truncate block">
                        {connection.base_url}
                      </span>
                    </div>
                  )}
                  
                  <div className="text-sm">
                    <span className="text-gray-500">Last Synced:</span>
                    <span className="ml-2 text-gray-900">
                      {connection.last_synced_at
                        ? new Date(connection.last_synced_at).toLocaleString()
                        : 'Never'}
                    </span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  <button
                    onClick={() => navigate(`/erp/extract/${selectedOrg.id}/${connection.erp_type}`)}
                    className="flex-1 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    Extract Data
                  </button>
                  <button
                    onClick={() => handleDisconnect(connection.erp_type)}
                    className="px-4 py-2 bg-red-50 text-red-600 text-sm rounded-lg hover:bg-red-100 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add Connection Modal */}
      {showAddModal && (
        <AddERPConnectionModal
          tenantId={selectedOrg?.id}
          onClose={() => setShowAddModal(false)}
          onSuccess={() => {
            setShowAddModal(false);
            fetchConnections(selectedOrg.id);
          }}
        />
      )}
    </div>
  );
};

export default ERPManagement;
