/**
 * Retailer Comparison Component
 * Compares prices across retailers
 */

import React, { useEffect, useState } from 'react';
import { Store, TrendingDown, Clock, Package } from 'lucide-react';
import { useAnalytics } from '../../hooks/useAnalytics';

interface RetailerComparisonProps {
  productId: number;
}

interface RetailerData {
  retailer_id: number;
  retailer_name: string;
  price: number;
  availability: boolean;
  delivery_time_days: number;
  rating: number;
}

export const RetailerComparison: React.FC<RetailerComparisonProps> = ({ productId }) => {
  const [retailers, setRetailers] = useState<RetailerData[]>([]);
  const { compareRetailers, loading, error } = useAnalytics();

  useEffect(() => {
    loadComparison();
  }, [productId]);

  const loadComparison = async () => {
    const data = await compareRetailers([productId]);
    if (data && data.retailers) {
      setRetailers(data.retailers);
    }
  };

  const sortedRetailers = [...retailers].sort((a, b) => a.price - b.price);
  const lowestPrice = sortedRetailers.length > 0 ? sortedRetailers[0].price : 0;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <Store className="h-6 w-6 text-blue-600" />
        <h2 className="text-xl font-bold text-gray-900">Retailer Comparison</h2>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700">{error}</p>
        </div>
      ) : retailers.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <Store className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">No retailer data available</p>
        </div>
      ) : (
        <div>
          {/* Summary Stats */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-green-50 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Best Price</p>
              <p className="text-2xl font-bold text-green-600">${lowestPrice.toFixed(2)}</p>
              <p className="text-xs text-gray-600 mt-1">{sortedRetailers[0]?.retailer_name}</p>
            </div>
            <div className="bg-blue-50 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Avg Price</p>
              <p className="text-2xl font-bold text-gray-900">
                ${(retailers.reduce((sum, r) => sum + r.price, 0) / retailers.length).toFixed(2)}
              </p>
            </div>
            <div className="bg-purple-50 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Price Range</p>
              <p className="text-2xl font-bold text-gray-900">
                ${(Math.max(...retailers.map(r => r.price)) - lowestPrice).toFixed(2)}
              </p>
            </div>
          </div>

          {/* Retailers List */}
          <div className="space-y-3">
            {sortedRetailers.map((retailer, index) => {
              const savings = retailer.price - lowestPrice;
              const savingsPercent = lowestPrice > 0 ? ((savings / lowestPrice) * 100) : 0;
              const isBest = index === 0;

              return (
                <div
                  key={retailer.retailer_id}
                  className={`border rounded-lg p-4 ${
                    isBest ? 'border-green-500 bg-green-50' : 'border-gray-200 hover:border-gray-300'
                  } transition-colors`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4 flex-1">
                      <div className={`p-3 rounded-lg ${isBest ? 'bg-green-100' : 'bg-gray-100'}`}>
                        <Store className={`h-6 w-6 ${isBest ? 'text-green-600' : 'text-gray-600'}`} />
                      </div>
                      
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-lg font-semibold text-gray-900">
                            {retailer.retailer_name}
                          </h3>
                          {isBest && (
                            <span className="px-2 py-1 bg-green-600 text-white text-xs rounded-full font-medium">
                              Best Deal
                            </span>
                          )}
                        </div>
                        
                        <div className="flex items-center gap-4 text-sm text-gray-600">
                          <div className="flex items-center gap-1">
                            <Package className="h-4 w-4" />
                            <span>{retailer.availability ? 'In Stock' : 'Out of Stock'}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Clock className="h-4 w-4" />
                            <span>{retailer.delivery_time_days} days delivery</span>
                          </div>
                          {retailer.rating && (
                            <div className="flex items-center gap-1">
                              <span>⭐</span>
                              <span>{retailer.rating.toFixed(1)}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    <div className="text-right">
                      <p className={`text-3xl font-bold ${isBest ? 'text-green-600' : 'text-gray-900'}`}>
                        ${retailer.price.toFixed(2)}
                      </p>
                      {!isBest && savings > 0 && (
                        <div className="flex items-center gap-1 mt-1">
                          <TrendingDown className="h-4 w-4 text-red-600" />
                          <span className="text-sm text-red-600">
                            +${savings.toFixed(2)} ({savingsPercent.toFixed(0)}%)
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Recommendation */}
          <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h4 className="font-semibold text-gray-900 mb-2">💡 Recommendation</h4>
            <p className="text-sm text-gray-700">
              Save ${(sortedRetailers[sortedRetailers.length - 1]?.price - lowestPrice).toFixed(2)} by 
              purchasing from <strong>{sortedRetailers[0]?.retailer_name}</strong> instead of{' '}
              <strong>{sortedRetailers[sortedRetailers.length - 1]?.retailer_name}</strong>.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
