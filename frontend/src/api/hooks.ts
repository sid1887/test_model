// React Query Hooks for Cumpair API

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from './client';
import type {
  SearchResult,
  CompleteProductContext,
  PriceComparison,
  ServiceHealth,
  Retailer,
  PredictionRequest,
  PredictionResult,
} from './types';

// Search Hooks
export function useUnifiedSearch(params: {
  q: string;
  limit?: number;
  use_cache?: boolean;
  use_vector?: boolean;
  enrich?: boolean;
}, enabled = true) {
  return useQuery<SearchResult>({
    queryKey: ['search', 'unified', params],
    queryFn: (): Promise<SearchResult> => api.unifiedSearch(params),
    enabled: enabled && !!params.q,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useLegacySearch(query: string, enabled = true) {
  return useQuery({
    queryKey: ['search', 'legacy', query],
    queryFn: () => api.search(query),
    enabled: enabled && !!query,
  });
}

// Image Search Hook
export function useImageSearch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ file, params }: { file: File; params: { limit?: number; enrich?: boolean } }) =>
      api.imageSearch(file, params),
    onSuccess: () => {
      // Invalidate search queries
      queryClient.invalidateQueries({ queryKey: ['search'] });
    },
  });
}

// Product Hooks
export function useCompleteProductContext(productId: string, enabled = true) {
  return useQuery<CompleteProductContext>({
    queryKey: ['product', 'complete', productId],
    queryFn: (): Promise<CompleteProductContext> => api.getCompleteProductContext(productId),
    enabled: enabled && !!productId,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

export function useProductAnalysis(productId: string, enabled = true) {
  return useQuery({
    queryKey: ['product', 'analysis', productId],
    queryFn: () => api.analyzeProduct(productId),
    enabled: enabled && !!productId,
  });
}

// Price Comparison Hooks
export function usePriceComparison(productId: string, days?: number, enabled = true) {
  return useQuery<PriceComparison>({
    queryKey: ['price-comparison', productId, days],
    queryFn: (): Promise<PriceComparison> => api.getPriceComparison({ product_id: productId, days }),
    enabled: enabled && !!productId,
    staleTime: 1 * 60 * 1000, // 1 minute
  });
}

// Price Alert Hooks
export function useCreatePriceAlert() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { product_id: string; target_price: number; email: string }) =>
      api.createPriceAlert(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['price-alerts'] });
    },
  });
}

// Prediction Hooks
export function usePricePrediction() {
  return useMutation<PredictionResult, Error, PredictionRequest>({
    mutationFn: (data: PredictionRequest): Promise<PredictionResult> => api.runPrediction(data),
  });
}

// Service Health Hook
export function useServiceHealth(refetchInterval?: number) {
  return useQuery<ServiceHealth>({
    queryKey: ['health', 'services'],
    queryFn: (): Promise<ServiceHealth> => api.getServiceHealth(),
    refetchInterval: refetchInterval || 30000, // Default 30 seconds
    staleTime: 10000, // 10 seconds
  });
}

// Retailers Hook
export function useRetailers() {
  return useQuery<Retailer[]>({
    queryKey: ['retailers'],
    queryFn: (): Promise<Retailer[]> => api.getRetailers(),
    staleTime: 60 * 60 * 1000, // 1 hour
  });
}

// Metrics Hook
export function useMetrics() {
  return useQuery<string>({
    queryKey: ['metrics'],
    queryFn: () => api.getMetrics(),
    refetchInterval: 60000, // 1 minute
  });
}
