// React Query hooks for Search V2 API
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { searchV2API } from '@/services/api';
import type {
  UnifiedSearchResponse,
  ImageSearchResponse,
  VoiceSearchResponse,
  CompleteProductContext,
  SearchOptions,
} from '@/services/api/search';

/**
 * Unified search hook
 */
export const useUnifiedSearchV2 = (query: string, options?: SearchOptions) => {
  return useQuery<UnifiedSearchResponse>({
    queryKey: ['search', 'unified', query, options],
    queryFn: () => searchV2API.unifiedSearch(query, options),
    enabled: !!query && query.length > 0,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

/**
 * Image search mutation
 */
export const useImageSearchV2 = () => {
  const queryClient = useQueryClient();

  return useMutation<ImageSearchResponse, Error, { file: File; sites?: string[]; top_k?: number }>({
    mutationFn: ({ file, sites, top_k }) => searchV2API.imageSearch(file, sites, top_k),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['search'] });
    },
  });
};

/**
 * Voice search mutation
 */
export const useVoiceSearchV2 = () => {
  const queryClient = useQueryClient();

  return useMutation<VoiceSearchResponse, Error, Blob>({
    mutationFn: (audioBlob) => searchV2API.voiceSearch(audioBlob),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['search'] });
    },
  });
};

/**
 * Get complete product context
 */
export const useCompleteProductContextV2 = (productId: string | number) => {
  return useQuery<CompleteProductContext>({
    queryKey: ['product', 'complete', productId],
    queryFn: () => searchV2API.getCompleteProductContext(productId),
    enabled: !!productId,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
};
