import { useState, useEffect } from 'react';
import { config, isDemoMode } from '@/config/env';

export interface SeedProduct {
  id: string;
  title: string;
  price: number;
  oldPrice?: number | null;
  currency: string;
  store: string;
  store_key: string;
  image_url: string;
  rating: number;
  rating_count: number;
  categories: string[];
  location: string;
  availability: string;
  description: string;
  url: string;
}

interface SeedProductsResponse {
  products: SeedProduct[];
  total: number;
  page: number;
  page_size: number;
  demo_mode: boolean;
  last_updated: string;
  stores: string[];
  locations: string[];
}

interface UseSeedProductsOptions {
  page?: number;
  page_size?: number;
  store?: string;
  category?: string;
  location?: string;
  min_price?: number;
  max_price?: number;
  currency?: string;
  sort_by?: 'price' | 'rating' | 'popularity';
  sort_order?: 'asc' | 'desc';
  enabled?: boolean;
}

export const useSeedProducts = (options: UseSeedProductsOptions = {}) => {
  const [data, setData] = useState<SeedProductsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const {
    page = 1,
    page_size = 20,
    store,
    category,
    location,
    min_price,
    max_price,
    currency,
    sort_by = 'rating',
    sort_order = 'desc',
    enabled = true,
  } = options;

  useEffect(() => {
    if (!enabled) return;

    const fetchProducts = async () => {
      setLoading(true);
      setError(null);

      try {
        // Build query params
        const params = new URLSearchParams({
          page: page.toString(),
          page_size: page_size.toString(),
          sort_by,
          sort_order,
        });

        if (store) params.append('store', store);
        if (category) params.append('category', category);
        if (location) params.append('location', location);
        if (min_price !== undefined) params.append('min_price', min_price.toString());
        if (max_price !== undefined) params.append('max_price', max_price.toString());
        if (currency) params.append('currency', currency);

        const response = await fetch(`${config.apiUrl}/api/seed/products?${params}`);
        
        if (!response.ok) {
          throw new Error(`Failed to fetch seed products: ${response.statusText}`);
        }

        const result = await response.json();
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Unknown error'));
      } finally {
        setLoading(false);
      }
    };

    fetchProducts();
  }, [page, page_size, store, category, location, min_price, max_price, currency, sort_by, sort_order, enabled]);

  return { data, loading, error, isOffline: isDemoMode() || data?.demo_mode };
};

interface SeedStatsResponse {
  total_products: number;
  stores: Record<string, number>;
  categories: Record<string, number>;
  currencies: Record<string, number>;
  locations: Record<string, number>;
  price_ranges: Record<string, { min: number; max: number; avg: number }>;
  last_updated: string;
  demo_mode: boolean;
}

export const useSeedStats = () => {
  const [data, setData] = useState<SeedStatsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(`${config.apiUrl}/api/seed/stats`);
        
        if (!response.ok) {
          throw new Error(`Failed to fetch seed stats: ${response.statusText}`);
        }

        const result = await response.json();
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Unknown error'));
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  return { data, loading, error };
};
