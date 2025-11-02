// React Query hooks for Comparison API
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { comparisonAPI } from '@/services/api';
import type {
  PriceComparisonResponse,
  RealTimeSearchRequest,
  RealTimeSearchResponse,
  SmartSearchRequest,
  RetailerInfo,
} from '@/services/api/comparison';
import { toast } from 'sonner';

/**
 * Real-time search across retailers
 */
export const useRealTimeSearch = () => {
  return useMutation<RealTimeSearchResponse, Error, RealTimeSearchRequest>({
    mutationFn: (request) => comparisonAPI.realTimeSearch(request),
    onError: (error) => {
      toast.error(`Search failed: ${error.message}`);
    },
  });
};

/**
 * Smart search using CLIP + scraper
 */
export const useSmartSearch = () => {
  return useMutation<RealTimeSearchResponse, Error, SmartSearchRequest>({
    mutationFn: (request) => comparisonAPI.smartSearch(request),
    onError: (error) => {
      toast.error(`Smart search failed: ${error.message}`);
    },
  });
};

/**
 * Search by image
 */
export const useSearchByImage = () => {
  return useMutation<RealTimeSearchResponse, Error, { file: File; retailers?: string[] }>({
    mutationFn: ({ file, retailers }) => comparisonAPI.searchByImage(file, retailers),
    onSuccess: () => {
      toast.success('Image search complete!');
    },
  });
};

/**
 * Search by barcode
 */
export const useSearchByBarcode = () => {
  return useMutation<RealTimeSearchResponse, Error, { barcode: string; retailers?: string[] }>({
    mutationFn: ({ barcode, retailers }) => comparisonAPI.searchByBarcode(barcode, retailers),
  });
};

/**
 * Get price comparison for product
 */
export const usePriceComparison = (productId: number | string) => {
  return useQuery<PriceComparisonResponse>({
    queryKey: ['comparison', 'prices', productId],
    queryFn: () => comparisonAPI.getPriceComparison(productId),
    enabled: !!productId,
    staleTime: 1 * 60 * 1000, // 1 minute
  });
};

/**
 * Get available retailers
 */
export const useRetailers = (category?: string, active_only?: boolean) => {
  return useQuery<RetailerInfo[]>({
    queryKey: ['comparison', 'retailers', category, active_only],
    queryFn: () => comparisonAPI.getRetailers({ category, active_only }),
    staleTime: 30 * 60 * 1000, // 30 minutes
  });
};

/**
 * Get price history
 */
export const usePriceHistory = (productId: number | string, days?: number) => {
  return useQuery<unknown>({
    queryKey: ['comparison', 'history', productId, days],
    queryFn: () => comparisonAPI.getPriceHistory(productId, days),
    enabled: !!productId,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};

/**
 * Get comparison statistics
 */
export const useComparisonStats = () => {
  return useQuery<unknown>({
    queryKey: ['comparison', 'stats'],
    queryFn: () => comparisonAPI.getComparisonStats(),
    staleTime: 10 * 60 * 1000,
  });
};

/**
 * Get price sources
 */
export const usePriceSources = () => {
  return useQuery<unknown>({
    queryKey: ['comparison', 'sources'],
    queryFn: () => comparisonAPI.getPriceSources(),
    staleTime: 30 * 60 * 1000, // 30 minutes
  });
};

/**
 * Refresh price comparison
 */
export const useRefreshPriceComparison = () => {
  const queryClient = useQueryClient();

  return useMutation<{ message: string; job_id: string }, Error, number | string>({
    mutationFn: (productId) => comparisonAPI.refreshPriceComparison(productId),
    onSuccess: (_, productId) => {
      queryClient.invalidateQueries({ queryKey: ['comparison', 'prices', productId] });
      queryClient.invalidateQueries({ queryKey: ['comparison', 'history', productId] });
      toast.success('Price comparison refreshed!');
    },
  });
};

/**
 * Get retailer configuration
 */
export const useRetailerConfig = (retailerKey: string) => {
  return useQuery<RetailerInfo>({
    queryKey: ['comparison', 'retailer', retailerKey],
    queryFn: () => comparisonAPI.getRetailerConfig(retailerKey),
    enabled: !!retailerKey,
    staleTime: 30 * 60 * 1000, // 30 minutes
  });
};

/**
 * Update retailer status
 */
export const useUpdateRetailerStatus = () => {
  const queryClient = useQueryClient();

  return useMutation<{ message: string }, Error, { retailerKey: string; is_active: boolean }>({
    mutationFn: ({ retailerKey, is_active }) =>
      comparisonAPI.updateRetailerStatus(retailerKey, is_active),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['comparison', 'retailer', variables.retailerKey] });
      queryClient.invalidateQueries({ queryKey: ['comparison', 'retailers'] });
      toast.success('Retailer status updated!');
    },
  });
};

/**
 * Enhanced search
 */
export const useEnhancedSearch = () => {
  return useMutation<RealTimeSearchResponse, Error, { query: string; filters?: Record<string, unknown> }>({
    mutationFn: ({ query, filters }) => comparisonAPI.enhancedSearch(query, filters),
    onError: (error) => {
      toast.error(`Enhanced search failed: ${error.message}`);
    },
  });
};

/**
 * Delete price comparison
 */
export const useDeletePriceComparison = () => {
  const queryClient = useQueryClient();

  return useMutation<{ message: string }, Error, number | string>({
    mutationFn: (productId) => comparisonAPI.deletePriceComparison(productId),
    onSuccess: (_, productId) => {
      queryClient.invalidateQueries({ queryKey: ['comparison', 'prices', productId] });
      toast.success('Price comparison deleted!');
    },
  });
};
