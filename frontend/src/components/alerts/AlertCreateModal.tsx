/**
 * Alert Create Modal Component
 * Form for creating new price alerts
 */

import React, { useState } from 'react';
import { X, Bell, DollarSign } from 'lucide-react';
import { AlertCreateRequest, AlertOperator, NotificationChannel, AlertFrequency } from '../../types/alerts';

interface AlertCreateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: AlertCreateRequest) => Promise<void>;
}

export const AlertCreateModal: React.FC<AlertCreateModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
}) => {
  const [formData, setFormData] = useState<AlertCreateRequest>({
    product_id: 0,
    target_price: 0,
    operator: '<=',
    channels: ['email'],
    frequency: 'daily',
    priority: 'normal',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (formData.product_id <= 0) {
      setError('Please enter a valid product ID');
      return;
    }
    
    if (formData.target_price <= 0) {
      setError('Please enter a valid target price');
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      await onSubmit(formData);
      
      // Reset form
      setFormData({
        product_id: 0,
        target_price: 0,
        operator: '<=',
        channels: ['email'],
        frequency: 'daily',
        priority: 'normal',
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create alert');
    } finally {
      setLoading(false);
    }
  };

  const operators: { value: AlertOperator; label: string }[] = [
    { value: '<=', label: 'Less than or equal to (≤)' },
    { value: '<', label: 'Less than (<)' },
    { value: '>=', label: 'Greater than or equal to (≥)' },
    { value: '>', label: 'Greater than (>)' },
    { value: '==', label: 'Equal to (=)' },
    { value: 'percent_off', label: 'Percent off (%)' },
  ];

  const channels: NotificationChannel[] = ['email', 'sms', 'whatsapp', 'push'];
  const frequencies: AlertFrequency[] = ['immediate', 'hourly', 'daily', 'weekly'];

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4">
        <div className="fixed inset-0 bg-black opacity-30" onClick={onClose}></div>
        
        <div className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <Bell className="h-6 w-6 text-blue-600" />
              <h2 className="text-2xl font-bold text-gray-900">Create Price Alert</h2>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="h-6 w-6" />
            </button>
          </div>
          
          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Product ID */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Product ID *
              </label>
              <input
                type="number"
                value={formData.product_id || ''}
                onChange={(e) => setFormData({ ...formData, product_id: parseInt(e.target.value) || 0 })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter product ID"
                required
              />
            </div>
            
            {/* Target Price & Operator */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Target Price *
                </label>
                <div className="relative">
                  <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="number"
                    step="0.01"
                    value={formData.target_price || ''}
                    onChange={(e) => setFormData({ ...formData, target_price: parseFloat(e.target.value) || 0 })}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="0.00"
                    required
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Condition
                </label>
                <select
                  value={formData.operator}
                  onChange={(e) => setFormData({ ...formData, operator: e.target.value as AlertOperator })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {operators.map((op) => (
                    <option key={op.value} value={op.value}>
                      {op.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            
            {/* Notification Channels */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Notification Channels
              </label>
              <div className="grid grid-cols-2 gap-3">
                {channels.map((channel) => (
                  <label
                    key={channel}
                    className="flex items-center gap-2 p-3 border border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
                  >
                    <input
                      type="checkbox"
                      checked={formData.channels?.includes(channel)}
                      onChange={(e) => {
                        const newChannels = e.target.checked
                          ? [...(formData.channels || []), channel]
                          : formData.channels?.filter((c) => c !== channel) || [];
                        setFormData({ ...formData, channels: newChannels });
                      }}
                      className="rounded text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700 capitalize">{channel}</span>
                  </label>
                ))}
              </div>
            </div>
            
            {/* Frequency & Priority */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Check Frequency
                </label>
                <select
                  value={formData.frequency}
                  onChange={(e) => setFormData({ ...formData, frequency: e.target.value as AlertFrequency })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {frequencies.map((freq) => (
                    <option key={freq} value={freq} className="capitalize">
                      {freq}
                    </option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Priority
                </label>
                <select
                  value={formData.priority}
                  onChange={(e) => setFormData({ ...formData, priority: e.target.value as 'normal' | 'urgent' })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="normal">Normal</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>
            </div>
            
            {/* Notes */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Notes (Optional)
              </label>
              <textarea
                value={formData.notes || ''}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows={3}
                placeholder="Add any notes about this alert..."
              />
            </div>
            
            {/* Error Message */}
            {error && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-800 text-sm">
                {error}
              </div>
            )}
            
            {/* Actions */}
            <div className="flex gap-3 pt-4 border-t border-gray-200">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                disabled={loading}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="flex-1 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400"
                disabled={loading}
              >
                {loading ? 'Creating...' : 'Create Alert'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
