// Barrel export for all API services
// Provides centralized access to all backend APIs

// Note: Not using export * to avoid naming conflicts (SearchResult exists in multiple modules)
// Import specific exports as needed from individual modules

// Re-export default objects for convenience
export { default as searchV2API } from './search';
export { default as comparisonAPI } from './comparison';
export { default as analyticsAPI } from './analytics';
export { default as alertsAPI } from './alerts';
export { default as smartListsAPI } from './smartLists';
export { default as aiAPI } from './ai';

// Combined API object for easy access
import searchV2API from './search';
import comparisonAPI from './comparison';
import analyticsAPI from './analytics';
import alertsAPI from './alerts';
import smartListsAPI from './smartLists';
import aiAPI from './ai';

export const API = {
  search: searchV2API,
  comparison: comparisonAPI,
  analytics: analyticsAPI,
  alerts: alertsAPI,
  smartLists: smartListsAPI,
  ai: aiAPI,
};

export default API;
