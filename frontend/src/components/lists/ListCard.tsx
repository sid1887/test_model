/**
 * List Card Component
 * Displays a smart list in card format
 */

import React from 'react';
import { Eye, Trash2, TrendingDown, Calendar, ShoppingCart } from 'lucide-react';
import { SmartList } from '../../types/alerts';
import { formatDistanceToNow } from 'date-fns';

interface ListCardProps {
  list: SmartList;
  onView: () => void;
  onDelete: () => void;
  onCompare: () => void;
}

export const ListCard: React.FC<ListCardProps> = ({
  list,
  onView,
  onDelete,
  onCompare,
}) => {
  return (
    <div className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-1">{list.name}</h3>
          {list.description && (
            <p className="text-sm text-gray-600 line-clamp-2">{list.description}</p>
          )}
        </div>
        <ShoppingCart className="h-6 w-6 text-blue-600 flex-shrink-0 ml-2" />
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 mb-4 py-3 border-t border-b border-gray-100">
        <div>
          <p className="text-xs text-gray-600">Items</p>
          <p className="text-xl font-bold text-gray-900">{list.item_count}</p>
        </div>
        <div>
          <p className="text-xs text-gray-600">Total Value</p>
          <p className="text-xl font-bold text-gray-900">
            ${list.total_value?.toFixed(2) || '0.00'}
          </p>
        </div>
      </div>

      {/* Last Updated */}
      <div className="flex items-center gap-2 text-sm text-gray-600 mb-4">
        <Calendar className="h-4 w-4" />
        <span>
          Updated {list.updated_at ? formatDistanceToNow(new Date(list.updated_at), { addSuffix: true }) : 'Never'}
        </span>
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        <button
          onClick={onView}
          className="flex-1 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center gap-2 text-sm"
        >
          <Eye className="h-4 w-4" />
          View
        </button>
        <button
          onClick={onCompare}
          className="flex-1 px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center gap-2 text-sm"
        >
          <TrendingDown className="h-4 w-4" />
          Compare
        </button>
        <button
          onClick={onDelete}
          className="px-3 py-2 bg-red-100 text-red-600 rounded-lg hover:bg-red-200 transition-colors"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
};
