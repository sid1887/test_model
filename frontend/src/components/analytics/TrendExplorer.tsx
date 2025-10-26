/**
 * Trend Explorer Component
 * Displays price trends over time with simple visualization
 */

import React, { useEffect, useState } from 'react';
import { Calendar, Download, TrendingDown, TrendingUp } from 'lucide-react';
import { useAnalytics } from '../../hooks/useAnalytics';
import { PriceTrend } from '../../types/alerts';
import { formatDistanceToNow } from 'date-fns';

interface TrendExplorerProps {
  productId: number;
}

export const TrendExplorer: React.FC<TrendExplorerProps> = ({ productId }) => {
  const [trends, setTrends] = useState<PriceTrend | null>(null);
  const [days, setDays] = useState<number>(30);
  const { getPriceTrends, loading, error } = useAnalytics();

  const loadTrends = React.useCallback(async () => {
    const data = await getPriceTrends(productId, days);
    if (data) setTrends(Array.isArray(data) ? data[0] : data);
  }, [getPriceTrends, productId, days]);

  useEffect(() => {
    loadTrends();
  }, [loadTrends]);

  const calculateStats = () => {
    if (!trends || trends.data_points.length === 0) return { min: 0, max: 0, avg: 0, change: 0 };
    
    const prices = trends.data_points.map(t => t.price);
    const min = Math.min(...prices);
    const max = Math.max(...prices);
    const avg = prices.reduce((a, b) => a + b, 0) / prices.length;
    const change = trends.data_points.length > 1 
      ? ((trends.data_points[trends.data_points.length - 1].price - trends.data_points[0].price) / trends.data_points[0].price) * 100
      : 0;
    
    return { min, max, avg, change };
  };

  const stats = calculateStats();

  return (
    <div className="bg-white rounded-lg shadow p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-gray-900">Price Trends</h2>
        <div className="flex items-center gap-3">
          <select
            value={days}
            onChange={(e) => setDays(parseInt(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="7">Last 7 days</option>
            <option value="14">Last 14 days</option>
            <option value="30">Last 30 days</option>
            <option value="60">Last 60 days</option>
            <option value="90">Last 90 days</option>
          </select>
          <button className="px-4 py-2 bg-blue-100 text-blue-600 rounded-lg hover:bg-blue-200 transition-colors flex items-center gap-2">
            <Download className="h-4 w-4" />
            Export
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-blue-50 rounded-lg p-4">
          <p className="text-sm text-gray-600 mb-1">Current Price</p>
          <p className="text-2xl font-bold text-gray-900">
            ${trends && trends.data_points.length > 0 ? trends.data_points[trends.data_points.length - 1].price.toFixed(2) : '0.00'}
          </p>
        </div>
        <div className="bg-green-50 rounded-lg p-4">
          <p className="text-sm text-gray-600 mb-1">Lowest Price</p>
          <p className="text-2xl font-bold text-green-600">${stats.min.toFixed(2)}</p>
        </div>
        <div className="bg-red-50 rounded-lg p-4">
          <p className="text-sm text-gray-600 mb-1">Highest Price</p>
          <p className="text-2xl font-bold text-red-600">${stats.max.toFixed(2)}</p>
        </div>
        <div className="bg-purple-50 rounded-lg p-4">
          <p className="text-sm text-gray-600 mb-1">Price Change</p>
          <div className="flex items-center gap-2">
            <p className={`text-2xl font-bold ${stats.change >= 0 ? 'text-red-600' : 'text-green-600'}`}>
              {stats.change >= 0 ? '+' : ''}{stats.change.toFixed(1)}%
            </p>
            {stats.change >= 0 ? (
              <TrendingUp className="h-5 w-5 text-red-600" />
            ) : (
              <TrendingDown className="h-5 w-5 text-green-600" />
            )}
          </div>
        </div>
      </div>

      {/* Chart Placeholder / Simple List */}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700">{error}</p>
        </div>
      ) : !trends || trends.data_points.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <Calendar className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">No price data available</p>
        </div>
      ) : (
        <div>
          {/* Simple Bar Chart Representation */}
          <div className="mb-6">
            <div className="flex items-end gap-2 h-64">
              {trends.data_points.slice(0, 30).map((dataPoint, index) => {
                const heightPercent = ((dataPoint.price - stats.min) / (stats.max - stats.min)) * 100;
                return (
                  <div key={index} className="flex-1 flex flex-col items-center group">
                    <div className="relative w-full">
                      <div
                        className="w-full bg-blue-500 hover:bg-blue-600 transition-colors rounded-t cursor-pointer"
                        style={{ height: `${Math.max(heightPercent, 5)}%` }}
                        title={`$${dataPoint.price.toFixed(2)} on ${new Date(dataPoint.timestamp).toLocaleDateString()}`}
                      ></div>
                    </div>
                  </div>
                );
              })}
            </div>
            <div className="flex justify-between mt-2 text-xs text-gray-600">
              <span>{new Date(trends.data_points[0].timestamp).toLocaleDateString()}</span>
              <span>{new Date(trends.data_points[trends.data_points.length - 1].timestamp).toLocaleDateString()}</span>
            </div>
          </div>

          {/* Data Table */}
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Date</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Price</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Retailer</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Availability</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Time Ago</th>
                </tr>
              </thead>
              <tbody>
                {trends && trends.data_points.slice().reverse().slice(0, 10).map((dataPoint, index) => (
                  <tr key={index} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4 text-sm text-gray-900">
                      {new Date(dataPoint.timestamp).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 text-sm font-medium text-gray-900">
                      ${dataPoint.price.toFixed(2)}
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-900">{dataPoint.retailer_name || 'Unknown'}</td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">
                        In Stock
                      </span>
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600">
                      {formatDistanceToNow(new Date(dataPoint.timestamp), { addSuffix: true })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
