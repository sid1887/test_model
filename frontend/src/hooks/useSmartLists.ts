/**
 * Custom hook for Smart Lists operations
 */

import { useState, useEffect, useCallback } from 'react';
import { SmartList, SmartListItem, ListTemplate } from '../types/alerts';
import { API_BASE_URL } from '../config/env';

export const useSmartLists = () => {
  const [lists, setLists] = useState<SmartList[]>([]);
  const [templates, setTemplates] = useState<ListTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch all lists
  const fetchLists = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/lists?user_id=1`);
      if (!response.ok) throw new Error('Failed to fetch lists');
      const data = await response.json();
      setLists(data.items || data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch lists');
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch templates
  const fetchTemplates = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/lists/templates`);
      if (!response.ok) throw new Error('Failed to fetch templates');
      const data = await response.json();
      setTemplates(data.items || data);
    } catch (err) {
      console.error('Failed to fetch templates:', err);
    }
  }, []);

  useEffect(() => {
    fetchLists();
    fetchTemplates();
  }, [fetchLists, fetchTemplates]);

  // Create list
  const createList = async (data: { name: string; description?: string; is_public?: boolean }) => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/lists`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...data, user_id: 1 }),
      });
      if (!response.ok) throw new Error('Failed to create list');
      const newList = await response.json();
      await fetchLists();
      return newList;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create list');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Update list
  const updateList = async (id: number, data: Partial<SmartList>) => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/lists/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error('Failed to update list');
      const updated = await response.json();
      await fetchLists();
      return updated;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update list');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Delete list
  const deleteList = async (id: number) => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/lists/${id}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error('Failed to delete list');
      await fetchLists();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete list');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Add item to list
  const addItem = async (listId: number, data: { product_id: number; quantity?: number; desired_price?: number; notes?: string }) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/lists/${listId}/items`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error('Failed to add item');
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add item');
      throw err;
    }
  };

  // Remove item from list
  const removeItem = async (listId: number, itemId: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/lists/${listId}/items/${itemId}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error('Failed to remove item');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove item');
      throw err;
    }
  };

  // Update item
  const updateItem = async (listId: number, itemId: number, data: Partial<SmartListItem>) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/lists/${listId}/items/${itemId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error('Failed to update item');
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update item');
      throw err;
    }
  };

  // Reorder items
  const reorderItems = async (listId: number, itemOrders: { item_id: number; position: number }[]) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/lists/${listId}/reorder`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item_orders: itemOrders }),
      });
      if (!response.ok) throw new Error('Failed to reorder items');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reorder items');
      throw err;
    }
  };

  // Start comparison job
  const startComparison = async (listId: number, retailerIds?: number[]) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/lists/${listId}/compare`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ retailer_ids: retailerIds }),
      });
      if (!response.ok) throw new Error('Failed to start comparison');
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start comparison');
      throw err;
    }
  };

  // Get comparison result
  const getComparisonResult = async (jobId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/lists/compare/${jobId}`);
      if (!response.ok) throw new Error('Failed to get comparison result');
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get comparison result');
      throw err;
    }
  };

  // Apply template
  const applyTemplate = async (listId: number, templateId: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/lists/${listId}/apply-template/${templateId}`, {
        method: 'POST',
      });
      if (!response.ok) throw new Error('Failed to apply template');
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to apply template');
      throw err;
    }
  };

  // Generate share token
  const generateShareToken = async (listId: number, expiresInDays: number = 7) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/lists/${listId}/share`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ expires_in_days: expiresInDays }),
      });
      if (!response.ok) throw new Error('Failed to generate share token');
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate share token');
      throw err;
    }
  };

  return {
    lists,
    templates,
    loading,
    error,
    fetchLists,
    createList,
    updateList,
    deleteList,
    addItem,
    removeItem,
    updateItem,
    reorderItems,
    startComparison,
    getComparisonResult,
    applyTemplate,
    generateShareToken,
  };
};
