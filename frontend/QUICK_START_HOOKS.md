# Quick Start: Using the New Connector Hooks

## 🚀 Installation Complete

All React Query connector hooks are now available! Here's how to use them in your pages.

## 📦 Import Pattern

```tsx
// Import from the barrel export
import { 
  useAnalyticsOverview,
  useTrendingProducts,
  useAlerts,
  useAlertsWebSocket,
  useUnifiedSearchV2,
  useSmartLists
} from '@/hooks/api';
```

## 🎯 5-Minute Quick Wins

### 1. Home Page - Replace Mock Trending Products (2 minutes)

**File**: `frontend/src/pages/Index.tsx`

**Find this:**
```tsx
const featuredProducts = [
  {
    id: '1',
    title: 'Sony WH-1000XM5 Headphones',
    // ... mock data
  },
  // ... more mock products
];
```

**Replace with:**
```tsx
import { useTrendingProducts } from '@/hooks/api';

// Inside component
const { data: featuredProducts, isLoading } = useTrendingProducts(undefined, 12);

if (isLoading) {
  return <AetherSkeleton count={12} />;
}
```

**Result**: ✅ Real trending products from backend!

---

### 2. Analytics Page - Real Dashboard Data (3 minutes)

**File**: `frontend/src/pages/Analytics.tsx`

**Find this:**
```tsx
import { useAnalytics } from '@/hooks/useAnalytics';
const { data } = useAnalytics();
```

**Replace with:**
```tsx
import { 
  useAnalyticsOverview, 
  useTrendingProducts,
  usePriceAnomalies 
} from '@/hooks/api';

// Inside component
const { data: overview, isLoading } = useAnalyticsOverview();
const { data: trending } = useTrendingProducts(undefined, 10);
const { data: anomalies } = usePriceAnomalies(0.8, 5);

if (isLoading) return <AetherSkeleton />;
```

**Result**: ✅ Real analytics data with auto-refresh!

---

### 3. Price Alerts - Add Real-Time Updates (5 minutes)

**File**: `frontend/src/pages/PriceAlerts.tsx`

**Add at the top:**
```tsx
import { 
  useAlerts, 
  useCreateAlert, 
  useUpdateAlert,
  useDeleteAlert,
  useAlertsWebSocket 
} from '@/hooks/api';

function PriceAlertsPage() {
  // Replace mock data
  const { data: alerts, isLoading } = useAlerts(true);
  
  // Add CRUD operations
  const createAlert = useCreateAlert();
  const updateAlert = useUpdateAlert();
  const deleteAlert = useDeleteAlert();
  
  // Add real-time WebSocket
  const { messages, isConnected } = useAlertsWebSocket();
  
  // WebSocket messages automatically show toast notifications!
  // No extra code needed - it's built into the hook
  
  const handleCreate = async (values) => {
    await createAlert.mutateAsync(values);
    // Toast shown automatically!
  };
  
  return (
    <div>
      {/* Show connection status */}
      <ConnectionBadge connected={isConnected} />
      
      {/* Rest of your UI stays the same! */}
      <AlertsList alerts={alerts} onDelete={deleteAlert.mutate} />
    </div>
  );
}
```

**Result**: ✅ Real alerts with live updates via WebSocket!

---

## 🎨 Complete Examples by Feature

### Analytics Dashboard
```tsx
import { 
  useAnalyticsOverview,
  useTrendingProducts,
  usePriceAnomalies,
  useProductTrends 
} from '@/hooks/api';

function AnalyticsDashboard() {
  const { data: overview } = useAnalyticsOverview();
  const { data: trending } = useTrendingProducts(undefined, 10);
  const { data: anomalies } = usePriceAnomalies(0.8, 5);

  return (
    <Grid>
      <StatCard title="Total Products" value={overview?.total_products} />
      <StatCard title="Active Alerts" value={overview?.active_alerts} />
      <TrendingProductsWidget products={trending} />
      <AnomaliesWidget anomalies={anomalies} />
    </Grid>
  );
}
```

### Search with Voice
```tsx
import { 
  useUnifiedSearchV2, 
  useImageSearchV2,
  useVoiceSearchV2 
} from '@/hooks/api';

function SearchPage() {
  const [query, setQuery] = useState('');
  const { data: textResults } = useUnifiedSearchV2(query, { use_cache: true });
  
  const imageSearch = useImageSearchV2();
  const voiceSearch = useVoiceSearchV2();

  const handleVoiceRecord = (audioBlob: Blob) => {
    voiceSearch.mutate(audioBlob, {
      onSuccess: (data) => {
        setQuery(data.transcription);
      }
    });
  };

  return (
    <div>
      <SearchBar value={query} onChange={setQuery} />
      <VoiceButton onRecord={handleVoiceRecord} />
      <ImageUpload onUpload={(file) => imageSearch.mutate({ file })} />
      <Results data={textResults || imageSearch.data?.results} />
    </div>
  );
}
```

### Smart Lists with Progress
```tsx
import { 
  useSmartLists,
  useStartComparisonJob,
  useComparisonJobStream 
} from '@/hooks/api';

function SmartListsPage() {
  const { data: lists } = useSmartLists();
  const startJob = useStartComparisonJob();
  const [jobId, setJobId] = useState('');
  
  const { progress, status, finalJob } = useComparisonJobStream(jobId);

  const handleStartComparison = async (listId: number) => {
    const result = await startJob.mutateAsync({ listId });
    setJobId(result.job_id);
  };

  return (
    <div>
      <ListsGrid 
        lists={lists} 
        onCompare={handleStartComparison}
      />
      
      {jobId && (
        <ProgressOverlay>
          <ProgressBar value={progress} />
          <StatusBadge status={status} />
        </ProgressOverlay>
      )}
      
      {status === 'completed' && finalJob && (
        <ResultsModal job={finalJob} />
      )}
    </div>
  );
}
```

### Price Comparison
```tsx
import { 
  usePriceComparison,
  useRetailers,
  useRefreshPriceComparison 
} from '@/hooks/api';

function ProductPage({ productId }) {
  const { data: comparison } = usePriceComparison(productId);
  const { data: retailers } = useRetailers(undefined, true);
  const refresh = useRefreshPriceComparison();

  const handleRefresh = () => {
    refresh.mutate(productId);
    // Toast shown automatically!
  };

  return (
    <div>
      <BestDealCard deal={comparison?.statistics.best_deal} />
      <PriceChart data={comparison?.comparisons} />
      <RetailersList retailers={retailers} />
      <RefreshButton 
        onClick={handleRefresh} 
        loading={refresh.isPending}
      />
    </div>
  );
}
```

## 🎁 Built-in Features

### 1. Automatic Loading States
```tsx
const { data, isLoading, isPending, error } = useAnalyticsOverview();

if (isLoading) return <Skeleton />;
if (error) return <ErrorState error={error} />;
return <Dashboard data={data} />;
```

### 2. Automatic Refetch
```tsx
const { data, refetch } = useTrendingProducts();

// Manual refetch
<Button onClick={() => refetch()}>Refresh</Button>

// Or it auto-refreshes every 5 minutes (configured in hook)
```

### 3. Automatic Cache
```tsx
// First call - hits API
const { data } = useTrendingProducts();

// Second call (within 2 minutes) - uses cache!
const { data: cached } = useTrendingProducts();

// After 2 minutes - automatically refetches
```

### 4. Toast Notifications
```tsx
const createAlert = useCreateAlert();

// Success toast shown automatically
await createAlert.mutateAsync(newAlert);

// Error toast shown automatically on failure
```

### 5. Real-time Updates
```tsx
// WebSocket
const { messages, isConnected } = useAlertsWebSocket();
// Auto-connect, auto-reconnect, toast on alerts

// SSE Streaming
const { progress, status, updates } = useComparisonJobStream(jobId);
// Real-time progress updates, automatic cleanup
```

## 📚 Full Hook Reference

See [`CONNECTOR_HOOKS_COMPLETE.md`](./CONNECTOR_HOOKS_COMPLETE.md) for:
- All 69 hooks documented
- Complete TypeScript types
- Advanced usage patterns
- Best practices

## 🎯 Migration Priority

1. ✅ **Easiest First**: Index.tsx (2 minutes)
2. ✅ **High Impact**: Analytics.tsx (3 minutes)
3. ✅ **Most Exciting**: PriceAlerts.tsx with WebSocket (5 minutes)
4. ⏳ **Enhanced**: SearchPage.tsx (15 minutes)
5. ⏳ **Advanced**: SmartLists.tsx with SSE (20 minutes)

## 💡 Pro Tips

### Combine Multiple Hooks
```tsx
// Compose data from multiple sources
const { data: products } = useTrendingProducts();
const { data: alerts } = useAlerts();
const { data: comparison } = usePriceComparison(productId);

// All cached, all typed, all automatic!
```

### Conditional Fetching
```tsx
// Only fetch when needed
const { data } = usePriceComparison(productId, {
  enabled: !!productId && isModalOpen
});
```

### Optimistic Updates
```tsx
const updateAlert = useUpdateAlert();

updateAlert.mutate(
  { alertId, request },
  {
    onMutate: async (variables) => {
      // Optimistically update UI
      const previous = queryClient.getQueryData(['alerts', alertId]);
      queryClient.setQueryData(['alerts', alertId], variables.request);
      return { previous };
    },
    onError: (err, variables, context) => {
      // Rollback on error
      queryClient.setQueryData(['alerts', alertId], context.previous);
    }
  }
);
```

## 🎊 You're Ready!

All hooks are:
- ✅ Fully typed
- ✅ Tested and working
- ✅ Documented
- ✅ Ready to use

Just import and replace mock data. Your beautiful UI stays the same, but now with **REAL DATA**!

---

*Quick reference for Phase 3 integration*
