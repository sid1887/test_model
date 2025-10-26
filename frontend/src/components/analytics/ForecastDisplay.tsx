/**
 * Forecast Display Component
 * Shows price predictions and best buy recommendations
 */

import React, { useEffect, useState } from 'react';
import { Brain, Calendar, TrendingDown, AlertCircle } from 'lucide-react';
import { useAnalytics } from '../../hooks/useAnalytics';
import { ProductForecast } from '../../types/alerts';

interface ForecastDisplayProps {
  productId: number;
}

export const ForecastDisplay: React.FC<ForecastDisplayProps> = ({ productId }) => {
  const [forecast, setForecast] = useState<ProductForecast | null>(null);
  const [days, setDays] = useState<number>(7);
  const { getForecast, loading, error } = useAnalytics();

  useEffect(() => {
    loadForecast();
  }, [productId, days]);

  const loadForecast = async () => {
    const data = await getForecast(productId, days);
    if (data) setForecast(data);
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Brain className="h-6 w-6 text-purple-600" />
          <h2 className="text-xl font-bold text-gray-900">Price Forecast</h2>
        </div>
        <select
          value={days}
          onChange={(e) => setDays(parseInt(e.target.value))}
          className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="7">Next 7 days</option>
          <option value="14">Next 14 days</option>
          <option value="30">Next 30 days</option>
        </select>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700">{error}</p>
        </div>
      ) : !forecast ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <Brain className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">No forecast available</p>
        </div>
      ) : (
        <div>
          {/* Best Buy Recommendation */}
          {forecast.best_buy_date && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
              <div className="flex items-start gap-4">
                <Calendar className="h-8 w-8 text-green-600 flex-shrink-0" />
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-green-900 mb-2">
                    Best Time to Buy
                  </h3>
                  <p className="text-gray-700 mb-3">{forecast.recommendation}</p>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-600">Predicted Date</p>
                      <p className="text-lg font-bold text-gray-900">
                        {new Date(forecast.best_buy_date).toLocaleDateString()}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Expected Price</p>
                      <p className="text-lg font-bold text-green-600">
                        ${forecast.best_buy_price?.toFixed(2)}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Model Info */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Current Price</p>
              <p className="text-2xl font-bold text-gray-900">${forecast.current_price.toFixed(2)}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Model Type</p>
              <p className="text-lg font-medium text-gray-900 uppercase">{forecast.model_type}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Confidence</p>
              <p className="text-2xl font-bold text-gray-900">
                {(forecast.confidence_interval * 100).toFixed(0)}%
              </p>
            </div>
          </div>

          {/* Trend Analysis */}
          {forecast.trend_analysis && (
            <div className="mb-6 p-4 bg-blue-50 rounded-lg">
              <div className="flex items-center gap-3 mb-3">
                <TrendingDown className="h-5 w-5 text-blue-600" />
                <h4 className="font-semibold text-gray-900">Trend Analysis</h4>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-600">Direction</p>
                  <p className="font-medium text-gray-900 capitalize">
                    {forecast.trend_analysis.direction}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Strength</p>
                  <p className="font-medium text-gray-900">
                    {forecast.trend_analysis.strength_percent.toFixed(1)}%
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Start Price</p>
                  <p className="font-medium text-gray-900">
                    ${forecast.trend_analysis.start_price.toFixed(2)}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">End Price</p>
                  <p className="font-medium text-gray-900">
                    ${forecast.trend_analysis.end_price.toFixed(2)}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Predictions Table */}
          <div>
            <h4 className="text-lg font-semibold text-gray-900 mb-4">Price Predictions</h4>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Date</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Predicted Price</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Range</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Confidence</th>
                  </tr>
                </thead>
                <tbody>
                  {forecast.predictions.map((pred, index) => (
                    <tr key={index} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4 text-sm text-gray-900">
                        {new Date(pred.date).toLocaleDateString()}
                      </td>
                      <td className="py-3 px-4 text-sm font-medium text-gray-900">
                        ${pred.predicted_price.toFixed(2)}
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-600">
                        ${pred.lower_bound.toFixed(2)} - ${pred.upper_bound.toFixed(2)}
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          <div className="flex-1 bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-purple-600 h-2 rounded-full"
                              style={{ width: `${pred.confidence * 100}%` }}
                            ></div>
                          </div>
                          <span className="text-sm text-gray-600">
                            {(pred.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Model Accuracy */}
          {(forecast.mae || forecast.rmse) && (
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2 mb-3">
                <AlertCircle className="h-5 w-5 text-gray-600" />
                <h4 className="font-semibold text-gray-900">Model Accuracy</h4>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                {forecast.mae && (
                  <div>
                    <p className="text-gray-600">Mean Absolute Error</p>
                    <p className="font-medium text-gray-900">${forecast.mae.toFixed(2)}</p>
                  </div>
                )}
                {forecast.rmse && (
                  <div>
                    <p className="text-gray-600">Root Mean Square Error</p>
                    <p className="font-medium text-gray-900">${forecast.rmse.toFixed(2)}</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
