/**
 * Alert Settings Modal Component
 * Manages user notification preferences
 */

import React, { useState, useEffect } from 'react';
import { X, Save, AlertCircle } from 'lucide-react';
import { UserPreferences, NotificationChannel } from '../../types/alerts';
import { API_BASE_URL } from '../../config/env';

interface AlertSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: () => void;
}

export const AlertSettingsModal: React.FC<AlertSettingsModalProps> = ({
  isOpen,
  onClose,
  onSave,
}) => {
  const [preferences, setPreferences] = useState<UserPreferences>({
    id: 1,
    user_id: 1,
    email: '',
    phone: '',
    whatsapp: '',
    email_enabled: true,
    sms_enabled: false,
    whatsapp_enabled: false,
    push_enabled: false,
    quiet_hours_start: undefined,
    quiet_hours_end: undefined,
    max_notifications_per_hour: 10,
    max_notifications_per_day: 50,
    timezone: 'UTC',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadPreferences();
    }
  }, [isOpen]);

  const loadPreferences = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/alerts/preferences/1`);
      if (!response.ok) throw new Error('Failed to load preferences');
      const data = await response.json();
      setPreferences(data);
    } catch (err) {
      console.error('Load preferences error:', err);
      setError('Failed to load preferences');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`${API_BASE_URL}/api/alerts/preferences`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(preferences),
      });
      
      if (!response.ok) throw new Error('Failed to save preferences');
      
      onSave();
      onClose();
    } catch (err) {
      console.error('Save preferences error:', err);
      setError('Failed to save preferences');
    } finally {
      setLoading(false);
    }
  };

  const handleChannelToggle = (channel: NotificationChannel) => {
    switch (channel) {
      case 'email':
        setPreferences({ ...preferences, email_enabled: !preferences.email_enabled });
        break;
      case 'sms':
        setPreferences({ ...preferences, sms_enabled: !preferences.sms_enabled });
        break;
      case 'whatsapp':
        setPreferences({ ...preferences, whatsapp_enabled: !preferences.whatsapp_enabled });
        break;
      case 'push':
        setPreferences({ ...preferences, push_enabled: !preferences.push_enabled });
        break;
    }
  };

  const isChannelEnabled = (channel: NotificationChannel): boolean => {
    switch (channel) {
      case 'email': return preferences.email_enabled;
      case 'sms': return preferences.sms_enabled;
      case 'whatsapp': return preferences.whatsapp_enabled;
      case 'push': return preferences.push_enabled;
      default: return false;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4">
        <div className="fixed inset-0 bg-black opacity-30" onClick={onClose}></div>
        
        <div className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Notification Settings</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="h-6 w-6" />
            </button>
          </div>
          
          {/* Error Message */}
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
              <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0" />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}
          
          {/* Form */}
          <div className="space-y-6">
            {/* Contact Information */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Contact Information</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Email Address
                  </label>
                  <input
                    type="email"
                    value={preferences.email || ''}
                    onChange={(e) => setPreferences({ ...preferences, email: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="your@email.com"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Phone Number
                  </label>
                  <input
                    type="tel"
                    value={preferences.phone || ''}
                    onChange={(e) => setPreferences({ ...preferences, phone: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="+1234567890"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    WhatsApp Number
                  </label>
                  <input
                    type="tel"
                    value={preferences.whatsapp || ''}
                    onChange={(e) => setPreferences({ ...preferences, whatsapp: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="+1234567890"
                  />
                </div>
              </div>
            </div>
            
            {/* Enabled Channels */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Notification Channels</h3>
              <div className="space-y-2">
                {(['email', 'sms', 'whatsapp', 'push'] as NotificationChannel[]).map((channel) => (
                  <label key={channel} className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={isChannelEnabled(channel)}
                      onChange={() => handleChannelToggle(channel)}
                      className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                    />
                    <span className="text-sm font-medium text-gray-700 capitalize">{channel}</span>
                  </label>
                ))}
              </div>
            </div>
            
            {/* Rate Limiting */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Rate Limiting</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Max Per Hour
                  </label>
                  <input
                    type="number"
                    value={preferences.max_notifications_per_hour}
                    onChange={(e) => setPreferences({ ...preferences, max_notifications_per_hour: parseInt(e.target.value) || 0 })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    min="1"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Max Per Day
                  </label>
                  <input
                    type="number"
                    value={preferences.max_notifications_per_day}
                    onChange={(e) => setPreferences({ ...preferences, max_notifications_per_day: parseInt(e.target.value) || 0 })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    min="1"
                  />
                </div>
              </div>
            </div>
            
            {/* Quiet Hours */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Quiet Hours</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Start Time
                  </label>
                  <input
                    type="time"
                    value={preferences.quiet_hours_start || ''}
                    onChange={(e) => setPreferences({ ...preferences, quiet_hours_start: e.target.value || undefined })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    End Time
                  </label>
                  <input
                    type="time"
                    value={preferences.quiet_hours_end || ''}
                    onChange={(e) => setPreferences({ ...preferences, quiet_hours_end: e.target.value || undefined })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
            </div>
            
            {/* Timezone */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Timezone
              </label>
              <select
                value={preferences.timezone}
                onChange={(e) => setPreferences({ ...preferences, timezone: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="UTC">UTC</option>
                <option value="America/New_York">Eastern Time</option>
                <option value="America/Chicago">Central Time</option>
                <option value="America/Denver">Mountain Time</option>
                <option value="America/Los_Angeles">Pacific Time</option>
              </select>
            </div>
          </div>
          
          {/* Actions */}
          <div className="flex gap-3 mt-6 pt-6 border-t border-gray-200">
            <button
              onClick={onClose}
              disabled={loading}
              className="flex-1 px-6 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={loading}
              className="flex-1 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Saving...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4" />
                  Save Settings
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
