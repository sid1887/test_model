// React Query Hooks for Cumpair API - Integrated Gateway

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from './client';
import type {
  ServiceHealth,
  Retailer,
  PredictionRequest,
  PredictionResult,
} from './types';

// ============================================================================
// SEARCH HOOKS
// ============================================================================

export function useSearch(q: string, enabled = true) {
  return useQuery({
    queryKey: ['search', q],
    queryFn: () => api.search(q),
    enabled: enabled && !!q,
    staleTime: 5 * 60 * 1000,
  });
}

export function useSemanticSearch(q: string, enabled = true) {
  return useQuery({
    queryKey: ['search', 'semantic', q],
    queryFn: () => api.semanticSearch(q),
    enabled: enabled && !!q,
    staleTime: 5 * 60 * 1000,
  });
}

export function useAutocomplete(q: string, enabled = true) {
  return useQuery({
    queryKey: ['search', 'autocomplete', q],
    queryFn: () => api.autocomplete(q),
    enabled: enabled && !!q,
  });
}

export function useFacetedSearch(q: string, category?: string, minPrice?: number, maxPrice?: number) {
  return useQuery({
    queryKey: ['search', 'faceted', q, category, minPrice, maxPrice],
    queryFn: () => api.facetedSearch(q, category, minPrice, maxPrice),
    staleTime: 5 * 60 * 1000,
  });
}

export function useTrendingSearch() {
  return useQuery({
    queryKey: ['search', 'trending'],
    queryFn: () => api.trendingSearch(),
    staleTime: 10 * 60 * 1000,
  });
}

// ============================================================================
// ELASTICSEARCH HOOKS
// ============================================================================

export function useElasticsearchSearch(q: string, enabled = true) {
  return useQuery({
    queryKey: ['search', 'elasticsearch', q],
    queryFn: () => api.elasticsearchSearch(q),
    enabled: enabled && !!q,
    staleTime: 5 * 60 * 1000,
  });
}

export function useFuzzySearch(q: string, enabled = true) {
  return useQuery({
    queryKey: ['search', 'fuzzy', q],
    queryFn: () => api.fuzzySearch(q),
    enabled: enabled && !!q,
  });
}

// ============================================================================
// RECOMMENDATIONS HOOKS
// ============================================================================

export function useRecommendations(userId: string, enabled = true) {
  return useQuery({
    queryKey: ['recommendations', userId],
    queryFn: () => api.getRecommendations(userId),
    enabled: enabled && !!userId,
    staleTime: 10 * 60 * 1000,
  });
}

export function useSimilarProducts(productId: string, enabled = true) {
  return useQuery({
    queryKey: ['recommendations', 'similar', productId],
    queryFn: () => api.getSimilarProducts(productId),
    enabled: enabled && !!productId,
    staleTime: 10 * 60 * 1000,
  });
}

export function useTrendingProducts() {
  return useQuery({
    queryKey: ['recommendations', 'trending'],
    queryFn: () => api.getTrendingProducts(),
    staleTime: 15 * 60 * 1000,
  });
}

export function useForecastDemand(productId: string, enabled = true) {
  return useQuery({
    queryKey: ['forecast', 'demand', productId],
    queryFn: () => api.forecastDemand(productId),
    enabled: enabled && !!productId,
    staleTime: 30 * 60 * 1000,
  });
}

// ============================================================================
// PRICE ALERT HOOKS
// ============================================================================

export function useCreatePriceAlert() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { productId: string; targetPrice: number; userId: string }) =>
      api.createPriceAlert(data.productId, data.targetPrice, data.userId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['alerts', variables.userId] });
    },
  });
}

export function useUserAlerts(userId: string, enabled = true) {
  return useQuery({
    queryKey: ['alerts', userId],
    queryFn: () => api.getUserAlerts(userId),
    enabled: enabled && !!userId,
    staleTime: 2 * 60 * 1000,
  });
}

// ============================================================================
// REAL-TIME HOOKS
// ============================================================================

export function useRealtimeStats() {
  return useQuery({
    queryKey: ['realtime', 'stats'],
    queryFn: () => api.getRealtimeStats(),
    refetchInterval: 5000,
    staleTime: 2000,
  });
}

export function useSendNotification() {
  return useMutation({
    mutationFn: (data: { userId: string; message: string }) =>
      api.sendNotification(data.userId, data.message),
  });
}

// ============================================================================
// EVENTS HOOKS
// ============================================================================

export function usePublishEvent() {
  return useMutation({
    mutationFn: (data: { eventType: string; data: Record<string, unknown>; userId?: string }) =>
      api.publishEvent(data.eventType, data.data, data.userId),
  });
}

export function useEventStream(streamKey: string, enabled = true) {
  return useQuery({
    queryKey: ['events', 'stream', streamKey],
    queryFn: () => api.getEventStream(streamKey),
    enabled: enabled && !!streamKey,
    staleTime: 1 * 60 * 1000,
  });
}

export function useUserEvents(userId: string, enabled = true) {
  return useQuery({
    queryKey: ['events', 'user', userId],
    queryFn: () => api.getUserEvents(userId),
    enabled: enabled && !!userId,
    refetchInterval: 10000,
    staleTime: 5000,
  });
}

export function useDeadLetterQueue() {
  return useQuery({
    queryKey: ['events', 'dlq'],
    queryFn: () => api.getDeadLetterQueue(),
    staleTime: 2 * 60 * 1000,
  });
}

export function useRetryEvent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (eventId: string) => api.retryEvent(eventId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['events', 'dlq'] });
    },
  });
}

// ============================================================================
// LEGACY HOOKS
// ============================================================================

export function useUnifiedSearch(params: {
  q: string;
  limit?: number;
  use_cache?: boolean;
  use_vector?: boolean;
  enrich?: boolean;
}, enabled = true) {
  return useQuery({
    queryKey: ['search', 'unified', params],
    queryFn: () => api.unifiedSearch(params),
    enabled: enabled && !!params.q,
    staleTime: 5 * 60 * 1000,
  });
}

export function usePriceComparison(productId: string, days?: number, enabled = true) {
  return useQuery({
    queryKey: ['price-comparison', productId, days],
    queryFn: () => api.getPriceComparison({ product_id: productId, days }),
    enabled: enabled && !!productId,
    staleTime: 1 * 60 * 1000,
  });
}

export function usePricePrediction() {
  return useMutation<PredictionResult, Error, PredictionRequest>({
    mutationFn: (data: PredictionRequest) => api.runPrediction(data),
  });
}

export function useServiceHealth(refetchInterval?: number) {
  return useQuery<ServiceHealth>({
    queryKey: ['health', 'services'],
    queryFn: () => api.getServiceHealth(),
    refetchInterval: refetchInterval || 30000,
    staleTime: 10000,
  });
}

export function useRetailers() {
  return useQuery<Retailer[]>({
    queryKey: ['retailers'],
    queryFn: () => api.getRetailers(),
    staleTime: 60 * 60 * 1000,
  });
}

export function useMetrics() {
  return useQuery<string>({
    queryKey: ['metrics'],
    queryFn: () => api.getMetrics(),
    refetchInterval: 60000,
  });
}
