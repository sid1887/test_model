// React Query hooks for Smart Lists API with SSE streaming
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState, useEffect } from 'react';
import { smartListsAPI } from '@/services/api';
import type {
  SmartList,
  CreateListRequest,
  UpdateListRequest,
  AddItemRequest,
  UpdateItemRequest,
  ComparisonJob,
  ComparisonJobUpdate,
  ListTemplate,
} from '@/services/api/smartLists';
import { toast } from 'sonner';

/**
 * List all smart lists
 */
export const useSmartLists = (category?: string) => {
  return useQuery<SmartList[]>({
    queryKey: ['smartLists', 'list', category],
    queryFn: () => smartListsAPI.listSmartLists(category),
    staleTime: 1 * 60 * 1000, // 1 minute
  });
};

/**
 * Get single smart list
 */
export const useSmartList = (listId: number) => {
  return useQuery<SmartList>({
    queryKey: ['smartLists', listId],
    queryFn: () => smartListsAPI.getSmartList(listId),
    enabled: !!listId,
  });
};

/**
 * Create smart list
 */
export const useCreateSmartList = () => {
  const queryClient = useQueryClient();

  return useMutation<SmartList, Error, CreateListRequest>({
    mutationFn: (request) => smartListsAPI.createSmartList(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['smartLists'] });
      toast.success('List created successfully!');
    },
  });
};

/**
 * Update smart list
 */
export const useUpdateSmartList = () => {
  const queryClient = useQueryClient();

  return useMutation<SmartList, Error, { listId: number; request: UpdateListRequest }>({
    mutationFn: ({ listId, request }) => smartListsAPI.updateSmartList(listId, request),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['smartLists'] });
      queryClient.invalidateQueries({ queryKey: ['smartLists', variables.listId] });
      toast.success('List updated!');
    },
  });
};

/**
 * Delete smart list
 */
export const useDeleteSmartList = () => {
  const queryClient = useQueryClient();

  return useMutation<{ message: string }, Error, number>({
    mutationFn: (listId) => smartListsAPI.deleteSmartList(listId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['smartLists'] });
      toast.success('List deleted!');
    },
  });
};

/**
 * Add item to list
 */
export const useAddListItem = () => {
  const queryClient = useQueryClient();

  return useMutation<unknown, Error, { listId: number; request: AddItemRequest }>({
    mutationFn: ({ listId, request }) => smartListsAPI.addListItem(listId, request),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['smartLists', variables.listId] });
      toast.success('Item added!');
    },
  });
};

/**
 * Update list item
 */
export const useUpdateListItem = () => {
  const queryClient = useQueryClient();

  return useMutation<
    unknown,
    Error,
    { listId: number; itemId: number; request: UpdateItemRequest }
  >({
    mutationFn: ({ listId, itemId, request }) =>
      smartListsAPI.updateListItem(listId, itemId, request),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['smartLists', variables.listId] });
    },
  });
};

/**
 * Delete list item
 */
export const useDeleteListItem = () => {
  const queryClient = useQueryClient();

  return useMutation<{ message: string }, Error, { listId: number; itemId: number }>({
    mutationFn: ({ listId, itemId }) => smartListsAPI.deleteListItem(listId, itemId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['smartLists', variables.listId] });
      toast.success('Item removed!');
    },
  });
};

/**
 * Start comparison job
 */
export const useStartComparisonJob = () => {
  return useMutation<
    { job_id: string; message: string },
    Error,
    { listId: number; retailers?: string[] }
  >({
    mutationFn: ({ listId, retailers }) => smartListsAPI.startComparisonJob(listId, retailers),
    onSuccess: () => {
      toast.success('Comparison started!');
    },
  });
};

/**
 * Get comparison job status
 */
export const useComparisonJobStatus = (jobId: string) => {
  return useQuery<ComparisonJob>({
    queryKey: ['smartLists', 'comparison', jobId],
    queryFn: () => smartListsAPI.getComparisonJobStatus(jobId),
    enabled: !!jobId,
    refetchInterval: (query) => {
      // Stop polling when job is complete or failed
      if (query.state.data?.status === 'completed' || query.state.data?.status === 'failed') {
        return false;
      }
      return 3000; // Poll every 3 seconds
    },
  });
};

/**
 * SSE streaming hook for comparison job updates
 */
export const useComparisonJobStream = (jobId: string) => {
  const [updates, setUpdates] = useState<ComparisonJobUpdate[]>([]);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<'idle' | 'running' | 'completed' | 'error'>('idle');
  const [finalJob, setFinalJob] = useState<ComparisonJob | null>(null);
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!jobId) return;

    setStatus('running');
    const eventSource = smartListsAPI.streamComparisonJob(
      jobId,
      (update) => {
        setUpdates((prev) => [...prev, update]);

        if (update.type === 'progress' && update.progress !== undefined) {
          setProgress(update.progress);
        } else if (update.type === 'item_complete' && update.item) {
          toast.success(`Found best deal for ${update.item.product_name}`);
        } else if (update.type === 'error' && update.error) {
          setStatus('error');
          toast.error(`Comparison error: ${update.error}`);
        }
      },
      (error) => {
        console.error('SSE error:', error);
        setStatus('error');
      },
      (job) => {
        setStatus('completed');
        setFinalJob(job);
        setProgress(100);
        queryClient.invalidateQueries({ queryKey: ['smartLists', 'comparison'] });
        toast.success('Comparison complete!');
      }
    );

    return () => {
      eventSource.close();
    };
  }, [jobId, queryClient]);

  return {
    updates,
    progress,
    status,
    finalJob,
    reset: () => {
      setUpdates([]);
      setProgress(0);
      setStatus('idle');
      setFinalJob(null);
    },
  };
};

/**
 * Get list templates
 */
export const useListTemplates = (category?: string) => {
  return useQuery<ListTemplate[]>({
    queryKey: ['smartLists', 'templates', category],
    queryFn: () => smartListsAPI.getListTemplates(category),
    staleTime: 30 * 60 * 1000, // 30 minutes
  });
};

/**
 * Apply template
 */
export const useApplyTemplate = () => {
  const queryClient = useQueryClient();

  return useMutation<SmartList, Error, { templateId: number; list_name?: string }>({
    mutationFn: ({ templateId, list_name }) => smartListsAPI.applyTemplate(templateId, list_name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['smartLists'] });
      toast.success('Template applied!');
    },
  });
};

/**
 * Duplicate list
 */
export const useDuplicateList = () => {
  const queryClient = useQueryClient();

  return useMutation<SmartList, Error, { listId: number; new_name?: string }>({
    mutationFn: ({ listId, new_name }) => smartListsAPI.duplicateList(listId, new_name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['smartLists'] });
      toast.success('List duplicated!');
    },
  });
};

/**
 * Export list
 */
export const useExportList = () => {
  return useMutation<Blob, Error, { listId: number; format: 'csv' | 'json' }>({
    mutationFn: ({ listId, format }) => smartListsAPI.exportList(listId, format),
    onSuccess: (blob, variables) => {
      // Download the file
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `list_${variables.listId}.${variables.format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success('List exported!');
    },
  });
};
