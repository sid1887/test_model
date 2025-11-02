# 🔌 Cumpair Backend API Integration Map

## 📊 Complete Backend API Endpoints

### 🔍 **Search V2 - God Engine** (`/api/v2/`)

| Endpoint | Method | Description | Status |
|----------|--------|-------------|---------|
| `/search` | GET | Unified search (cache + FAISS + AI) | ✅ Backend Ready |
| `/search/stream` | GET | SSE streaming search | ✅ Backend Ready |
| `/search/image` | POST | Image upload → CLIP search | ✅ Backend Ready |
| `/search/voice` | POST | Voice → STT → search | ⚠️ Coming soon |
| `/product/{id}/complete` | GET | Complete product context | ✅ Backend Ready |

### 🖼️ **AI Features** (`/api/`)

| Endpoint | Method | Description | Status |
|----------|--------|-------------|---------|
| `/images/upload` | POST | Upload image for processing | ✅ Backend Ready |
| `/images/analyze` | POST | Analyze image (CLIP, barcode, OCR) | ✅ Backend Ready |
| `/clip/compare` | POST | CLIP similarity search | ✅ Backend Ready |
| `/barcode/decode` | POST | Decode barcode/QR | ✅ Backend Ready |
| `/ocr/receipt` | POST | Extract receipt text | ✅ Backend Ready |
| `/text/generate` | POST | HuggingFace text generation | ✅ Backend Ready |
| `/text/analyze` | POST | Sentiment, NER, summarize | ✅ Backend Ready |
| `/embeddings` | POST | Get text embeddings | ✅ Backend Ready |
| `/voice/transcribe` | POST | Speech-to-text | ✅ Backend Ready |
| `/captcha/solve` | POST | Self-hosted CAPTCHA solver | ✅ Backend Ready |

### 💰 **Price Comparison** (`/api/comparison/`)

| Endpoint | Method | Description | Status |
|----------|--------|-------------|---------|
| `/compare/{product_id}` | GET | Get price comparison results | ✅ Backend Ready |
| `/compare/{product_id}/refresh` | POST | Trigger new price scraping | ✅ Backend Ready |
| `/compare/{product_id}/history` | GET | Price history | ✅ Backend Ready |
| `/real-time-search` | POST | Live scraper search (15+ retailers) | ✅ Backend Ready |
| `/smart-search` | POST | CLIP + scraper search | ✅ Backend Ready |
| `/enhanced-search` | POST | Filtered retailer search | ✅ Backend Ready |
| `/search-by-image` | POST | Image → AI → scraper | ✅ Backend Ready |
| `/search-by-barcode` | POST | Barcode → scraper | ✅ Backend Ready |
| `/retailers` | GET | List all 15+ retailers | ✅ Backend Ready |
| `/retailers/{key}/config` | GET | Retailer configuration | ✅ Backend Ready |
| `/retailers/{key}/status` | POST | Update retailer status | ✅ Backend Ready |
| `/sources` | GET | Available price sources | ✅ Backend Ready |
| `/stats` | GET | Comparison statistics | ✅ Backend Ready |

### 📊 **Analytics** (`/api/analytics/`)

| Endpoint | Method | Description | Status |
|----------|--------|-------------|---------|
| `/overview` | GET | Dashboard stats | ✅ Backend Ready |
| `/product/{id}/trends` | GET | Price trends over time | ✅ Backend Ready |
| `/product/{id}/forecast` | GET | Price predictions | ✅ Backend Ready |
| `/product/{id}/forecast/generate` | POST | Generate new forecast | ✅ Backend Ready |
| `/sentiment/{id}` | GET | Sentiment analysis | ✅ Backend Ready |
| `/sentiment/{id}/analyze` | POST | Trigger sentiment analysis | ✅ Backend Ready |
| `/retailers/comparison` | GET | Retailer performance | ✅ Backend Ready |
| `/anomalies` | GET | Price anomalies | ✅ Backend Ready |
| `/products/trending` | GET | Trending products | ✅ Backend Ready |

### 🔔 **Price Alerts** (`/api/alerts/`)

| Endpoint | Method | Description | Status |
|----------|--------|-------------|---------|
| `/` | GET | List alerts | ✅ Backend Ready |
| `/` | POST | Create alert | ✅ Backend Ready |
| `/{id}` | GET | Get alert details | ✅ Backend Ready |
| `/{id}` | PUT | Update alert | ✅ Backend Ready |
| `/{id}` | DELETE | Delete alert | ✅ Backend Ready |
| `/{id}/trigger-now` | POST | Manual trigger | ✅ Backend Ready |
| `/{id}/pause` | POST | Pause alert | ✅ Backend Ready |
| `/{id}/resume` | POST | Resume alert | ✅ Backend Ready |
| `/{id}/history` | GET | Alert history | ✅ Backend Ready |
| `/{id}/notifications` | GET | Alert notifications | ✅ Backend Ready |
| `/preferences` | GET/PUT | User preferences | ✅ Backend Ready |
| **WebSocket** `/ws/alerts` | - | Real-time updates | ✅ Backend Ready |

### 📝 **Smart Lists** (`/api/lists/`)

| Endpoint | Method | Description | Status |
|----------|--------|-------------|---------|
| `/` | GET | List all lists | ✅ Backend Ready |
| `/` | POST | Create list | ✅ Backend Ready |
| `/{id}` | GET | Get list details | ✅ Backend Ready |
| `/{id}` | PUT | Update list | ✅ Backend Ready |
| `/{id}` | DELETE | Delete list | ✅ Backend Ready |
| `/{id}/items` | POST | Add item | ✅ Backend Ready |
| `/{id}/items/{item_id}` | PUT | Update item | ✅ Backend Ready |
| `/{id}/items/{item_id}` | DELETE | Delete item | ✅ Backend Ready |
| `/{id}/items/reorder` | POST | Reorder items | ✅ Backend Ready |
| `/{id}/compare` | POST | Start comparison job | ✅ Backend Ready |
| `/compare-jobs/{job_id}` | GET | Get job status | ✅ Backend Ready |
| `/compare-jobs/{job_id}/stream` | GET | SSE job stream | ✅ Backend Ready |
| `/templates` | GET | List templates | ✅ Backend Ready |
| `/templates/{id}/apply` | POST | Apply template | ✅ Backend Ready |

### 🛍️ **Products** (`/api/products/`)

| Endpoint | Method | Description | Status |
|----------|--------|-------------|---------|
| `/` | GET | List products | ✅ Backend Ready |
| `/` | POST | Create product | ✅ Backend Ready |
| `/{id}` | GET | Get product | ✅ Backend Ready |
| `/{id}` | PUT | Update product | ✅ Backend Ready |
| `/{id}` | DELETE | Delete product | ✅ Backend Ready |
| `/stats/summary` | GET | Product statistics | ✅ Backend Ready |

### 🏪 **Retailers** (`/api/retailers/`)

| Endpoint | Method | Description | Status |
|----------|--------|-------------|---------|
| `/` | GET | List retailers | ✅ Backend Ready |
| `/{id}` | GET | Get retailer details | ✅ Backend Ready |

### 🌱 **Seed Data** (`/api/seed/`)

| Endpoint | Method | Description | Status |
|----------|--------|-------------|---------|
| `/products` | GET | Get seed products | ✅ Backend Ready |
| `/products/{id}` | GET | Get seed product | ✅ Backend Ready |
| `/stats` | GET | Seed stats | ✅ Backend Ready |
| `/retailers` | GET | Seed retailers | ✅ Backend Ready |

### 👤 **User** (`/api/user/`)

| Endpoint | Method | Description | Status |
|----------|--------|-------------|---------|
| `/location` | GET/POST | User location | ✅ Backend Ready |
| `/preferences` | GET/POST | User preferences | ✅ Backend Ready |

### 🏥 **Health** (`/api/v1/health/`)

| Endpoint | Method | Description | Status |
|----------|--------|-------------|---------|
| `/` | GET | Basic health | ✅ Backend Ready |
| `/detailed` | GET | Detailed health | ✅ Backend Ready |
| `/ai-models` | GET | AI model status | ✅ Backend Ready |
| `/services` | GET | Service status | ✅ Backend Ready |

---

## 🎯 Frontend Integration Strategy

### **Phase 1: Core Search Features** (Priority 1)

#### 1. **Enhanced SearchPage** (`/search`)
**Connects to:**
- `POST /api/v2/search` - Main search
- `GET /api/v2/search/stream` - Streaming results
- `POST /api/images/upload` - Image upload
- `POST /api/images/analyze` - Image analysis
- `POST /api/clip/compare` - CLIP search
- `POST /api/comparison/search-by-image` - Image → scraper
- `POST /api/comparison/real-time-search` - Live prices
- `POST /api/voice/transcribe` - Voice search

**Features to Build:**
- [ ] Drag-drop image upload zone
- [ ] Image preview with analysis status
- [ ] CLIP similarity results grid
- [ ] Barcode detection feedback
- [ ] Voice recording with waveform
- [ ] STT transcription display
- [ ] Streaming search with ghost→real morphing
- [ ] Real-time price comparison grid

#### 2. **Product Details Modal**
**Connects to:**
- `GET /api/v2/product/{id}/complete` - Complete context
- `GET /api/analytics/product/{id}/trends` - Price history
- `GET /api/analytics/sentiment/{id}` - Sentiment
- `GET /api/comparison/compare/{id}` - Price comparison

**Features to Build:**
- [ ] Modal with price history chart
- [ ] AI-generated insights
- [ ] Similar products carousel
- [ ] Retailer comparison table
- [ ] Real-time price ticker
- [ ] Sentiment meter
- [ ] Quick actions (add to list, create alert)

#### 3. **Real-time Price Comparison**
**Connects to:**
- `POST /api/comparison/real-time-search` - Live search
- `POST /api/comparison/smart-search` - CLIP + search
- `GET /api/comparison/retailers` - Retailer list
- `POST /api/comparison/enhanced-search` - Filtered search

**Features to Build:**
- [ ] Retailer filter (category, priority)
- [ ] Live search results table
- [ ] Price statistics card
- [ ] Best deal highlighting
- [ ] Refresh button with loading
- [ ] Export comparison results

---

### **Phase 2: Analytics & Insights** (Priority 2)

#### 4. **Enhanced Analytics Page** (`/analytics`)
**Connects to:**
- `GET /api/analytics/overview` - Dashboard stats
- `GET /api/analytics/product/{id}/trends` - Trends
- `GET /api/analytics/product/{id}/forecast` - Forecast
- `GET /api/analytics/sentiment/{id}` - Sentiment
- `GET /api/analytics/retailers/comparison` - Retailers
- `GET /api/analytics/anomalies` - Anomalies
- `GET /api/analytics/products/trending` - Trending

**Features to Build:**
- [ ] Connect overview stats (real numbers)
- [ ] Interactive price trend charts
- [ ] Forecast predictions with confidence
- [ ] Sentiment analysis visualization
- [ ] Retailer performance comparison
- [ ] Anomaly detection alerts
- [ ] Trending products feed

#### 5. **AI Insights Dashboard** (`/ai-insights` - NEW PAGE)
**Connects to:**
- `POST /api/text/generate` - Text generation
- `POST /api/text/analyze` - Text analysis
- `POST /api/analytics/product/{id}/forecast/generate` - Generate forecast
- `POST /api/analytics/sentiment/{id}/analyze` - Analyze sentiment
- `POST /api/embeddings` - Embeddings

**Features to Build:**
- [ ] Product recommendation engine
- [ ] AI-generated insights
- [ ] Sentiment trends over time
- [ ] Price prediction confidence
- [ ] Category insights
- [ ] Market trend analysis

---

### **Phase 3: Smart Lists & Alerts** (Priority 3)

#### 6. **Enhanced Smart Lists Page** (`/lists`)
**Connects to:**
- All `/api/lists/` endpoints
- `POST /api/lists/{id}/compare` - Start comparison
- `GET /api/lists/compare-jobs/{id}/stream` - SSE stream
- `GET /api/lists/templates` - Templates

**Features to Build:**
- [ ] Connect all CRUD operations
- [ ] Drag-drop item reordering
- [ ] Template selector with preview
- [ ] Comparison job with progress
- [ ] SSE streaming for live updates
- [ ] Best deals from comparison

#### 7. **Enhanced Price Alerts Page** (`/alerts`)
**Connects to:**
- All `/api/alerts/` endpoints
- `WebSocket /ws/alerts` - Real-time updates

**Features to Build:**
- [ ] WebSocket connection for live updates
- [ ] Real-time alert firing notifications
- [ ] Live price ticker
- [ ] Alert history timeline
- [ ] Notification preferences
- [ ] Batch operations

---

### **Phase 4: Advanced Features** (Priority 4)

#### 8. **Retailer Management** (Admin/Settings)
**Connects to:**
- `GET /api/comparison/retailers` - List retailers
- `GET /api/comparison/retailers/{key}/config` - Config
- `POST /api/comparison/retailers/{key}/status` - Update status

**Features to Build:**
- [ ] Retailer grid with status
- [ ] Category filtering
- [ ] Priority management
- [ ] Enable/disable retailers
- [ ] Performance metrics

#### 9. **Barcode Scanner**
**Connects to:**
- `POST /api/barcode/decode` - Decode barcode
- `POST /api/comparison/search-by-barcode` - Search

**Features to Build:**
- [ ] Camera access for scanning
- [ ] Barcode detection overlay
- [ ] Instant product search
- [ ] Manual barcode entry

#### 10. **OCR Receipt Scanner**
**Connects to:**
- `POST /api/ocr/receipt` - Extract text
- Receipt parsing integration

**Features to Build:**
- [ ] Receipt image upload
- [ ] Line item extraction
- [ ] Price sum calculations
- [ ] Export to shopping list

---

## 🛠️ Technical Implementation Plan

### **API Client Setup**

```typescript
// frontend/src/lib/api-client.ts
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add request interceptor for auth
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Add response interceptor for errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
    }
    return Promise.reject(error);
  }
);
```

### **Custom Hooks for Each Feature**

```typescript
// frontend/src/hooks/useImageSearch.ts
export const useImageSearch = () => {
  const [uploading, setUploading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  
  const uploadImage = async (file: File) => {
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await apiClient.post('/api/images/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    
    setUploading(false);
    return response.data;
  };
  
  const analyzeImage = async (imageId: string) => {
    setAnalyzing(true);
    const response = await apiClient.post('/api/images/analyze', {
      image_id: imageId,
      tasks: ['clip', 'barcode', 'ocr']
    });
    setAnalyzing(false);
    return response.data;
  };
  
  return { uploadImage, analyzeImage, uploading, analyzing };
};
```

### **WebSocket Connection**

```typescript
// frontend/src/lib/websocket.ts
export class AlertsWebSocket {
  private ws: WebSocket | null = null;
  
  connect(onMessage: (data: any) => void) {
    const WS_URL = 'ws://localhost:8000/ws/alerts';
    this.ws = new WebSocket(WS_URL);
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data);
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }
  
  disconnect() {
    this.ws?.close();
  }
}
```

### **SSE (Server-Sent Events)**

```typescript
// frontend/src/hooks/useStreamingSearch.ts
export const useStreamingSearch = () => {
  const [results, setResults] = useState<any[]>([]);
  const [phase, setPhase] = useState<string>('idle');
  
  const startSearch = (query: string) => {
    const eventSource = new EventSource(
      `${API_BASE}/api/v2/search/stream?q=${encodeURIComponent(query)}`
    );
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.phase === 'ghost') {
        setPhase('ghost');
        setResults(data.results);
      } else if (data.phase === 'real') {
        setPhase('real');
        setResults(data.results);
      } else if (data.phase === 'complete') {
        eventSource.close();
        setPhase('complete');
      }
    };
    
    return () => eventSource.close();
  };
  
  return { results, phase, startSearch };
};
```

---

## ✅ Implementation Checklist

### **Core Integrations**
- [ ] Setup API client with axios
- [ ] Create custom hooks for each feature
- [ ] Setup WebSocket for alerts
- [ ] Setup SSE for streaming
- [ ] Error handling and loading states
- [ ] Toast notifications for feedback

### **Search Features**
- [ ] Image upload + CLIP search
- [ ] Voice recording + transcription
- [ ] Barcode detection + search
- [ ] Streaming search with SSE
- [ ] Real-time price comparison

### **Analytics Features**
- [ ] Dashboard stats
- [ ] Price trends charts
- [ ] Forecasting visualization
- [ ] Sentiment analysis
- [ ] Retailer comparison

### **Smart Lists**
- [ ] CRUD operations
- [ ] Comparison jobs
- [ ] SSE streaming
- [ ] Templates

### **Price Alerts**
- [ ] WebSocket real-time updates
- [ ] Alert management
- [ ] Notifications

---

**Let's start implementing! 🚀**
