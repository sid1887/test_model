/**
 * Compare Drawer Component
 * Shows real-time comparison progress with SSE
 */

import React, { useEffect, useState } from 'react';
import { X, TrendingDown, Check, Loader } from 'lucide-react';
import { API_BASE_URL } from '../../config/env';

interface CompareDrawerProps {
  jobId: string;
  onClose: () => void;
}

interface CompareResult {
  best_store: string;
  total_price: number;
  potential_savings: number;
  items: Array<{
    product_id: number;
    retailer: string;
    price: number;
  }>;
}

export const CompareDrawer: React.FC<CompareDrawerProps> = ({ jobId, onClose }) => {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<'running' | 'completed' | 'failed'>('running');
  const [result, setResult] = useState<CompareResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [processedItems, setProcessedItems] = useState<number>(0);
  const [totalItems, setTotalItems] = useState<number>(0);

  useEffect(() => {
    // Connect to SSE stream for progress updates
    const eventSource = new EventSource(`${API_BASE_URL}/api/lists/compare/${jobId}/progress`);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.progress !== undefined) {
          setProgress(data.progress);
        }
        
        if (data.processed_items !== undefined) {
          setProcessedItems(data.processed_items);
        }
        
        if (data.total_items !== undefined) {
          setTotalItems(data.total_items);
        }
        
        if (data.status) {
          setStatus(data.status);
        }
        
        if (data.status === 'completed' && data.result) {
          setResult(data.result);
          eventSource.close();
        }
        
        if (data.status === 'failed') {
          setError(data.error || 'Comparison failed');
          eventSource.close();
        }
      } catch (err) {
        console.error('Failed to parse SSE data:', err);
      }
    };

    eventSource.onerror = () => {
      console.error('SSE connection error');
      eventSource.close();
      // Try to fetch final result
      fetchResult();
    };

    return () => {
      eventSource.close();
    };
  }, [jobId]);

  const fetchResult = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/lists/compare/${jobId}`);
      if (!response.ok) throw new Error('Failed to fetch result');
      const data = await response.json();
      
      if (data.status === 'completed') {
        setResult(data.result);
        setStatus('completed');
        setProgress(100);
      } else if (data.status === 'failed') {
        setError(data.error || 'Comparison failed');
        setStatus('failed');
      }
    } catch (err) {
      console.error('Failed to fetch comparison result:', err);
      setError('Failed to fetch result');
      setStatus('failed');
    }
  };

  return (
    <div className="fixed inset-y-0 right-0 w-full md:w-1/2 lg:w-1/3 bg-white shadow-2xl z-50 overflow-y-auto">
      {/* Header */}
      <div className="sticky top-0 bg-white border-b border-gray-200 p-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <TrendingDown className="h-6 w-6 text-green-600" />
          <h2 className="text-xl font-bold text-gray-900">Price Comparison</h2>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 transition-colors"
        >
          <X className="h-6 w-6" />
        </button>
      </div>

      {/* Content */}
      <div className="p-6">
        {status === 'running' && (
          <div>
            <div className="mb-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">
                  Comparing prices...
                </span>
                <span className="text-sm font-medium text-gray-900">
                  {progress.toFixed(0)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-green-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
              <p className="text-sm text-gray-600 mt-2">
                {processedItems} of {totalItems} items processed
              </p>
            </div>

            <div className="flex items-center gap-3 text-gray-600">
              <Loader className="h-5 w-5 animate-spin" />
              <span>Finding best prices across retailers...</span>
            </div>
          </div>
        )}

        {status === 'failed' && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-red-900 mb-2">Comparison Failed</h3>
            <p className="text-red-700">{error || 'An error occurred during comparison'}</p>
            <button
              onClick={onClose}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Close
            </button>
          </div>
        )}

        {status === 'completed' && result && (
          <div>
            {/* Summary Card */}
            <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
              <div className="flex items-center gap-2 mb-4">
                <Check className="h-6 w-6 text-green-600" />
                <h3 className="text-lg font-semibold text-green-900">Best Deal Found!</h3>
              </div>
              
              <div className="space-y-3">
                <div>
                  <p className="text-sm text-gray-600">Best Store</p>
                  <p className="text-2xl font-bold text-gray-900">{result.best_store}</p>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-600">Total Price</p>
                    <p className="text-xl font-bold text-gray-900">
                      ${result.total_price.toFixed(2)}
                    </p>
                  </div>
                  
                  <div>
                    <p className="text-sm text-gray-600">Potential Savings</p>
                    <p className="text-xl font-bold text-green-600">
                      ${result.potential_savings.toFixed(2)}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Items Breakdown */}
            <div>
              <h4 className="text-lg font-semibold text-gray-900 mb-4">Items Breakdown</h4>
              <div className="space-y-3">
                {result.items.map((item, index) => (
                  <div
                    key={index}
                    className="bg-gray-50 rounded-lg p-4 flex items-center justify-between"
                  >
                    <div>
                      <p className="font-medium text-gray-900">Product #{item.product_id}</p>
                      <p className="text-sm text-gray-600">{item.retailer}</p>
                    </div>
                    <p className="text-lg font-bold text-gray-900">
                      ${item.price.toFixed(2)}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="mt-6 pt-6 border-t border-gray-200">
              <button
                onClick={onClose}
                className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                Done
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
