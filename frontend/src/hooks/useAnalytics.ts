/**
 * Custom hook for Analytics operations
 */

import { useState, useCallback } from 'react';
import { PriceTrend, ProductForecast, SentimentAnalysis, AnalyticsOverview } from '../types/alerts';
import { API_BASE_URL } from '../config/env';

export const useAnalytics = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Get analytics overview
  const getOverview = useCallback(async (): Promise<AnalyticsOverview | null> => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_BASE_URL}/api/analytics/overview`);
      if (!response.ok) throw new Error('Failed to fetch overview');
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch overview');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  // Get price trends
  const getPriceTrends = useCallback(async (
    productId: number,
    days: number = 30,
    retailerId?: number
  ): Promise<PriceTrend[] | null> => {
    try {
      setLoading(true);
      setError(null);
      const params = new URLSearchParams({
        product_id: productId.toString(),
        days: days.toString(),
        ...(retailerId && { retailer_id: retailerId.toString() }),
      });
      const response = await fetch(`${API_BASE_URL}/api/analytics/trends?${params}`);
      if (!response.ok) throw new Error('Failed to fetch price trends');
      const data = await response.json();
      return data.trends || data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch price trends');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  // Get price forecast
  const getForecast = useCallback(async (
    productId: number,
    days: number = 7
  ): Promise<ProductForecast | null> => {
    try {
      setLoading(true);
      setError(null);
      const params = new URLSearchParams({
        product_id: productId.toString(),
        days: days.toString(),
      });
      const response = await fetch(`${API_BASE_URL}/api/analytics/forecast?${params}`);
      if (!response.ok) throw new Error('Failed to fetch forecast');
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch forecast');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  // Get sentiment analysis
  const getSentiment = useCallback(async (
    productId: number
  ): Promise<SentimentAnalysis | null> => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_BASE_URL}/api/analytics/sentiment/${productId}`);
      if (!response.ok) throw new Error('Failed to fetch sentiment');
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch sentiment');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  // Compare retailers
  const compareRetailers = useCallback(async (productIds: number[]) => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_BASE_URL}/api/analytics/compare-retailers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_ids: productIds }),
      });
      if (!response.ok) throw new Error('Failed to compare retailers');
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to compare retailers');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  // Get best buy timing
  const getBestBuyTime = useCallback(async (productId: number) => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_BASE_URL}/api/analytics/best-buy-time/${productId}`);
      if (!response.ok) throw new Error('Failed to get best buy time');
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get best buy time');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    loading,
    error,
    getOverview,
    getPriceTrends,
    getForecast,
    getSentiment,
    compareRetailers,
    getBestBuyTime,
  };
};
