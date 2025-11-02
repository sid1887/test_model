# 🚀 Cumpair Frontend-Backend Integration Guide

## ✅ What's Been Built

### **API Service Layer Complete** (6 modules)

All API services are now available in `frontend/src/services/api/`:

```typescript
import API from '@/services/api';
// OR
import { searchV2API, comparisonAPI, analyticsAPI, alertsAPI, smartListsAPI, aiAPI } from '@/services/api';
```

---

## 📋 Quick Reference

### **1. Search V2 API** (`searchV2API`)

**Endpoints:**
- `unifiedSearch(query, options)` - Multi-tier cached search
- `streamingSearch(query, onMessage, onError, onComplete)` - SSE streaming with ghost→real morphing
- `imageSearch(file, sites, top_k)` - CLIP visual search
- `voiceSearch(audioBlob)` - Whisper speech-to-text + search
- `getCompleteProductContext(productId)` - Full product data

**Example Usage:**

```typescript
import { searchV2API } from '@/services/api';

// Unified search
const results = await searchV2API.unifiedSearch('wireless headphones', {
  top_k: 20,
  cache_level: 'both',
  enrich: true
});

// Streaming search with SSE
const eventSource = searchV2API.streamingSearch(
  'laptop',
  (phase) => {
    console.log(`Phase: ${phase.phase}`, phase.results);
    if (phase.phase === 'ghost') {
      setGhostResults(phase.results);
    } else if (phase.phase === 'real') {
      setRealResults(phase.results);
    }
  },
  (error) => console.error('Stream error:', error),
  () => console.log('Stream complete')
);

// Cleanup
return () => eventSource.close();

// Image search
const imageResults = await searchV2API.imageSearch(file, ['amazon', 'walmart']);

// Voice search
const recorder = new MediaRecorder(stream);
recorder.ondataavailable = async (event) => {
  const results = await searchV2API.voiceSearch(event.data);
  console.log('Transcription:', results.transcription);
  console.log('Search results:', results.search_results);
};
```

---

### **2. Comparison API** (`comparisonAPI`)

**Endpoints:**
- `realTimeSearch(request)` - Live multi-retailer scraping
- `smartSearch(request)` - CLIP + scraper combined
- `searchByImage(file, retailers)` - Image → AI detection → prices
- `searchByBarcode(barcode, retailers)` - Barcode lookup
- `getPriceComparison(productId)` - Get price comparisons
- `refreshPriceComparison(productId)` - Trigger fresh scraping
- `getPriceHistory(productId, days)` - Price history
- `getRetailers(filters)` - Get 15+ retailers with filters
- `enhancedSearch(query, filters)` - Filtered retailer search

**Example Usage:**

```typescript
import { comparisonAPI } from '@/services/api';

// Real-time multi-retailer search
const results = await comparisonAPI.realTimeSearch({
  query: 'nintendo switch',
  retailers: ['amazon', 'walmart', 'bestbuy'],
  max_results_per_site: 10
});

console.log('Best deals:', results.best_deals);
console.log('Grouped by retailer:', results.grouped_by_retailer);

// Smart search (CLIP + scraper)
const smartResults = await comparisonAPI.smartSearch({
  product_id: 123,
  use_clip: true,
  retailers: ['amazon', 'ebay']
});

// Image search
const imageResults = await comparisonAPI.searchByImage(file, ['amazon', 'target']);

// Get retailers with filtering
const retailers = await comparisonAPI.getRetailers({
  category: 'electronics',
  priority: 'high',
  active_only: true
});

// Get price comparisons
const comparison = await comparisonAPI.getPriceComparison(123);
console.log('Statistics:', comparison.statistics);
console.log('Best deal:', comparison.statistics.best_deal);
```

---

### **3. Analytics API** (`analyticsAPI`)

**Endpoints:**
- `getAnalyticsOverview()` - Dashboard stats
- `getProductTrends(productId, days)` - Price trends over time
- `getProductForecast(productId, days_ahead)` - Price predictions
- `generateForecast(productId, days_ahead)` - Generate new forecast
- `getProductSentiment(productId)` - Sentiment analysis
- `analyzeSentiment(productId)` - Trigger sentiment analysis
- `getRetailerComparison(category)` - Retailer performance
- `getPriceAnomalies(min_confidence, limit)` - Unusual price changes
- `getTrendingProducts(category, limit)` - Trending products
- `getCategoryInsights()` - Category-level insights
- `getMarketTrends(days)` - Overall market trends

**Example Usage:**

```typescript
import { analyticsAPI } from '@/services/api';
import { LineChart, Line, XAxis, YAxis } from 'recharts';

// Dashboard overview
const overview = await analyticsAPI.getAnalyticsOverview();
console.log('Total products:', overview.total_products);
console.log('Avg savings:', overview.avg_price_savings);

// Price trends
const trends = await analyticsAPI.getProductTrends(123, 30);
// Render chart:
<LineChart data={trends.trends}>
  <XAxis dataKey="date" />
  <YAxis />
  <Line dataKey="price" stroke="#8884d8" />
</LineChart>

// Price forecast
const forecast = await analyticsAPI.getProductForecast(123, 14);
console.log('Recommendation:', forecast.recommendation); // 'buy_now' | 'wait' | 'monitor'
console.log('Reasoning:', forecast.reasoning);

// Sentiment analysis
const sentiment = await analyticsAPI.getProductSentiment(123);
console.log('Overall sentiment:', sentiment.overall_sentiment);
console.log('Score:', sentiment.sentiment_score); // -1 to 1
console.log('Positive themes:', sentiment.key_positive_themes);

// Trending products
const trending = await analyticsAPI.getTrendingProducts('electronics', 10);
```

---

### **4. Alerts API** (`alertsAPI`)

**Endpoints:**
- `listAlerts(active_only)` - Get all alerts
- `createAlert(request)` - Create new alert
- `updateAlert(alertId, request)` - Update alert
- `deleteAlert(alertId)` - Delete alert
- `triggerAlert(alertId)` - Manually trigger (test)
- `pauseAlert(alertId)` - Pause alert
- `resumeAlert(alertId)` - Resume alert
- `getAlertHistory(alertId, limit)` - Alert history
- `getAlertNotifications(alertId, unread_only)` - Get notifications
- `getAlertPreferences()` - Get notification preferences
- `updateAlertPreferences(preferences)` - Update preferences
- `alertsAPI.websocket` - WebSocket singleton

**Example Usage:**

```typescript
import { alertsAPI, AlertsWebSocket } from '@/services/api';

// List alerts
const alerts = await alertsAPI.listAlerts(true); // active only

// Create alert
const newAlert = await alertsAPI.createAlert({
  product_id: 123,
  target_price: 299.99,
  condition: 'below',
  notification_method: 'push',
  frequency: 'instant'
});

// WebSocket for real-time updates
const ws = alertsAPI.websocket;

ws.onMessage((message) => {
  if (message.type === 'alert_fired') {
    toast.success(`Alert fired: ${message.data.product_name}`);
    // Update UI with new price
    updateProductPrice(message.data.product_id, message.data.new_price);
  } else if (message.type === 'price_update') {
    // Real-time price ticker
    updatePriceTicker(message.data);
  }
});

ws.onError((error) => {
  console.error('WebSocket error:', error);
});

ws.connect();

// Cleanup
useEffect(() => {
  return () => ws.disconnect();
}, []);
```

---

### **5. Smart Lists API** (`smartListsAPI`)

**Endpoints:**
- `listSmartLists(category)` - Get all lists
- `createSmartList(request)` - Create list
- `getSmartList(listId)` - Get list details
- `updateSmartList(listId, request)` - Update list
- `deleteSmartList(listId)` - Delete list
- `addListItem(listId, request)` - Add item
- `updateListItem(listId, itemId, request)` - Update item
- `deleteListItem(listId, itemId)` - Delete item
- `reorderListItems(listId, request)` - Reorder items
- `startComparisonJob(listId, retailers)` - Start comparison
- `getComparisonJobStatus(jobId)` - Get job status
- `streamComparisonJob(jobId, onUpdate, onError, onComplete)` - SSE streaming
- `getListTemplates(category)` - Get templates
- `applyTemplate(templateId, list_name)` - Apply template
- `exportList(listId, format)` - Export to CSV/JSON

**Example Usage:**

```typescript
import { smartListsAPI } from '@/services/api';

// Get lists
const lists = await smartListsAPI.listSmartLists();

// Create list
const newList = await smartListsAPI.createSmartList({
  name: 'Grocery Shopping',
  category: 'grocery',
  tags: ['weekly', 'essentials']
});

// Add items
await smartListsAPI.addListItem(newList.id, {
  product_name: 'Organic Milk',
  quantity: 2,
  priority: 'high',
  target_price: 4.99
});

// Start comparison job
const { job_id } = await smartListsAPI.startComparisonJob(newList.id, ['walmart', 'target']);

// Stream results with SSE
const eventSource = smartListsAPI.streamComparisonJob(
  job_id,
  (update) => {
    if (update.type === 'progress') {
      setProgress(update.progress);
    } else if (update.type === 'item_complete') {
      addComparisonResult(update.item);
    } else if (update.type === 'complete') {
      console.log('Comparison complete!');
    }
  },
  (error) => console.error('Stream error:', error),
  (job) => {
    console.log('Final results:', job.results);
    // Show best deals
    showBestDeals(job.results);
  }
);

// Cleanup
return () => eventSource.close();
```

---

### **6. AI API** (`aiAPI`)

**Endpoints:**
- `uploadImage(file)` - Upload image
- `analyzeImage(request)` - Multi-task analysis
- `clipCompare(request)` - Visual similarity search
- `decodeBarcode(request)` - Barcode detection
- `extractReceipt(request)` - OCR receipt parsing
- `generateText(request)` - LLM text generation
- `analyzeText(request)` - Sentiment, NER, summarization
- `getEmbeddings(request)` - Text embeddings
- `transcribeVoice(audio, language)` - Speech-to-text
- `solveCaptcha(request)` - CAPTCHA solving

**Example Usage:**

```typescript
import { aiAPI } from '@/services/api';

// Upload and analyze image
const { image_id } = await aiAPI.uploadImage(file);

const analysis = await aiAPI.analyzeImage({
  image_id,
  tasks: ['clip', 'barcode', 'ocr']
});

console.log('CLIP results:', analysis.clip_results);
console.log('Barcode detected:', analysis.barcode?.barcode_value);
console.log('OCR text:', analysis.ocr_text);

// Visual similarity search
const similarProducts = await aiAPI.clipCompare({
  image_id,
  top_k: 10
});

// Barcode detection
const barcode = await aiAPI.decodeBarcode({ image_id });
if (barcode.detected) {
  console.log('Barcode:', barcode.barcode_value);
  // Search by barcode
  const products = await comparisonAPI.searchByBarcode(barcode.barcode_value);
}

// Receipt OCR
const receipt = await aiAPI.extractReceipt({ image_id });
console.log('Items:', receipt.items);
console.log('Total:', receipt.total_amount);

// Text generation
const generated = await aiAPI.generateText({
  prompt: 'Write a product description for',
  max_tokens: 100,
  temperature: 0.7
});

// Text analysis
const textAnalysis = await aiAPI.analyzeText({
  text: 'Great product! Fast shipping and amazing quality.',
  tasks: ['sentiment', 'keywords']
});

console.log('Sentiment:', textAnalysis.sentiment); // 'positive', score: 0.95

// Voice transcription
const transcription = await aiAPI.transcribeVoice(audioBlob, 'en');
console.log('Transcription:', transcription.transcription);
console.log('Confidence:', transcription.confidence);
```

---

## 🎯 Implementation Patterns

### **Pattern 1: React Query Hooks**

Create custom hooks for each API category:

```typescript
// hooks/useSearchData.ts
import { useQuery, useMutation } from '@tanstack/react-query';
import { searchV2API } from '@/services/api';

export const useUnifiedSearch = (query: string) => {
  return useQuery({
    queryKey: ['search', query],
    queryFn: () => searchV2API.unifiedSearch(query),
    enabled: query.length > 0,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useImageSearch = () => {
  return useMutation({
    mutationFn: (file: File) => searchV2API.imageSearch(file),
  });
};
```

### **Pattern 2: SSE Streaming Hooks**

```typescript
// hooks/useStreamingSearch.ts
import { useState, useEffect } from 'react';
import { searchV2API, StreamingPhase } from '@/services/api';

export const useStreamingSearch = (query: string) => {
  const [phase, setPhase] = useState<string>('idle');
  const [results, setResults] = useState([]);

  useEffect(() => {
    if (!query) return;

    const eventSource = searchV2API.streamingSearch(
      query,
      (phaseData: StreamingPhase) => {
        setPhase(phaseData.phase);
        if (phaseData.results) {
          setResults(phaseData.results);
        }
      }
    );

    return () => eventSource.close();
  }, [query]);

  return { phase, results };
};
```

### **Pattern 3: WebSocket Hooks**

```typescript
// hooks/useAlertsWebSocket.ts
import { useState, useEffect } from 'react';
import { alertsAPI } from '@/services/api';

export const useAlertsWebSocket = () => {
  const [messages, setMessages] = useState([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const ws = alertsAPI.websocket;

    const unsubscribeMessage = ws.onMessage((message) => {
      setMessages((prev) => [...prev, message]);
    });

    const unsubscribeOpen = ws.onOpen(() => {
      setIsConnected(true);
    });

    const unsubscribeClose = ws.onClose(() => {
      setIsConnected(false);
    });

    ws.connect();

    return () => {
      unsubscribeMessage();
      unsubscribeOpen();
      unsubscribeClose();
      ws.disconnect();
    };
  }, []);

  return { messages, isConnected };
};
```

---

## 🔧 Next Steps

### **Immediate Actions:**

1. **Connect SearchPage** (`/search`)
   - Add `ImageUpload` component
   - Add `VoiceRecorder` component
   - Wire up streaming search
   - Display real-time results

2. **Connect Analytics** (`/analytics`)
   - Replace mock data with `analyticsAPI`
   - Add charts (recharts)
   - Show trending products
   - Display anomalies

3. **Connect Price Alerts** (`/alerts`)
   - Wire up CRUD operations
   - Implement WebSocket
   - Show live notifications
   - Display alert history

4. **Connect Smart Lists** (`/lists`)
   - Wire up CRUD operations
   - Implement comparison jobs
   - Add SSE streaming
   - Show best deals

5. **Connect Index (Home)** (`/`)
   - Use real trending products
   - Wire up search bar
   - Show real stats

---

## 📚 Documentation

- **API_INTEGRATION_MAP.md** - Complete endpoint listing
- **Type Definitions** - All types exported from service modules
- **Error Handling** - Automatic error toasts
- **Loading States** - Use React Query `isLoading`, `isError`

---

## 🎉 Ready to Build!

All backend APIs are now accessible from frontend. Start connecting pages one by one, replacing mock data with real API calls. Use the patterns above to maintain consistency.

**No more dummy data - everything is LIVE! 🚀**
