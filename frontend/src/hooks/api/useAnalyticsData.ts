// React Query hooks for Analytics API
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { analyticsAPI } from '@/services/api';
import type {
  AnalyticsOverview,
  PriceTrendsResponse,
  PriceForecastResponse,
  SentimentAnalysis,
  RetailerPerformance,
  PriceAnomaly,
  TrendingProduct,
} from '@/services/api/analytics';

/**
 * Get analytics dashboard overview
 */
export const useAnalyticsOverview = () => {
  return useQuery<AnalyticsOverview>({
    queryKey: ['analytics', 'overview'],
    queryFn: () => analyticsAPI.getAnalyticsOverview(),
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchInterval: 5 * 60 * 1000, // Auto-refresh every 5 minutes
  });
};

/**
 * Get price trends for a product
 */
export const useProductTrends = (productId: number | string, days?: number) => {
  return useQuery<PriceTrendsResponse>({
    queryKey: ['analytics', 'trends', productId, days],
    queryFn: () => analyticsAPI.getProductTrends(productId, days),
    enabled: !!productId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

/**
 * Get price forecast for a product
 */
export const useProductForecast = (productId: number | string, days_ahead?: number) => {
  return useQuery<PriceForecastResponse>({
    queryKey: ['analytics', 'forecast', productId, days_ahead],
    queryFn: () => analyticsAPI.getProductForecast(productId, days_ahead),
    enabled: !!productId,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};

/**
 * Generate new forecast (mutation)
 */
export const useGenerateForecast = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ productId, days_ahead }: { productId: number | string; days_ahead?: number }) =>
      analyticsAPI.generateForecast(productId, days_ahead),
    onSuccess: (_, variables) => {
      // Invalidate forecast cache
      queryClient.invalidateQueries({
        queryKey: ['analytics', 'forecast', variables.productId],
      });
    },
  });
};

/**
 * Get sentiment analysis for a product
 */
export const useProductSentiment = (productId: number | string) => {
  return useQuery<SentimentAnalysis>({
    queryKey: ['analytics', 'sentiment', productId],
    queryFn: () => analyticsAPI.getProductSentiment(productId),
    enabled: !!productId,
    staleTime: 15 * 60 * 1000, // 15 minutes
  });
};

/**
 * Trigger sentiment analysis (mutation)
 */
export const useAnalyzeSentiment = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (productId: number | string) => analyticsAPI.analyzeSentiment(productId),
    onSuccess: (_, productId) => {
      queryClient.invalidateQueries({
        queryKey: ['analytics', 'sentiment', productId],
      });
    },
  });
};

/**
 * Get retailer performance comparison
 */
export const useRetailerComparison = (category?: string) => {
  return useQuery<RetailerPerformance[]>({
    queryKey: ['analytics', 'retailers', 'comparison', category],
    queryFn: () => analyticsAPI.getRetailerComparison(category),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};

/**
 * Get price anomalies
 */
export const usePriceAnomalies = (min_confidence?: number, limit?: number) => {
  return useQuery<PriceAnomaly[]>({
    queryKey: ['analytics', 'anomalies', min_confidence, limit],
    queryFn: () => analyticsAPI.getPriceAnomalies(min_confidence, limit),
    staleTime: 3 * 60 * 1000, // 3 minutes
    refetchInterval: 5 * 60 * 1000, // Auto-refresh every 5 minutes
  });
};

/**
 * Get trending products
 */
export const useTrendingProducts = (category?: string, limit?: number) => {
  return useQuery<TrendingProduct[]>({
    queryKey: ['analytics', 'trending', category, limit],
    queryFn: () => analyticsAPI.getTrendingProducts(category, limit),
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchInterval: 5 * 60 * 1000, // Auto-refresh every 5 minutes
  });
};

/**
 * Get category insights
 */
export const useCategoryInsights = () => {
  return useQuery({
    queryKey: ['analytics', 'categories', 'insights'],
    queryFn: () => analyticsAPI.getCategoryInsights(),
    staleTime: 15 * 60 * 1000, // 15 minutes
  });
};

/**
 * Get market trends
 */
export const useMarketTrends = (days?: number) => {
  return useQuery({
    queryKey: ['analytics', 'market', 'trends', days],
    queryFn: () => analyticsAPI.getMarketTrends(days),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};
