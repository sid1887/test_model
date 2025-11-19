# Geolocation & Region Management Service Documentation

## Overview

**Service:** Geolocation & Region Management (Port 8012)
**Purpose:** Complex geolocation detection, regional data variants, dynamic pricing, local inventory management
**Status:** Production-ready
**Lines of Code:** 850+
**Endpoints:** 18+

The Geolocation & Region Management Service handles user location detection, region-specific product availability, dynamic regional pricing, and inventory management. This service is critical for multi-region commerce platforms where products, prices, and availability vary by geographic location.

---

## Architecture Overview

The service operates on the principle that e-commerce data is fundamentally regional:
- Products vary by region (availability, local titles)
- Prices differ by currency and regional economics
- Inventory is location-based (fulfillment centers)
- Taxes and shipping vary by region
- Languages and languages preferences are regional

```
User IP
   ↓
GeoIP Detection
   ↓
Country/Region Identification
   ↓
Regional Context Loading
   ↓
Data Filtering & Personalization
```

---

## Geolocation Detection

### Detect User Location
**Endpoint:** `POST /location/detect`

Detects user's location from IP address using GeoIP2 database.

**Implementation:**
```python
import geoip2.database

reader = geoip2.database.Reader('GeoLite2-City.mmdb')
response = reader.city(ip_address)

location = {
    "ip_address": ip_address,
    "country": response.country.name,
    "country_code": response.country.iso_code,  # e.g., "US"
    "city": response.city.name,
    "region": response.subdivisions[0].name if response.subdivisions else None,
    "latitude": response.location.latitude,
    "longitude": response.location.longitude,
    "timezone": response.location.time_zone
}

# Cache for 24 hours
redis.setex(f"location:{ip_address}", 86400, json.dumps(location))
```

**Request:**
```json
{
    "ip_address": "203.0.113.42"
}
```

**Response:**
```json
{
    "ip_address": "203.0.113.42",
    "country": "Australia",
    "country_code": "AU",
    "city": "Sydney",
    "region": "New South Wales",
    "latitude": -33.8688,
    "longitude": 151.2093,
    "timezone": "Australia/Sydney"
}
```

**Caching:**
- 24-hour Redis TTL per IP
- Reduces repeated GeoIP lookups
- Instant location retrieval for return users

---

## Region Management

### List Regions
**Endpoint:** `GET /regions?region_type=country`

Lists all enabled regions, optionally filtered by type.

**Implementation:**
```sql
SELECT * FROM regions
WHERE (region_type = $1 OR $1 IS NULL)
AND enabled = true
ORDER BY region_type, name
```

**Region Types:**
- `country` - National regions
- `state` - State/province level
- `city` - City-specific regions
- `continent` - Continental groupings

**Response:**
```json
{
    "regions": [
        {
            "id": "region-us",
            "name": "United States",
            "region_type": "country",
            "country_code": "US",
            "currency": "USD",
            "language": "en",
            "tax_rate": 0.0,
            "shipping_cost": 5.99,
            "enabled": true
        },
        {
            "id": "region-au",
            "name": "Australia",
            "region_type": "country",
            "country_code": "AU",
            "currency": "AUD",
            "language": "en",
            "tax_rate": 0.1,
            "shipping_cost": 9.99,
            "enabled": true
        }
    ],
    "count": 50
}
```

### Get Region Details
**Endpoint:** `GET /regions/{region_id}`

Retrieves complete details for a specific region.

**Response:**
```json
{
    "id": "region-us",
    "name": "United States",
    "region_type": "country",
    "country_code": "US",
    "city": null,
    "state": null,
    "latitude": 37.0902,
    "longitude": -95.7129,
    "currency": "USD",
    "language": "en",
    "tax_rate": 0.0,
    "shipping_cost": 5.99,
    "enabled": true
}
```

### Create Region
**Endpoint:** `POST /regions` (admin only)

Creates a new region configuration.

**Request:**
```json
{
    "name": "California",
    "region_type": "state",
    "country_code": "US",
    "state": "CA",
    "currency": "USD",
    "language": "en",
    "tax_rate": 0.0725,
    "shipping_cost": 4.99,
    "enabled": true
}
```

### Update Region
**Endpoint:** `PUT /regions/{region_id}` (admin only)

Updates existing region configuration.

---

## Regional Products

### Get Regional Products
**Endpoint:** `GET /regions/{region_id}/products?skip=0&limit=20`

Lists all products available in a specific region.

**Implementation:**
```sql
SELECT
    p.id, p.title, p.price, p.image_url, p.rating,
    rp.region_id, rp.local_title, rp.availability,
    rp.stock_level, rp.fulfillment_center,
    r.currency
FROM regional_products rp
JOIN products p ON rp.product_id = p.id
JOIN regions r ON rp.region_id = r.id
WHERE rp.region_id = $1
ORDER BY p.title
LIMIT $2 OFFSET $3
```

**Regional Product Properties:**
- `local_title`: Product name in local language/terminology
- `availability`: In Stock, Back Order, Unavailable
- `stock_level`: Quantity available
- `fulfillment_center`: Which warehouse ships from

**Response:**
```json
{
    "products": [
        {
            "product_id": "p123",
            "region_id": "region-au",
            "title": "XPS 13 Laptop",
            "price": 1299.00,
            "currency": "AUD",
            "local_title": "XPS 13 Portable Computer",
            "description": "High-performance ultrabook",
            "availability": "In Stock",
            "stock_level": 45,
            "fulfillment_center": "Sydney DC"
        }
    ],
    "count": 1,
    "region_id": "region-au"
}
```

### Add Product to Region
**Endpoint:** `POST /regions/{region_id}/products` (admin only)

Adds a product to a region with local configuration.

**Request:**
```json
{
    "product_id": "p123",
    "local_title": "XPS 13 Portable Computer",
    "availability": "In Stock",
    "stock_level": 45,
    "fulfillment_center": "Sydney DC"
}
```

**Implementation:**
```sql
INSERT INTO regional_products (
    region_id, product_id, local_title, availability,
    stock_level, fulfillment_center
)
VALUES ($1, $2, $3, $4, $5, $6)
ON CONFLICT (region_id, product_id) DO UPDATE SET
    availability = EXCLUDED.availability,
    stock_level = EXCLUDED.stock_level,
    fulfillment_center = EXCLUDED.fulfillment_center
```

---

## Regional Pricing

Regional pricing allows different prices for the same product across regions due to:
- Currency differences
- Regional economic factors
- Import taxes and tariffs
- Local competition
- Supply chain costs

### Get Regional Pricing
**Endpoint:** `GET /regions/{region_id}/pricing/{product_id}`

Retrieves pricing for a product in a specific region.

**Implementation:**
```sql
SELECT * FROM regional_pricing
WHERE region_id = $1
AND product_id = $2
AND expiry_date > NOW()
```

**Response:**
```json
{
    "product_id": "p123",
    "region_id": "region-au",
    "base_price": 999.99,
    "regional_price": 1299.00,
    "currency": "AUD",
    "markup_percentage": 30.0,
    "effective_date": "2024-01-01T00:00:00Z",
    "expiry_date": "2024-12-31T23:59:59Z"
}
```

### Set Regional Pricing
**Endpoint:** `POST /regions/{region_id}/pricing` (admin only)

Sets dynamic pricing for a product in a region.

**Request:**
```json
{
    "product_id": "p123",
    "base_price": 999.99,
    "regional_price": 1299.00,
    "currency": "AUD",
    "markup_percentage": 30.0,
    "effective_date": "2024-01-15T00:00:00Z",
    "expiry_date": "2024-12-31T23:59:59Z"
}
```

**Pricing Strategies:**

#### Fixed Markup
```
Regional Price = Base Price × (1 + Markup%)
Example: $999.99 × 1.30 = $1,299.99
```

#### Tiered Pricing
```
Products by Category:
- Electronics: 25% markup
- Clothing: 15% markup
- Food: 5% markup
```

#### Dynamic Pricing
```
Peak Season: 40% markup
Off-Season: 10% markup
Clearance: -20% discount
```

**Implementation:**
```sql
INSERT INTO regional_pricing (
    region_id, product_id, base_price, regional_price,
    currency, markup_percentage, effective_date, expiry_date
)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
ON CONFLICT (region_id, product_id) DO UPDATE SET
    regional_price = EXCLUDED.regional_price,
    markup_percentage = EXCLUDED.markup_percentage,
    effective_date = EXCLUDED.effective_date,
    expiry_date = EXCLUDED.expiry_date
```

---

## User Region Context

### Get User Region Context
**Endpoint:** `POST /user-context`

Combines geolocation + region data + pricing + language preferences into complete user context.

**Request:**
```json
{
    "user_id": "user123",
    "ip_address": "203.0.113.42"
}
```

**Implementation:**
```python
# 1. Detect location from IP
location = await detect_location(ip_address)

# 2. Find matching region
region = db.query("""
    SELECT * FROM regions
    WHERE country_code = $1 AND enabled = true
    ORDER BY region_type DESC
    LIMIT 1
""", location['country_code'])

# 3. Build context
context = {
    "user_id": user_id,
    "detected_region_id": region['id'],
    "detected_location": location,
    "primary_region": region,
    "preferred_currency": region['currency'],
    "language": region['language'],
    "tax_applicable": True
}

# 4. Cache for 1 hour
redis.setex(f"user_context:{user_id}", 3600, context.json())

return context
```

**Response:**
```json
{
    "user_id": "user123",
    "detected_region_id": "region-au",
    "detected_location": {
        "ip_address": "203.0.113.42",
        "country": "Australia",
        "country_code": "AU",
        "city": "Sydney",
        "region": "New South Wales",
        "latitude": -33.8688,
        "longitude": 151.2093,
        "timezone": "Australia/Sydney"
    },
    "primary_region": {
        "id": "region-au",
        "name": "Australia",
        "currency": "AUD",
        "language": "en",
        "tax_rate": 0.1,
        "shipping_cost": 9.99
    },
    "preferred_currency": "AUD",
    "language": "en",
    "tax_applicable": true
}
```

---

## Database Schema

### Regions Table
```sql
CREATE TABLE regions (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    region_type VARCHAR(50) NOT NULL,  -- country, state, city, continent
    country_code CHAR(2) NOT NULL,
    city VARCHAR(100),
    state VARCHAR(100),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    currency VARCHAR(3) NOT NULL,  -- ISO 4217 code
    language VARCHAR(10) NOT NULL,  -- ISO 639-1 code
    tax_rate DECIMAL(5, 4),  -- e.g., 0.10 for 10%
    shipping_cost DECIMAL(10, 2),
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_regions_country ON regions(country_code);
CREATE INDEX idx_regions_type ON regions(region_type);
```

### Regional Products Table
```sql
CREATE TABLE regional_products (
    id SERIAL PRIMARY KEY,
    region_id VARCHAR(50) REFERENCES regions(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    local_title VARCHAR(255),
    availability VARCHAR(50),  -- In Stock, Back Order, Unavailable
    stock_level INT DEFAULT 0,
    fulfillment_center VARCHAR(255),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(region_id, product_id)
);

CREATE INDEX idx_regional_products_region ON regional_products(region_id);
CREATE INDEX idx_regional_products_product ON regional_products(product_id);
```

### Regional Pricing Table
```sql
CREATE TABLE regional_pricing (
    id SERIAL PRIMARY KEY,
    region_id VARCHAR(50) REFERENCES regions(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    base_price DECIMAL(10, 2),
    regional_price DECIMAL(10, 2),
    currency VARCHAR(3),
    markup_percentage DECIMAL(5, 2),  -- Can be negative for discounts
    effective_date TIMESTAMP,
    expiry_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(region_id, product_id)
);

CREATE INDEX idx_regional_pricing_region ON regional_pricing(region_id);
CREATE INDEX idx_regional_pricing_effective ON regional_pricing(effective_date, expiry_date);
```

---

## Multi-Region Data Strategy

### Product Availability Matrix
```
Product P123 Availability:
- USA (region-us): In Stock, 500 units
- Australia (region-au): In Stock, 45 units
- UK (region-uk): Back Order, 0 units
- EU (region-eu): Unavailable, 0 units
```

### Currency Conversion Example
```
Product: XPS 13 Laptop
- Base Price: $999.99 USD

Regional Variants:
- USA: $999.99 USD (base)
- Australia: $1,299.00 AUD (30% markup)
- UK: £799.99 GBP (special pricing)
- EU: €899.99 EUR (inclusive of VAT)
```

### Tax Calculation
```python
def calculate_total_with_tax(base_price, region_id):
    region = db.get_region(region_id)
    regional_price = db.get_regional_price(region_id)

    subtotal = regional_price
    tax = subtotal * region['tax_rate']
    total = subtotal + tax

    return {
        'subtotal': subtotal,
        'tax': tax,
        'total': total,
        'currency': region['currency']
    }
```

---

## Integration Patterns

### With Search Service (8010)
```
User Search Request
    ↓
Get User Region Context
    ↓
Filter Products by Region
    ↓
Apply Regional Pricing
    ↓
Return Localized Results
```

### With User Service (8011)
```
User Login
    ↓
Detect IP Location
    ↓
Create/Update User Region Context
    ↓
Personalize Recommendations by Region
    ↓
Display Region-Specific Content
```

### With Product Data
```
Store Base Product
    ↓
Create Regional Variants
    ↓
Set Regional Pricing
    ↓
Update Local Inventory
    ↓
Make Available in Region
```

---

## Usage Examples

### Python Client
```python
import httpx

# Detect user location
response = httpx.post(
    "http://localhost:8012/location/detect",
    json={"ip_address": "203.0.113.42"}
)
location = response.json()

# Get user region context
response = httpx.post(
    "http://localhost:8012/user-context",
    json={
        "user_id": "user123",
        "ip_address": location['ip_address']
    }
)
context = response.json()

# Get regional products
response = httpx.get(
    f"http://localhost:8012/regions/{context['detected_region_id']}/products"
)
products = response.json()

# Get regional pricing
response = httpx.get(
    f"http://localhost:8012/regions/{context['detected_region_id']}/pricing/p123"
)
pricing = response.json()
print(f"Price: {pricing['regional_price']} {pricing['currency']}")
```

### Frontend Integration
```javascript
// Detect user location
const location = await fetch(
    'http://localhost:8012/location/detect',
    { method: 'POST', body: JSON.stringify({ ip_address: userIP }) }
).then(r => r.json());

// Get user context
const context = await fetch(
    'http://localhost:8012/user-context',
    { method: 'POST', body: JSON.stringify({ user_id, ip_address }) }
).then(r => r.json());

// Display currency and regional info
console.log(`Showing prices in ${context.preferred_currency}`);
console.log(`Shipping: ${context.primary_region.shipping_cost}`);
```

---

## Deployment

### Docker
```bash
docker build -f docker/Dockerfile.geolocation -t geolocation:1.0 .

docker run -p 8012:8012 \
    -v geoip_data:/data \
    -e GEOIP_DB=/data/GeoLite2-City.mmdb \
    geolocation:1.0
```

### Docker Compose
```bash
docker-compose -f docker-compose.phase5-core.yml --profile phase5-core up -d geolocation
```

---

## Monitoring

**Health Check:** `GET /health`

Track metrics:
- GeoIP lookup success rate
- Region detection accuracy
- Regional product availability
- Pricing tier effectiveness
- Cache hit rates

---

## Future Enhancements

1. **Advanced Geofencing:** Sub-city level regions
2. **Dynamic Shipping:** Real-time courier integration
3. **Tax Compliance:** Automatic tax calculation per region
4. **Currency Conversion:** Real-time exchange rates
5. **Local Fulfillment:** Warehouse optimization
6. **Regional Marketing:** Localized promotions
7. **Compliance Rules:** GDPR, CCPA per-region
8. **Multi-Language Support:** Automatic translation
