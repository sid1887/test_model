/**
 * Price Alerts Page - Main component
 * Manages price alert creation, listing, and monitoring
 */

import React, { useState, useEffect } from 'react';
import { Plus, Bell, TrendingDown, AlertCircle, CheckCircle, Pause } from 'lucide-react';
import { AlertCreateModal } from '../components/alerts/AlertCreateModal';
import { AlertCard } from '../components/alerts/AlertCard';
import { AlertDetailModal } from '../components/alerts/AlertDetailModal';
import { AlertSettingsModal } from '../components/alerts/AlertSettingsModal';
import { useAlerts } from '../hooks/useAlerts';
import { useWebSocket } from '../hooks/useWebSocket';
import { Alert } from '../types/alerts';

export const PriceAlertsPage: React.FC = () => {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  
  const {
    alerts,
    loading,
    error,
    totalAlerts,
    createAlert,
    updateAlert,
    deleteAlert,
    pauseAlert,
    resumeAlert,
    triggerAlert,
    refreshAlerts
  } = useAlerts(filterStatus);
  
  // WebSocket for real-time updates
  const { lastMessage } = useWebSocket('/ws/alerts');
  
  useEffect(() => {
    if (lastMessage) {
      // Refresh alerts when WebSocket message received
      refreshAlerts();
    }
  }, [lastMessage, refreshAlerts]);
  
  const handleCreateAlert = async (alertData: Record<string, unknown>) => {
    try {
      await createAlert(alertData);
      setIsCreateModalOpen(false);
    } catch (err) {
      console.error('Failed to create alert:', err);
    }
  };
  
  const handleViewDetails = (alert: Alert) => {
    setSelectedAlert(alert);
  };
  
  const getStatusCounts = () => {
    const counts = {
      active: alerts.filter((a: Alert) => a.status === 'active').length,
      paused: alerts.filter((a: Alert) => a.status === 'paused').length,
      fired: alerts.filter((a: Alert) => a.status === 'fired').length,
      expired: alerts.filter((a: Alert) => a.status === 'expired').length,
    };
    return counts;
  };
  
  const statusCounts = getStatusCounts();
  
  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                <Bell className="h-8 w-8 text-blue-600" />
                Price Alerts
              </h1>
              <p className="mt-2 text-gray-600">
                Monitor product prices and get notified when they match your targets
              </p>
            </div>
            
            <div className="flex gap-3">
              <button
                onClick={() => setIsSettingsModalOpen(true)}
                className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Settings
              </button>
              <button
                onClick={() => setIsCreateModalOpen(true)}
                className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-sm"
              >
                <Plus className="h-5 w-5" />
                Create Alert
              </button>
            </div>
          </div>
        </div>
        
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <StatCard
            icon={<CheckCircle className="h-6 w-6 text-green-600" />}
            label="Active Alerts"
            value={statusCounts.active}
            color="green"
          />
          <StatCard
            icon={<Pause className="h-6 w-6 text-yellow-600" />}
            label="Paused"
            value={statusCounts.paused}
            color="yellow"
          />
          <StatCard
            icon={<TrendingDown className="h-6 w-6 text-blue-600" />}
            label="Fired Today"
            value={statusCounts.fired}
            color="blue"
          />
          <StatCard
            icon={<AlertCircle className="h-6 w-6 text-gray-600" />}
            label="Total Alerts"
            value={totalAlerts}
            color="gray"
          />
        </div>
        
        {/* Filter Tabs */}
        <div className="mb-6 border-b border-gray-200">
          <nav className="flex gap-6">
            {['all', 'active', 'paused', 'fired', 'expired'].map((status) => (
              <button
                key={status}
                onClick={() => setFilterStatus(status)}
                className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
                  filterStatus === status
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {status.charAt(0).toUpperCase() + status.slice(1)}
                {status !== 'all' && (
                  <span className="ml-2 px-2 py-0.5 rounded-full text-xs bg-gray-100">
                    {statusCounts[status as keyof typeof statusCounts] || 0}
                  </span>
                )}
              </button>
            ))}
          </nav>
        </div>
        
        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-red-600" />
            <p className="text-red-800">{error}</p>
          </div>
        )}
        
        {/* Alerts List */}
        {loading ? (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : alerts.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
            <Bell className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No alerts yet</h3>
            <p className="text-gray-600 mb-6">
              Create your first price alert to start monitoring product prices
            </p>
            <button
              onClick={() => setIsCreateModalOpen(true)}
              className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Plus className="h-5 w-5" />
              Create Your First Alert
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {alerts.map((alert: Alert) => (
              <AlertCard
                key={alert.id}
                alert={alert}
                onView={() => handleViewDetails(alert)}
                onPause={() => pauseAlert(alert.id)}
                onResume={() => resumeAlert(alert.id)}
                onTrigger={() => triggerAlert(alert.id)}
                onDelete={() => deleteAlert(alert.id)}
              />
            ))}
          </div>
        )}
      </div>
      
      {/* Modals */}
      <AlertCreateModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSubmit={handleCreateAlert}
      />
      
      {selectedAlert && (
        <AlertDetailModal
          alert={selectedAlert}
          isOpen={!!selectedAlert}
          onClose={() => setSelectedAlert(null)}
          onUpdate={updateAlert}
        />
      )}
      
      <AlertSettingsModal
        isOpen={isSettingsModalOpen}
        onClose={() => setIsSettingsModalOpen(false)}
      />
    </div>
  );
};

// Stats Card Component
interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: number;
  color: 'green' | 'yellow' | 'blue' | 'gray';
}

const StatCard: React.FC<StatCardProps> = ({ icon, label, value, color }) => {
  const colorClasses = {
    green: 'bg-green-50 border-green-200',
    yellow: 'bg-yellow-50 border-yellow-200',
    blue: 'bg-blue-50 border-blue-200',
    gray: 'bg-gray-50 border-gray-200',
  };
  
  return (
    <div className={`p-6 rounded-lg border ${colorClasses[color]}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600 mb-1">{label}</p>
          <p className="text-3xl font-bold text-gray-900">{value}</p>
        </div>
        <div>{icon}</div>
      </div>
    </div>
  );
};
