# React Query Connector Hooks - Complete Documentation

> **Phase 2 Complete**: Bridge layer connecting API services to UI pages

## 📋 Overview

This directory contains React Query hooks that bridge the API service layer (`services/api/`) to the UI pages (`pages/`). These hooks provide:

- 🔄 **Automatic caching** with smart stale times
- 🔁 **Auto-refresh** for real-time data
- 🎯 **Cache invalidation** on mutations
- 🔔 **Toast notifications** for user feedback
- 🌐 **WebSocket support** for real-time updates
- 📡 **SSE support** for streaming data
- 📘 **Full TypeScript** typing

## 📁 File Structure

```
hooks/api/
├── index.ts                    # Barrel export
├── useAnalyticsData.ts         # Analytics & insights hooks (11 hooks) ✅
├── useSearchData.ts            # Search V2 hooks (4 hooks) ✅
├── useAlertsData.ts            # Price alerts + WebSocket (14 hooks) ✅
├── useSmartListsData.ts        # Smart lists + SSE streaming (15 hooks) ✅
├── useComparisonData.ts        # Price comparison hooks (15 hooks) ✅
└── useAIData.ts                # AI features hooks (10 hooks) ✅
```

## 🎣 Available Hooks (69 Total)

### 1. Analytics Hooks (`useAnalyticsData.ts`) - 11 hooks

**Query Hooks:**
- `useAnalyticsOverview()` - Dashboard statistics
- `useProductTrends(productId, days)` - Price trends over time
- `useProductForecast(productId, days_ahead)` - AI price predictions
- `useProductSentiment(productId)` - Sentiment analysis
- `useRetailerComparison(category)` - Retailer performance comparison
- `usePriceAnomalies(min_confidence, limit)` - Unusual price changes
- `useTrendingProducts(category, limit)` - Trending products
- `useCategoryInsights()` - Category insights
- `useMarketTrends(days)` - Market-wide trends

**Mutation Hooks:**
- `useGenerateForecast()` - Trigger forecast generation
- `useAnalyzeSentiment()` - Trigger sentiment analysis

**Example:**
```tsx
import { useAnalyticsOverview, useTrendingProducts } from '@/hooks/api';

function AnalyticsPage() {
  const { data: overview, isLoading } = useAnalyticsOverview();
  const { data: trending } = useTrendingProducts(undefined, 12);

  if (isLoading) return <Skeleton />;

  return (
    <div>
      <h1>Total Products: {overview?.total_products}</h1>
      <ProductGrid products={trending} />
    </div>
  );
}
```

---

### 2. Search Hooks (`useSearchData.ts`) - 4 hooks

**Query Hooks:**
- `useUnifiedSearchV2(query, options)` - Main search with multi-tier caching
- `useCompleteProductContextV2(productId)` - Full product data

**Mutation Hooks:**
- `useImageSearchV2()` - CLIP visual search
- `useVoiceSearchV2()` - Whisper speech-to-text search

**Example:**
```tsx
import { useUnifiedSearchV2, useImageSearchV2 } from '@/hooks/api';

function SearchPage() {
  const [query, setQuery] = useState('');
  const { data: results } = useUnifiedSearchV2(query, { use_cache: true });
  const imageSearch = useImageSearchV2();

  const handleImageUpload = (file: File) => {
    imageSearch.mutate({ file, top_k: 20 });
  };

  return <SearchResults results={results || imageSearch.data?.results} />;
}
```

---

### 3. Alerts Hooks (`useAlertsData.ts`) - 14 hooks

**Query Hooks:**
- `useAlerts(active_only)` - List all alerts
- `useAlert(alertId)` - Single alert details
- `useAlertHistory(alertId, limit)` - Historical triggers
- `useAlertNotifications(alertId, unread_only)` - Notifications

**Mutation Hooks:**
- `useCreateAlert()` - Create new alert
- `useUpdateAlert()` - Update alert
- `useDeleteAlert()` - Delete alert
- `useTriggerAlert()` - Manual test trigger
- `usePauseAlert()` - Pause monitoring
- `useResumeAlert()` - Resume monitoring
- `useAlertPreferences()` - Get/update preferences (nested mutation)

**WebSocket Hook:**
- `useAlertsWebSocket()` - Real-time connection with auto-reconnect

**Example:**
```tsx
import { useAlerts, useCreateAlert, useAlertsWebSocket } from '@/hooks/api';

function PriceAlertsPage() {
  const { data: alerts } = useAlerts(true);
  const createAlert = useCreateAlert();
  const { messages, isConnected } = useAlertsWebSocket();

  useEffect(() => {
    messages.forEach(msg => {
      if (msg.type === 'alert_fired') {
        // Toast notification already shown automatically!
        console.log('Alert fired:', msg.data);
      }
    });
  }, [messages]);

  return (
    <div>
      <ConnectionStatus connected={isConnected} />
      <AlertsList alerts={alerts} />
    </div>
  );
}
```

---

### 4. Smart Lists Hooks (`useSmartListsData.ts`) - 15 hooks

**Query Hooks:**
- `useSmartLists(category)` - List all lists
- `useSmartList(listId)` - Single list details
- `useComparisonJobStatus(jobId)` - Comparison job status (with polling)
- `useListTemplates(category)` - Available templates

**Mutation Hooks:**
- `useCreateSmartList()` - Create list
- `useUpdateSmartList()` - Update list
- `useDeleteSmartList()` - Delete list
- `useAddListItem()` - Add item
- `useUpdateListItem()` - Update item
- `useDeleteListItem()` - Delete item
- `useStartComparisonJob()` - Start comparison
- `useApplyTemplate()` - Apply template
- `useDuplicateList()` - Duplicate list
- `useExportList()` - Export list (CSV/JSON)

**SSE Streaming Hook:**
- `useComparisonJobStream(jobId)` - Real-time comparison progress

**Example:**
```tsx
import { useSmartLists, useStartComparisonJob, useComparisonJobStream } from '@/hooks/api';

function SmartListsPage() {
  const { data: lists } = useSmartLists();
  const startJob = useStartComparisonJob();
  const [jobId, setJobId] = useState('');
  const { progress, status, finalJob } = useComparisonJobStream(jobId);

  const handleCompare = async (listId: number) => {
    const result = await startJob.mutateAsync({ listId });
    setJobId(result.job_id);
  };

  return (
    <div>
      <ListsGrid lists={lists} onCompare={handleCompare} />
      {jobId && <ProgressBar progress={progress} status={status} />}
    </div>
  );
}
```

---

### 5. Comparison Hooks (`useComparisonData.ts`) - 15 hooks

**Query Hooks:**
- `usePriceComparison(productId)` - Price comparison with stats
- `useRetailers(category, active_only)` - Available retailers
- `usePriceHistory(productId, days)` - Historical prices
- `useComparisonStats()` - Overall statistics
- `usePriceSources()` - Price sources
- `useRetailerConfig(retailerKey)` - Retailer configuration

**Mutation Hooks:**
- `useRealTimeSearch()` - Live scraper search
- `useSmartSearch()` - CLIP + scraper combined
- `useSearchByImage()` - Image → AI → prices
- `useSearchByBarcode()` - Barcode lookup
- `useRefreshPriceComparison()` - Refresh prices
- `useUpdateRetailerStatus()` - Enable/disable retailer
- `useEnhancedSearch()` - Enhanced search with filters
- `useDeletePriceComparison()` - Delete comparison

**Example:**
```tsx
import { usePriceComparison, useRetailers, useRealTimeSearch } from '@/hooks/api';

function ComparisonPage({ productId }) {
  const { data: comparison } = usePriceComparison(productId);
  const { data: retailers } = useRetailers(undefined, true);
  const realTimeSearch = useRealTimeSearch();

  const handleSearch = (query: string) => {
    realTimeSearch.mutate({
      query,
      retailers: retailers?.map(r => r.key),
      max_results_per_site: 10
    });
  };

  return (
    <div>
      <BestDeal deal={comparison?.statistics.best_deal} />
      <PriceChart comparisons={comparison?.comparisons} />
    </div>
  );
}
```

---

### 6. AI Hooks (`useAIData.ts`) - 10 hooks

**All Mutation Hooks:**
- `useUploadImage()` - Upload image for processing
- `useAnalyzeImage()` - Image analysis (CLIP, OCR, caption, objects)
- `useCLIPCompare()` - Visual similarity comparison
- `useDecodeBarcode()` - Barcode detection & decoding
- `useExtractReceipt()` - OCR receipt extraction
- `useGenerateText()` - LLM text generation
- `useAnalyzeText()` - Sentiment, NER, summarization, keywords
- `useGetEmbeddings()` - Text embeddings
- `useTranscribeVoice()` - Whisper speech-to-text
- `useSolveCaptcha()` - CAPTCHA solving

**Example:**
```tsx
import { useUploadImage, useAnalyzeImage, useDecodeBarcode } from '@/hooks/api';

function AIFeaturesPage() {
  const uploadImage = useUploadImage();
  const analyzeImage = useAnalyzeImage();
  const decodeBarcode = useDecodeBarcode();

  const handleImageUpload = async (file: File) => {
    const uploaded = await uploadImage.mutateAsync(file);
    
    // Analyze the uploaded image
    const analysis = await analyzeImage.mutateAsync({
      image_id: uploaded.image_id,
      tasks: ['clip', 'barcode', 'ocr', 'caption']
    });

    if (analysis.barcode?.detected) {
      console.log('Barcode found:', analysis.barcode.barcode_value);
    }
  };

  return <ImageUploader onUpload={handleImageUpload} />;
}
```

---

## 🎯 Usage Patterns

### Pattern 1: Simple Query Hook
```tsx
const { data, isLoading, error, refetch } = useProductTrends(productId, 30);

if (isLoading) return <Skeleton />;
if (error) return <ErrorState error={error} />;

return <TrendsChart data={data} />;
```

### Pattern 2: Mutation Hook
```tsx
const createAlert = useCreateAlert();

const handleSubmit = async (values) => {
  try {
    await createAlert.mutateAsync(values);
    // Toast notification shown automatically!
  } catch (error) {
    // Error toast shown automatically!
  }
};

return (
  <Form onSubmit={handleSubmit}>
    {/* ... */}
    <Button disabled={createAlert.isPending}>
      {createAlert.isPending ? 'Creating...' : 'Create Alert'}
    </Button>
  </Form>
);
```

### Pattern 3: WebSocket Hook
```tsx
const { messages, isConnected, clearMessages } = useAlertsWebSocket();

useEffect(() => {
  messages.forEach(msg => {
    if (msg.type === 'alert_fired') {
      // Handle real-time alert
      // Toast notification already shown!
    }
  });
}, [messages]);

return <ConnectionIndicator connected={isConnected} />;
```

### Pattern 4: SSE Streaming Hook
```tsx
const { progress, status, updates, finalJob, reset } = useComparisonJobStream(jobId);

useEffect(() => {
  if (status === 'completed' && finalJob) {
    // Show results
    navigate(`/lists/${finalJob.list_id}`);
  }
}, [status, finalJob]);

return (
  <div>
    <ProgressBar value={progress} />
    <StatusBadge status={status} />
    <UpdatesFeed updates={updates} />
  </div>
);
```

## 🔧 Common Features

### Automatic Cache Invalidation
All mutation hooks automatically invalidate related queries:
```tsx
const createAlert = useCreateAlert();

createAlert.mutate(newAlert); // ← Automatically invalidates ['alerts'] cache
```

### Toast Notifications
All mutations include user feedback:
```tsx
const deleteAlert = useDeleteAlert();

deleteAlert.mutate(alertId); // ← Shows "Alert deleted!" toast on success
```

### Proper TypeScript Types
All hooks are fully typed with generics:
```tsx
const { data } = useAnalyticsOverview();
//     ^? AnalyticsOverview | undefined

const createAlert = useCreateAlert();
//    ^? UseMutationResult<PriceAlert, Error, CreateAlertRequest>
```

### Smart Stale Times
Different data gets different cache durations:
- **Real-time data** (alerts, overview): 1-2 minutes
- **Moderate data** (trends, comparisons): 5-10 minutes
- **Static data** (retailers, templates): 30 minutes

### Auto-Refresh
Volatile data auto-refreshes:
```tsx
// Analytics overview refreshes every 5 minutes
const { data } = useAnalyticsOverview();
// refetchInterval: 5 * 60 * 1000 (configured internally)
```

## 🚀 Next Steps

### Phase 3: Update Pages to Use New Hooks

1. **Update Analytics.tsx** - Replace old hooks with new analytics hooks
2. **Update SearchPage.tsx** - Use V2 search hooks
3. **Update PriceAlerts.tsx** - Add WebSocket for real-time updates
4. **Update SmartLists.tsx** - Add SSE streaming for comparison jobs
5. **Update Index.tsx** - Replace mock data with trending products

### Usage in Pages
```tsx
// ✅ DO THIS
import { 
  useAnalyticsOverview, 
  useTrendingProducts,
  useAlertsWebSocket 
} from '@/hooks/api';

// ❌ DON'T DO THIS
import { useAnalytics } from '@/hooks/useAnalytics'; // Old hook
```

## 📊 Coverage Summary

| Category | Hooks | Status | Real-time |
|----------|-------|--------|-----------|
| Analytics | 11 | ✅ Complete | Auto-refresh |
| Search | 4 | ✅ Complete | - |
| Alerts | 14 | ✅ Complete | ✅ WebSocket |
| Smart Lists | 15 | ✅ Complete | ✅ SSE |
| Comparison | 15 | ✅ Complete | - |
| AI | 10 | ✅ Complete | - |
| **Total** | **69** | **100%** | **2 protocols** |

## 🎉 Achievement

**Phase 2 Complete**: All 69 connector hooks created with:
- Full TypeScript typing
- React Query integration
- Toast notifications
- Cache management
- Real-time support (WebSocket + SSE)
- Auto-refresh capabilities

**Ready for Phase 3**: Update UI pages to use these hooks and replace all mock data with real backend data.

---

*Last Updated: Phase 2 Complete*
*Created by: GitHub Copilot*
