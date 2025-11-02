"""
OpenAPI Schema Generator
Auto-generates TypeScript types and API client from FastAPI routes
"""

from typing import Dict, Any
import json
from pathlib import Path
from fastapi.openapi.utils import get_openapi
from main import app


def generate_openapi_schema() -> Dict[str, Any]:
    """Generate OpenAPI schema from FastAPI app"""
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    return schema


def save_openapi_schema(output_path: str = "frontend/src/api/openapi.json"):
    """Save OpenAPI schema to file"""
    schema = generate_openapi_schema()
    
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output, 'w') as f:
        json.dump(schema, f, indent=2)
    
    print(f"✅ OpenAPI schema saved to {output_path}")


def generate_typescript_types(output_path: str = "frontend/src/api/types.ts"):
    """Generate TypeScript types from OpenAPI schema"""
    schema = generate_openapi_schema()
    
    typescript_code = """// Auto-generated TypeScript types from OpenAPI schema
// DO NOT EDIT MANUALLY

"""
    
    # Generate types from components/schemas
    if "components" in schema and "schemas" in schema["components"]:
        for name, definition in schema["components"]["schemas"].items():
            typescript_code += generate_type_from_schema(name, definition)
            typescript_code += "\n\n"
    
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output, 'w') as f:
        f.write(typescript_code)
    
    print(f"✅ TypeScript types saved to {output_path}")


def generate_type_from_schema(name: str, schema: Dict[str, Any]) -> str:
    """Convert OpenAPI schema to TypeScript interface"""
    if schema.get("type") == "object":
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        ts_interface = f"export interface {name} {{\n"
        
        for prop_name, prop_schema in properties.items():
            optional = "" if prop_name in required else "?"
            ts_type = openapi_type_to_ts(prop_schema)
            ts_interface += f"  {prop_name}{optional}: {ts_type};\n"
        
        ts_interface += "}"
        return ts_interface
    
    return f"export type {name} = any; // Complex type"


def openapi_type_to_ts(schema: Dict[str, Any]) -> str:
    """Convert OpenAPI type to TypeScript type"""
    openapi_type = schema.get("type")
    
    type_map = {
        "string": "string",
        "integer": "number",
        "number": "number",
        "boolean": "boolean",
        "array": f"Array<{openapi_type_to_ts(schema.get('items', {}))}>",
        "object": "any"
    }
    
    if openapi_type in type_map:
        return type_map[openapi_type]
    
    # Handle $ref
    if "$ref" in schema:
        ref_name = schema["$ref"].split("/")[-1]
        return ref_name
    
    return "any"


def generate_api_client(output_path: str = "frontend/src/api/client.ts"):
    """Generate TypeScript API client"""
    client_code = """// Auto-generated API client
// DO NOT EDIT MANUALLY

import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import type * as Types from './types';

export class CumpairAPIClient {
  private client: AxiosInstance;

  constructor(baseURL: string = 'http://localhost:8000') {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  // Search V2 - God Engine
  async unifiedSearch(params: {
    q: string;
    limit?: number;
    use_cache?: boolean;
    use_vector?: boolean;
    enrich?: boolean;
  }) {
    return this.client.get('/api/v2/search', { params });
  }

  async streamingSearch(params: { q: string; limit?: number }) {
    return this.client.get('/api/v2/search/stream', { params });
  }

  async imageSearch(file: File, params: { limit?: number; enrich?: boolean }) {
    const formData = new FormData();
    formData.append('file', file);
    
    return this.client.post('/api/v2/search/image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      params,
    });
  }

  async voiceSearch(audio: File, params: { limit?: number }) {
    const formData = new FormData();
    formData.append('audio', file);
    
    return this.client.post('/api/v2/search/voice', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      params,
    });
  }

  async getCompleteProductContext(productId: number) {
    return this.client.get(`/api/v2/product/${productId}/complete`);
  }

  // Price Comparison
  async smartSearch(params: {
    query: string;
    sites?: string[];
    max_results?: number;
  }) {
    return this.client.post('/api/v1/comparison/smart-search', null, { params });
  }

  async searchByImage(file: File, sites: string[] = ['amazon', 'walmart', 'ebay']) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('sites', JSON.stringify(sites));
    
    return this.client.post('/api/v1/comparison/search-by-image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  }

  async searchByBarcode(barcode: string, sites: string[] = ['amazon', 'walmart']) {
    return this.client.post('/api/v1/comparison/search-by-barcode', null, {
      params: { barcode, sites: sites.join(',') },
    });
  }

  // Price Alerts
  async createPriceAlert(data: {
    product_id: number;
    target_price: number;
    alert_type: 'email' | 'push' | 'sms';
  }) {
    return this.client.post('/api/alerts', data);
  }

  async getPriceAlerts(userId: number) {
    return this.client.get(`/api/alerts/user/${userId}`);
  }

  // Analytics
  async getPriceHistory(productId: number, days: number = 30) {
    return this.client.get(`/api/analytics/price-history/${productId}`, {
      params: { days },
    });
  }

  async getPriceForecast(productId: number, days: number = 7) {
    return this.client.get(`/api/analytics/price-forecast/${productId}`, {
      params: { days },
    });
  }

  // Health & Metrics
  async getHealth() {
    return this.client.get('/api/v1/health');
  }

  async getServiceHealth() {
    return this.client.get('/health/services');
  }

  async getMetrics() {
    return this.client.get('/metrics');
  }
}

// Default client instance
export const api = new CumpairAPIClient();
"""
    
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output, 'w') as f:
        f.write(client_code)
    
    print(f"✅ API client saved to {output_path}")


def generate_react_hooks(output_path: str = "frontend/src/api/hooks.ts"):
    """Generate React Query hooks"""
    hooks_code = """// Auto-generated React Query hooks
// DO NOT EDIT MANUALLY

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from './client';

// Search Hooks
export function useUnifiedSearch(params: Parameters<typeof api.unifiedSearch>[0]) {
  return useQuery({
    queryKey: ['search', 'unified', params],
    queryFn: () => api.unifiedSearch(params),
    enabled: !!params.q,
  });
}

export function useImageSearch() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: { file: File; limit?: number; enrich?: boolean }) =>
      api.imageSearch(data.file, { limit: data.limit, enrich: data.enrich }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['search'] });
    },
  });
}

export function useVoiceSearch() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: { audio: File; limit?: number }) =>
      api.voiceSearch(data.audio, { limit: data.limit }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['search'] });
    },
  });
}

// Product Hooks
export function useProductContext(productId: number) {
  return useQuery({
    queryKey: ['product', productId, 'context'],
    queryFn: () => api.getCompleteProductContext(productId),
    enabled: !!productId,
  });
}

export function usePriceHistory(productId: number, days: number = 30) {
  return useQuery({
    queryKey: ['product', productId, 'history', days],
    queryFn: () => api.getPriceHistory(productId, days),
    enabled: !!productId,
  });
}

export function usePriceForecast(productId: number, days: number = 7) {
  return useQuery({
    queryKey: ['product', productId, 'forecast', days],
    queryFn: () => api.getPriceForecast(productId, days),
    enabled: !!productId,
  });
}

// Alert Hooks
export function useCreatePriceAlert() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: api.createPriceAlert,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
    },
  });
}

export function usePriceAlerts(userId: number) {
  return useQuery({
    queryKey: ['alerts', userId],
    queryFn: () => api.getPriceAlerts(userId),
    enabled: !!userId,
  });
}

// Health Hooks
export function useServiceHealth() {
  return useQuery({
    queryKey: ['health', 'services'],
    queryFn: () => api.getServiceHealth(),
    refetchInterval: 30000, // Refetch every 30s
  });
}
"""
    
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output, 'w') as f:
        f.write(hooks_code)
    
    print(f"✅ React hooks saved to {output_path}")


if __name__ == "__main__":
    print("🔧 Generating frontend integration layer...")
    save_openapi_schema()
    generate_typescript_types()
    generate_api_client()
    generate_react_hooks()
    print("✅ Frontend integration complete!")
