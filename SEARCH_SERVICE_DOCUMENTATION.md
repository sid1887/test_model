# Search & Discovery Service Documentation

## Overview

**Service:** Search & Discovery (Port 8010)
**Purpose:** Multi-method search (full-text + semantic CLIP + hybrid + image-based)
**Status:** Production-ready
**Lines of Code:** 850+
**Endpoints:** 20+

The Search & Discovery Service provides comprehensive product search capabilities using multiple search methods to deliver the most relevant results to users.

---

## Architecture

### Search Methods

#### 1. Full-Text Search
**Endpoint:** `POST /search/full-text`

Uses PostgreSQL's built-in Full-Text Search (FTS) with tsvector indexing.

**Implementation:**
```sql
SELECT
    id, title, price, rating, reviews_count,
    image_url, retailer, category,
    to_tsvector('english', title || ' ' || description) @@
    plainto_tsquery('english', $1) as relevance
FROM products
WHERE category = ANY($2)
AND price BETWEEN $3 AND $4
AND retailer = ANY($5)
ORDER BY ts_rank(to_tsvector('english', title || ' ' || description),
    plainto_tsquery('english', $1)) DESC
LIMIT $6 OFFSET $7
```

**Features:**
- Natural language query parsing
- Price range filtering
- Category filtering
- Retailer filtering
- Sort options: relevance (default), price_low, price_high, rating, newest, popularity
- Pagination support (page, limit)
- Execution time tracking

**Request:**
```json
{
    "query": "laptop under 1000",
    "category": ["Electronics"],
    "price_min": 0,
    "price_max": 1000,
    "retailer": ["Amazon", "Best Buy"],
    "sort_by": "relevance",
    "page": 1,
    "limit": 20
}
```

**Response:**
```json
{
    "query": "laptop under 1000",
    "type": "full-text",
    "total_results": 342,
    "page": 1,
    "limit": 20,
    "results": [
        {
            "product_id": "p123",
            "title": "XPS 13 Laptop",
            "price": 999.99,
            "rating": 4.8,
            "reviews": 2150,
            "image_url": "...",
            "retailer": "Amazon",
            "category": "Electronics",
            "relevance_score": 0.95
        }
    ],
    "facets": {
        "categories": [{"name": "Laptops", "count": 342}],
        "price_ranges": [{"range": "Under $500", "count": 89}],
        "retailers": [{"name": "Amazon", "count": 250}]
    },
    "execution_time_ms": 45,
    "timestamp": "2024-01-15T10:30:00Z"
}
```

#### 2. Semantic Search
**Endpoint:** `POST /search/semantic`

Uses CLIP embeddings and pgvector for semantic similarity search.

**Implementation:**
```python
# Query to CLIP embedding
query_embedding = model.encode(request.query, convert_to_tensor=True)

# PostgreSQL pgvector similarity search
SELECT
    id, title, price, rating, reviews_count, image_url, retailer,
    1 - (embedding <-> $1::vector) as similarity
FROM product_embeddings
WHERE 1 - (embedding <-> $1::vector) > $2
ORDER BY embedding <-> $1::vector ASC
LIMIT $3
```

**Features:**
- CLIP model: `clip-ViT-B-32`
- Vector dimension: 512
- Similarity threshold: 0.5 (default, configurable)
- Semantic understanding of queries
- Works across languages
- Returns similarity scores

**Request:**
```json
{
    "query": "portable computing device for work",
    "threshold": 0.5,
    "limit": 20
}
```

**Response:**
```json
{
    "query": "portable computing device for work",
    "type": "semantic",
    "results": [
        {
            "product_id": "p123",
            "title": "XPS 13 Laptop",
            "relevance_score": 0.92
        }
    ],
    "execution_time_ms": 156
}
```

#### 3. Hybrid Search
**Endpoint:** `POST /search/hybrid`

Combines full-text and semantic search using Reciprocal Rank Fusion (RRF).

**Implementation:**
```python
# Parallel execution
text_results, semantic_results = await asyncio.gather(
    full_text_search(query),
    semantic_search(query)
)

# RRF Fusion: 1 / (60 + rank)
fused_scores = {}
for rank, result in enumerate(text_results):
    fused_scores[result.id] = 1 / (60 + rank + 1)

for rank, result in enumerate(semantic_results):
    if result.id in fused_scores:
        fused_scores[result.id] += 1 / (60 + rank + 1)
    else:
        fused_scores[result.id] = 1 / (60 + rank + 1)

# Sort by combined score
ranked = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
```

**Benefits:**
- Best results from both methods
- Avoids duplicate results
- Adaptive ranking
- More comprehensive coverage

#### 4. Image Search
**Endpoint:** `POST /search/image`

Searches using visual similarity via CLIP image embeddings.

**Implementation:**
```python
# Load and encode image
image = Image.open(BytesIO(requests.get(image_url).content))
image_embedding = model.encode(image, convert_to_tensor=True)

# Vector similarity search on image_embedding column
SELECT
    id, title, price, image_url,
    1 - (image_embedding <-> $1::vector) as visual_similarity
FROM product_embeddings
WHERE 1 - (image_embedding <-> $1::vector) > $2
ORDER BY image_embedding <-> $1::vector ASC
```

**Features:**
- Multi-modal search (cross-modal: image to text)
- Product photography matching
- Visual similarity discovery
- Threshold: 0.7 (default)

---

## Advanced Features

### Search History
**Endpoints:**
- `POST /search/history/add` - Add search to history
- `GET /search/history/{user_id}` - Get user's search history

**Implementation:**
- Redis List: `search_history:{user_id}`
- Max 100 searches per user
- TTL: 30 days
- JSON serialization with timestamp

**Data Structure:**
```json
{
    "query": "laptop",
    "search_type": "full-text",
    "result_count": 342,
    "timestamp": "2024-01-15T10:30:00Z"
}
```

### Trending Searches
**Endpoints:**
- `GET /search/trending` - Get top trending queries
- `POST /search/trending/update` - Update trending counter

**Implementation:**
- Redis Sorted Set: `trending_searches`
- Incremental counter: `ZINCRBY`
- TTL: 7 days
- Zset with scores (counts)

**Response:**
```json
{
    "trending": [
        {"query": "macbook pro", "searches": 1240},
        {"query": "gaming laptop", "searches": 980}
    ]
}
```

### Faceted Search
**Endpoint:** `GET /search/facets`

Generates facets for advanced filtering UI.

**Implementation:**
```sql
-- Categories with counts
SELECT category, COUNT(*) as count
FROM products
GROUP BY category
ORDER BY count DESC;

-- Price ranges
SELECT
    CASE
        WHEN price < 100 THEN 'Under $100'
        WHEN price < 500 THEN '$100-$500'
        WHEN price < 1000 THEN '$500-$1000'
        ELSE 'Over $1000'
    END as range,
    COUNT(*) as count
FROM products
GROUP BY range;

-- Retailers with counts
SELECT retailer, COUNT(*) as count
FROM products
GROUP BY retailer
ORDER BY count DESC;
```

**Response:**
```json
{
    "facets": {
        "categories": [
            {"name": "Laptops", "count": 1200},
            {"name": "Desktops", "count": 850}
        ],
        "price_ranges": [
            {"range": "Under $100", "count": 340},
            {"range": "$100-$500", "count": 520}
        ],
        "retailers": [
            {"name": "Amazon", "count": 2150},
            {"name": "Best Buy", "count": 1890}
        ]
    }
}
```

### Autocomplete
**Endpoint:** `GET /search/autocomplete?q=query`

Provides real-time search suggestions.

**Implementation:**
- Prefix matching on product titles: `LOWER(title) LIKE $1`
- Trending term inclusion
- Top 10 results
- Min 2-character query

**Response:**
```json
{
    "suggestions": [
        "macbook pro 16 inch",
        "macbook pro 14 inch",
        "macbook pro m2"
    ]
}
```

---

## Database Schema

### Products Table
```sql
CREATE TABLE products (
    id UUID PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2),
    rating DECIMAL(3, 2),
    reviews_count INT DEFAULT 0,
    image_url VARCHAR(500),
    retailer VARCHAR(100),
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Full-text search index
CREATE INDEX idx_products_fts ON products
    USING GIN(to_tsvector('english', title || ' ' || description));
```

### Product Embeddings Table (pgvector)
```sql
CREATE TABLE product_embeddings (
    id UUID PRIMARY KEY REFERENCES products(id),
    embedding vector(512),  -- CLIP ViT-B-32 dimension
    image_embedding vector(512),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Vector similarity index (HNSW)
CREATE INDEX idx_embeddings_hnsw ON product_embeddings
    USING hnsw (embedding vector_cosine_ops);

CREATE INDEX idx_image_embeddings_hnsw ON product_embeddings
    USING hnsw (image_embedding vector_cosine_ops);
```

---

## Performance Considerations

### Query Optimization
1. **Full-Text Search:** ~45ms avg response time
   - PostgreSQL FTS is highly optimized
   - GIN index on tsvector
   - Most common search type

2. **Semantic Search:** ~150ms avg response time
   - CLIP encoding: ~100ms
   - pgvector similarity: ~50ms
   - More expensive due to ML encoding

3. **Hybrid Search:** ~200ms avg response time
   - Parallel execution of both methods
   - Combined ranking
   - Best coverage

4. **Image Search:** ~300ms avg response time
   - Image download + processing
   - CLIP encoding
   - Vector similarity

### Caching Strategy
- Search history: Redis (instant retrieval)
- Trending searches: Redis sorted set (real-time updates)
- Results: Can be cached with TTL (not implemented by default)

### Scaling
- Connection pooling: 5-20 asyncpg connections
- Horizontal scaling: Multiple service instances behind load balancer
- Database: Consider read replicas for semantic search

---

## Integration Points

### With User Service (8011)
- Search history tied to user_id
- Personalized search recommendations based on history
- Trending searches inform recommendation engine

### With Geolocation Service (8012)
- Regional product filtering
- Retailer availability by region
- Local inventory consideration

### With AI Models (Phase 1)
- CLIP embeddings generation
- Vector storage via pgvector
- Multi-modal search capabilities

---

## Usage Examples

### Python Client
```python
import httpx

# Full-text search
response = httpx.post(
    "http://localhost:8010/search/full-text",
    json={
        "query": "gaming laptop",
        "category": ["Electronics"],
        "price_min": 500,
        "price_max": 2000,
        "sort_by": "rating",
        "limit": 20
    }
)
results = response.json()

# Semantic search
response = httpx.post(
    "http://localhost:8010/search/semantic",
    json={"query": "portable powerful computer"}
)

# Hybrid search
response = httpx.post(
    "http://localhost:8010/search/hybrid",
    json={"query": "gaming laptop under 1500"}
)

# Image search
response = httpx.post(
    "http://localhost:8010/search/image",
    json={"image_url": "https://example.com/laptop.jpg"}
)
```

### JavaScript/Frontend
```javascript
// Full-text search
const response = await fetch('http://localhost:8010/search/full-text', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        query: 'gaming laptop',
        limit: 20,
        sort_by: 'rating'
    })
});

const results = await response.json();
console.log(results.results);  // Array of products
console.log(results.facets);   // Categories, prices, retailers
```

---

## Deployment

### Docker
```bash
# Build image
docker build -f docker/Dockerfile.search-discovery -t search-discovery:1.0 .

# Run container
docker run -p 8010:8010 \
    --env POSTGRES_HOST=postgres \
    --env REDIS_URL=redis://redis:6379/3 \
    search-discovery:1.0
```

### Docker Compose
```bash
# Start all Phase 5.5 services
docker-compose -f docker-compose.phase5-core.yml --profile phase5-core up -d
```

---

## Health Monitoring

**Health Check Endpoint:** `GET /health`

```json
{
    "status": "healthy",
    "service": "search-discovery",
    "timestamp": "2024-01-15T10:30:00Z"
}
```

Checks:
- PostgreSQL database connectivity
- Redis connectivity
- Service responsiveness

---

## Future Enhancements

1. **Faceted Filtering:** Dynamic facet-based drill-down
2. **Search Personalization:** ML-based result ranking per user
3. **Query Expansion:** Synonym handling + typo correction
4. **Result Caching:** Redis caching for popular queries
5. **Analytics:** Search volume + success metrics tracking
6. **Spell Correction:** Auto-correct user typos
7. **Boosting:** Promote new/trending products in results
8. **Custom Weights:** Configurable search field weights
