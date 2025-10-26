/**
 * Alert Card Component
 * Displays individual alert with actions
 */

import React from 'react';
import { Eye, Pause, Play, Trash2, RefreshCw, TrendingDown, Clock } from 'lucide-react';
import { Alert } from '../../types/alerts';
import { formatDistanceToNow } from 'date-fns';

interface AlertCardProps {
  alert: Alert;
  onView: () => void;
  onPause: () => void;
  onResume: () => void;
  onTrigger: () => void;
  onDelete: () => void;
}

export const AlertCard: React.FC<AlertCardProps> = ({
  alert,
  onView,
  onPause,
  onResume,
  onTrigger,
  onDelete,
}) => {
  const getStatusColor = () => {
    switch (alert.status) {
      case 'active':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'paused':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'fired':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'expired':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getOperatorSymbol = () => {
    const operators = {
      '<=': '≤',
      '<': '<',
      '>': '>',
      '>=': '≥',
      '==': '=',
      'percent_off': '%'
    };
    return operators[alert.operator] || alert.operator;
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor()}`}>
              {alert.status}
            </span>
            {alert.priority === 'urgent' && (
              <span className="px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800 border border-red-200">
                Urgent
              </span>
            )}
          </div>
          
          <button
            onClick={onDelete}
            className="text-gray-400 hover:text-red-600 transition-colors"
            title="Delete alert"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
        
        <h3 className="font-medium text-gray-900 mb-1">
          Product #{alert.product_id}
        </h3>
        
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <TrendingDown className="h-4 w-4" />
          <span className="font-medium">
            Price {getOperatorSymbol()} ${alert.target_price.toFixed(2)}
          </span>
        </div>
      </div>
      
      {/* Details */}
      <div className="p-4 space-y-3">
        {/* Fire Count */}
        {alert.fire_count > 0 && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Fired:</span>
            <span className="font-medium text-gray-900">{alert.fire_count} times</span>
          </div>
        )}
        
        {/* Last Checked */}
        {alert.last_checked_at && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600 flex items-center gap-1">
              <Clock className="h-3 w-3" />
              Last checked:
            </span>
            <span className="text-gray-900">
              {formatDistanceToNow(new Date(alert.last_checked_at), { addSuffix: true })}
            </span>
          </div>
        )}
        
        {/* Channels */}
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Channels:</span>
          <div className="flex gap-1">
            {alert.channels.map((channel) => (
              <span
                key={channel}
                className="px-2 py-0.5 bg-gray-100 text-gray-700 rounded text-xs"
              >
                {channel}
              </span>
            ))}
          </div>
        </div>
        
        {/* Frequency */}
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Frequency:</span>
          <span className="text-gray-900 capitalize">{alert.frequency}</span>
        </div>
        
        {/* Notes */}
        {alert.notes && (
          <div className="text-sm text-gray-600 italic pt-2 border-t border-gray-100">
            "{alert.notes}"
          </div>
        )}
      </div>
      
      {/* Actions */}
      <div className="p-4 border-t border-gray-200 bg-gray-50 flex gap-2">
        <button
          onClick={onView}
          className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50 transition-colors"
        >
          <Eye className="h-4 w-4" />
          Details
        </button>
        
        {alert.status === 'active' ? (
          <>
            <button
              onClick={onPause}
              className="flex items-center justify-center gap-2 px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50 transition-colors"
              title="Pause alert"
            >
              <Pause className="h-4 w-4" />
            </button>
            <button
              onClick={onTrigger}
              className="flex items-center justify-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 transition-colors"
              title="Check now"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
          </>
        ) : alert.status === 'paused' ? (
          <button
            onClick={onResume}
            className="flex items-center justify-center gap-2 px-3 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700 transition-colors"
            title="Resume alert"
          >
            <Play className="h-4 w-4" />
          </button>
        ) : null}
      </div>
    </div>
  );
};
