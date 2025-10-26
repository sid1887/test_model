/**
 * Analytics Page Component
 * Main page for viewing analytics and insights
 */

import React, { useState, useEffect, useCallback } from 'react';
import { TrendingUp, BarChart3, Brain, DollarSign } from 'lucide-react';
import { useAnalytics } from '../hooks/useAnalytics';
import { AnalyticsOverview } from '../types/alerts';
import { TrendExplorer } from '../components/analytics/TrendExplorer';
import { ForecastDisplay } from '../components/analytics/ForecastDisplay';
import { SentimentPanel } from '../components/analytics/SentimentPanel';
import { RetailerComparison } from '../components/analytics/RetailerComparison';

export const AnalyticsPage: React.FC = () => {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [activeTab, setActiveTab] = useState<'trends' | 'forecast' | 'sentiment' | 'retailers'>('trends');
  const [selectedProductId, setSelectedProductId] = useState<number>(1);
  const { getOverview, loading } = useAnalytics();

  const loadOverview = useCallback(async () => {
    const data = await getOverview();
    if (data) setOverview(data);
  }, [getOverview]);

  useEffect(() => {
    loadOverview();
  }, [loadOverview]);

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Analytics & Insights</h1>
            <p className="text-gray-600 mt-1">Track trends, forecasts, and market intelligence</p>
          </div>
          <div className="flex items-center gap-3">
            <label className="text-sm font-medium text-gray-700">Product ID:</label>
            <input
              type="number"
              value={selectedProductId}
              onChange={(e) => setSelectedProductId(parseInt(e.target.value) || 1)}
              className="w-32 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              min="1"
            />
          </div>
        </div>

        {/* Overview Stats */}
        {overview && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6">
            <div className="bg-white rounded-lg shadow p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Products Tracked</p>
                  <p className="text-2xl font-bold text-gray-900">{overview.total_products}</p>
                </div>
                <BarChart3 className="h-8 w-8 text-blue-600" />
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Avg. Price Change</p>
                  <p className={`text-2xl font-bold ${(overview?.avg_price_change ?? 0) >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                    {(overview?.avg_price_change ?? 0) >= 0 ? '+' : ''}{(overview?.avg_price_change ?? 0).toFixed(1)}%
                  </p>
                </div>
                <TrendingUp className="h-8 w-8 text-green-600" />
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Total Savings</p>
                  <p className="text-2xl font-bold text-gray-900">${(overview?.total_savings ?? 0).toFixed(2)}</p>
                </div>
                <DollarSign className="h-8 w-8 text-yellow-600" />
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Forecasts Generated</p>
                  <p className="text-2xl font-bold text-gray-900">{overview?.forecasts_generated ?? 0}</p>
                </div>
                <Brain className="h-8 w-8 text-purple-600" />
              </div>
            </div>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="mt-6 bg-white rounded-lg shadow p-2 flex gap-2">
          <button
            onClick={() => setActiveTab('trends')}
            className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors flex items-center justify-center gap-2 ${
              activeTab === 'trends'
                ? 'bg-blue-600 text-white'
                : 'text-gray-700 hover:bg-gray-100'
            }`}
          >
            <TrendingUp className="h-4 w-4" />
            Price Trends
          </button>
          <button
            onClick={() => setActiveTab('forecast')}
            className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors flex items-center justify-center gap-2 ${
              activeTab === 'forecast'
                ? 'bg-blue-600 text-white'
                : 'text-gray-700 hover:bg-gray-100'
            }`}
          >
            <Brain className="h-4 w-4" />
            Forecast
          </button>
          <button
            onClick={() => setActiveTab('sentiment')}
            className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors flex items-center justify-center gap-2 ${
              activeTab === 'sentiment'
                ? 'bg-blue-600 text-white'
                : 'text-gray-700 hover:bg-gray-100'
            }`}
          >
            <BarChart3 className="h-4 w-4" />
            Sentiment
          </button>
          <button
            onClick={() => setActiveTab('retailers')}
            className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors flex items-center justify-center gap-2 ${
              activeTab === 'retailers'
                ? 'bg-blue-600 text-white'
                : 'text-gray-700 hover:bg-gray-100'
            }`}
          >
            <DollarSign className="h-4 w-4" />
            Retailer Compare
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto">
        {loading ? (
          <div className="flex justify-center py-12 bg-white rounded-lg shadow">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <>
            {activeTab === 'trends' && <TrendExplorer productId={selectedProductId} />}
            {activeTab === 'forecast' && <ForecastDisplay productId={selectedProductId} />}
            {activeTab === 'sentiment' && <SentimentPanel productId={selectedProductId} />}
            {activeTab === 'retailers' && <RetailerComparison productId={selectedProductId} />}
          </>
        )}
      </div>
    </div>
  );
};
