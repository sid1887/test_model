/**
 * List Detail View Component
 * Shows detailed view of a list with items
 */

import React, { useState, useEffect, useCallback } from 'react';
import { ArrowLeft, Plus, Save, Share2, TrendingDown, Trash2 } from 'lucide-react';
import { SmartList, SmartListItem } from '../../types/alerts';
import { useSmartLists } from '../../hooks/useSmartLists';
import { API_BASE_URL } from '../../config/env';

interface ListDetailViewProps {
  list: SmartList;
  onBack: () => void;
  onDelete: () => void;
  onCompare: () => void;
}

export const ListDetailView: React.FC<ListDetailViewProps> = ({
  list,
  onBack,
  onDelete,
  onCompare,
}) => {
  const [items, setItems] = useState<SmartListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddItem, setShowAddItem] = useState(false);
  const [newItemProductId, setNewItemProductId] = useState('');
  const [newItemQuantity, setNewItemQuantity] = useState('1');
  const [newItemDesiredPrice, setNewItemDesiredPrice] = useState('');
  const { addItem, removeItem, generateShareToken } = useSmartLists();

  const fetchItems = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/lists/${list.id}/items`);
      if (!response.ok) throw new Error('Failed to fetch items');
      const data = await response.json();
      setItems(data.items || data);
    } catch (err) {
      console.error('Failed to fetch items:', err);
    } finally {
      setLoading(false);
    }
  }, [list.id]);

  useEffect(() => {
    fetchItems();
  }, [fetchItems]);

  const handleAddItem = async () => {
    if (!newItemProductId) return;

    try {
      await addItem(list.id, {
        product_id: parseInt(newItemProductId),
        quantity: parseInt(newItemQuantity) || 1,
        desired_price: newItemDesiredPrice ? parseFloat(newItemDesiredPrice) : undefined,
      });
      setShowAddItem(false);
      setNewItemProductId('');
      setNewItemQuantity('1');
      setNewItemDesiredPrice('');
      await fetchItems();
    } catch (err) {
      console.error('Failed to add item:', err);
    }
  };

  const handleRemoveItem = async (itemId: number) => {
    try {
      await removeItem(list.id, itemId);
      await fetchItems();
    } catch (err) {
      console.error('Failed to remove item:', err);
    }
  };

  const handleShare = async () => {
    try {
      const result = await generateShareToken(list.id, 7);
      const shareUrl = `${window.location.origin}/lists/shared/${result.token}`;
      await navigator.clipboard.writeText(shareUrl);
      alert('Share link copied to clipboard!');
    } catch (err) {
      console.error('Failed to generate share link:', err);
    }
  };

  const totalValue = items.reduce((sum, item) => sum + (item.current_price || 0) * item.quantity, 0);
  const totalDesired = items.reduce((sum, item) => sum + (item.desired_price || 0) * item.quantity, 0);
  const potentialSavings = totalDesired > 0 ? totalValue - totalDesired : 0;

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <button
            onClick={onBack}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
            Back to Lists
          </button>
          <div className="flex gap-2">
            <button
              onClick={handleShare}
              className="px-4 py-2 bg-blue-100 text-blue-600 rounded-lg hover:bg-blue-200 transition-colors flex items-center gap-2"
            >
              <Share2 className="h-4 w-4" />
              Share
            </button>
            <button
              onClick={onCompare}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2"
            >
              <TrendingDown className="h-4 w-4" />
              Compare Prices
            </button>
            <button
              onClick={onDelete}
              className="px-4 py-2 bg-red-100 text-red-600 rounded-lg hover:bg-red-200 transition-colors flex items-center gap-2"
            >
              <Trash2 className="h-4 w-4" />
              Delete
            </button>
          </div>
        </div>

        <h1 className="text-3xl font-bold text-gray-900 mb-2">{list.name}</h1>
        {list.description && (
          <p className="text-gray-600">{list.description}</p>
        )}

        {/* Stats */}
        <div className="grid grid-cols-4 gap-4 mt-6">
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-sm text-gray-600">Items</p>
            <p className="text-2xl font-bold text-gray-900">{items.length}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-sm text-gray-600">Current Total</p>
            <p className="text-2xl font-bold text-gray-900">${totalValue.toFixed(2)}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-sm text-gray-600">Desired Total</p>
            <p className="text-2xl font-bold text-gray-900">${totalDesired.toFixed(2)}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-sm text-gray-600">Potential Savings</p>
            <p className={`text-2xl font-bold ${potentialSavings < 0 ? 'text-green-600' : 'text-gray-900'}`}>
              ${Math.abs(potentialSavings).toFixed(2)}
            </p>
          </div>
        </div>
      </div>

      {/* Items List */}
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Items</h2>
          <button
            onClick={() => setShowAddItem(!showAddItem)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            Add Item
          </button>
        </div>

        {/* Add Item Form */}
        {showAddItem && (
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Product ID *
                </label>
                <input
                  type="number"
                  value={newItemProductId}
                  onChange={(e) => setNewItemProductId(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="123"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Quantity
                </label>
                <input
                  type="number"
                  value={newItemQuantity}
                  onChange={(e) => setNewItemQuantity(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  min="1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Desired Price
                </label>
                <input
                  type="number"
                  value={newItemDesiredPrice}
                  onChange={(e) => setNewItemDesiredPrice(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="0.00"
                  step="0.01"
                />
              </div>
            </div>
            <div className="flex gap-2 mt-4">
              <button
                onClick={handleAddItem}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
              >
                <Save className="h-4 w-4" />
                Add Item
              </button>
              <button
                onClick={() => setShowAddItem(false)}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Items Table */}
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : items.length === 0 ? (
          <div className="text-center py-12 bg-gray-50 rounded-lg">
            <p className="text-gray-600">No items in this list yet</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Product ID</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Quantity</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Current Price</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Desired Price</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Available</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Actions</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4 text-sm text-gray-900">#{item.product_id}</td>
                    <td className="py-3 px-4 text-sm text-gray-900">{item.quantity}</td>
                    <td className="py-3 px-4 text-sm text-gray-900">
                      {item.current_price ? `$${item.current_price.toFixed(2)}` : '-'}
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-900">
                      {item.desired_price ? `$${item.desired_price.toFixed(2)}` : '-'}
                    </td>
                    <td className="py-3 px-4">
                      {item.is_available ? (
                        <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">
                          In Stock
                        </span>
                      ) : (
                        <span className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded-full">
                          Out of Stock
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <button
                        onClick={() => handleRemoveItem(item.id)}
                        className="text-red-600 hover:text-red-800 transition-colors"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
