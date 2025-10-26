/**
 * Environment Configuration
 * Centralized access to environment variables with type safety and defaults
 */

export const config = {
  // Service Configuration
  serviceName: import.meta.env.VITE_SERVICE_NAME || 'cumpair',
  demoMode: import.meta.env.VITE_DEMO_MODE === 'true',
  
  // API Configuration
  apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  apiTimeout: parseInt(import.meta.env.VITE_API_TIMEOUT || '30000', 10),
  
  // Feature Flags
  features: {
    realTimeSearch: import.meta.env.VITE_ENABLE_REAL_TIME_SEARCH === 'true',
    priceAlerts: import.meta.env.VITE_ENABLE_PRICE_ALERTS === 'true',
    analytics: import.meta.env.VITE_ENABLE_ANALYTICS === 'true',
    geolocation: import.meta.env.VITE_ENABLE_GEOLOCATION === 'true',
    demoOldComponents: import.meta.env.VITE_DEMO_OLD_COMPONENTS === 'true',
  },
  
  // Search Configuration
  search: {
    defaultSites: (import.meta.env.VITE_DEFAULT_SEARCH_SITES || 'amazon,walmart,ebay').split(','),
    minSimilarityScore: parseFloat(import.meta.env.VITE_MIN_SIMILARITY_SCORE || '0.7'),
    maxResults: parseInt(import.meta.env.VITE_MAX_SEARCH_RESULTS || '20', 10),
  },
  
  // Upload Configuration
  upload: {
    maxFileSize: parseInt(import.meta.env.VITE_MAX_FILE_SIZE || '10485760', 10),
    allowedTypes: (import.meta.env.VITE_ALLOWED_FILE_TYPES || 'image/jpeg,image/png,image/webp,image/gif').split(','),
  },
  
  // Development Settings
  debug: import.meta.env.VITE_DEBUG_MODE === 'true',
  logLevel: import.meta.env.VITE_LOG_LEVEL || 'info',
} as const;

// Helper function to check if running in demo mode
export const isDemoMode = () => config.demoMode;

// Helper function to get service name
export const getServiceName = () => config.serviceName;

// Helper function to check feature flags
export const isFeatureEnabled = (feature: keyof typeof config.features) => {
  return config.features[feature];
};

// Export convenience constants
export const API_BASE_URL = config.apiUrl;
export const WS_BASE_URL = config.apiUrl.replace('http', 'ws');

// Log configuration on load (only in debug mode)
if (config.debug) {
  console.log('[Config] Environment configuration loaded:', {
    serviceName: config.serviceName,
    demoMode: config.demoMode,
    apiUrl: config.apiUrl,
    features: config.features,
  });
}
