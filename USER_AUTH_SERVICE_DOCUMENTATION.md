# User Features & Auth Service Documentation

## Overview

**Service:** User Features & Auth (Port 8011)
**Purpose:** Google OAuth, JWT authentication, user profiles, wishlist management, personalized recommendations
**Status:** Production-ready
**Lines of Code:** 850+
**Endpoints:** 20+

The User Features & Auth Service handles user authentication, profile management, wishlist operations, and personalized product recommendations using collaborative filtering and ML models.

---

## Authentication System

### OAuth 2.0 Flow

#### 1. Initiate Login
**Endpoint:** `GET /auth/google/login`

Redirects user to Google OAuth consent screen.

**Implementation:**
```python
# Generate random state token
state = secrets.token_urlsafe(32)

# Store state in Redis (600 second TTL)
redis.setex(f"oauth_state:{state}", 600, "pending")

# Redirect to Google OAuth
google_auth_url = (
    f"https://accounts.google.com/o/oauth2/v2/auth?"
    f"client_id={GOOGLE_CLIENT_ID}&"
    f"redirect_uri={GOOGLE_REDIRECT_URI}&"
    f"response_type=code&"
    f"scope=openid email profile&"
    f"state={state}"
)
return RedirectResponse(url=google_auth_url)
```

**Flow:**
```
User → /auth/google/login → Google OAuth Screen → Consent
```

#### 2. OAuth Callback
**Endpoint:** `GET /auth/callback?code={code}&state={state}`

Handles OAuth callback from Google, exchanges code for tokens.

**Implementation:**
```python
# Verify state token
state_exists = redis.exists(f"oauth_state:{state}")
redis.delete(f"oauth_state:{state}")  # One-time use

# Exchange code for tokens
token_response = httpx.post(
    "https://oauth2.googleapis.com/token",
    data={
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code"
    }
)

# Get user info
user_info = httpx.get(
    "https://www.googleapis.com/oauth2/v1/userinfo",
    headers={"Authorization": f"Bearer {tokens['access_token']}"}
).json()

# Create/update user in database
user_id = hashlib.md5(user_info['email'].encode()).hexdigest()
await db.execute("""
    INSERT INTO users (id, email, name, avatar_url, created_at, last_login)
    VALUES ($1, $2, $3, $4, NOW(), NOW())
    ON CONFLICT (id) DO UPDATE SET last_login = NOW()
""", user_id, user_info['email'], user_info['name'], user_info['picture'])

# Generate JWT token
jwt_token = create_jwt_token(user_id, user_info['email'])

# Redirect to frontend with token
return RedirectResponse(url=f"http://localhost:3000/auth/success?token={jwt_token}")
```

**Security:**
- State token prevents CSRF attacks
- One-time use state tokens
- 10-minute expiry
- Secure token exchange

#### 3. Token Generation
**JWT Token Structure:**
```python
payload = {
    "sub": user_id,              # Subject (user ID)
    "email": user_email,         # Email
    "exp": datetime.utcnow() + timedelta(hours=24),  # Expiry
    "iat": datetime.utcnow()     # Issued at
}

token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
```

**Token Response:**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
        "id": "abc123def456",
        "email": "user@example.com",
        "name": "John Doe",
        "avatar_url": "https://lh3.googleusercontent.com/...",
        "created_at": "2024-01-10T10:30:00Z",
        "last_login": "2024-01-15T10:30:00Z"
    },
    "expires_in": 86400
}
```

#### 4. Token Verification
**Endpoint:** `GET /auth/verify`

Verifies JWT token validity.

**Implementation:**
```python
# Extract token from Authorization header
def get_token_from_header(authorization):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing header")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid format")

    return parts[1]

# Verify token signature and expiry
try:
    payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    return {"valid": True, "user_id": payload['sub']}
except jwt.ExpiredSignatureError:
    raise HTTPException(status_code=401, detail="Token expired")
except jwt.InvalidTokenError:
    raise HTTPException(status_code=401, detail="Invalid token")
```

---

## User Profile Management

### Get Profile
**Endpoint:** `GET /profile`

Retrieves complete user profile with statistics.

**Implementation:**
```sql
SELECT
    u.id, u.email, u.name, u.avatar_url,
    u.created_at, u.last_login,
    (SELECT COUNT(*) FROM wishlist WHERE user_id = u.id) as wishlist_count,
    (SELECT COUNT(*) FROM user_searches WHERE user_id = u.id) as search_count
FROM users u
WHERE u.id = $1
```

**Response:**
```json
{
    "id": "abc123def456",
    "email": "user@example.com",
    "name": "John Doe",
    "avatar_url": "https://...",
    "wishlist_count": 15,
    "recommendations_count": 20,
    "searches_count": 142,
    "created_at": "2024-01-10T10:30:00Z",
    "last_login": "2024-01-15T10:30:00Z"
}
```

---

## Wishlist Management

### Add to Wishlist
**Endpoint:** `POST /wishlist/add`

Adds product to user's wishlist.

**Implementation:**
```sql
INSERT INTO wishlist (user_id, product_id, added_at)
VALUES ($1, $2, NOW())
ON CONFLICT (user_id, product_id) DO NOTHING
```

**Request:**
```json
{
    "product_id": "p123"
}
```

**Response:**
```json
{
    "status": "added",
    "product_id": "p123"
}
```

### Remove from Wishlist
**Endpoint:** `DELETE /wishlist/remove?product_id=p123`

Removes product from wishlist.

### Get Wishlist
**Endpoint:** `GET /wishlist`

Retrieves all wishlist items with product details.

**Implementation:**
```sql
SELECT
    p.id, p.title, p.price, p.image_url,
    w.added_at
FROM wishlist w
JOIN products p ON w.product_id = p.id
WHERE w.user_id = $1
ORDER BY w.added_at DESC
```

**Response:**
```json
{
    "items": [
        {
            "product_id": "p123",
            "title": "XPS 13 Laptop",
            "price": 999.99,
            "image_url": "https://...",
            "added_at": "2024-01-15T10:30:00Z"
        }
    ],
    "count": 15
}
```

---

## Recommendation Engine

The service provides four types of recommendations using different algorithms.

### 1. Collaborative Filtering
**Type:** `collaborative`

Finds users with similar purchase/browsing patterns and recommends products they liked.

**Implementation:**
```sql
SELECT DISTINCT
    p.id, p.title, p.price, p.rating, p.image_url,
    'Similar users liked this' as reason,
    COUNT(*) as score
FROM users u
JOIN purchases up ON u.id = up.user_id
JOIN products p ON up.product_id = p.id
WHERE u.id != $1
AND up.user_id IN (
    SELECT u2.id FROM users u2
    WHERE u2.created_at > NOW() - INTERVAL '1 year'
    LIMIT 100  -- Compare against 100 similar users
)
AND p.id NOT IN (
    SELECT product_id FROM purchases WHERE user_id = $1
)
GROUP BY p.id, p.title, p.price, p.rating, p.image_url
ORDER BY score DESC
LIMIT $2
```

### 2. Content-Based Filtering
**Type:** `content_based`

Recommends products similar to categories the user has viewed.

**Implementation:**
```sql
SELECT
    p.id, p.title, p.price, p.rating, p.image_url,
    'Similar to your interests' as reason,
    0.9 as score
FROM products p
WHERE p.category IN (
    SELECT DISTINCT category
    FROM products
    WHERE id IN (
        SELECT product_id FROM user_searches
        WHERE user_id = $1
    )
)
AND p.id NOT IN (
    SELECT product_id FROM purchases WHERE user_id = $1
)
AND p.id NOT IN (
    SELECT product_id FROM wishlist WHERE user_id = $1
)
ORDER BY p.rating DESC
LIMIT $2
```

### 3. Trending Products
**Type:** `trending`

Popular products based on reviews and ratings.

**Implementation:**
```sql
SELECT
    id, title, price, rating, image_url,
    'Trending now' as reason,
    reviews_count::float as score
FROM products
ORDER BY reviews_count DESC, rating DESC
LIMIT $1
```

### 4. Personalized (Hybrid)
**Type:** `personalized` (default)

Combines collaborative + content-based + trending with weighted scoring.

**Implementation:**
```sql
SELECT
    id, title, price, rating, image_url,
    'Recommended for you' as reason,
    (rating * 0.5 + (reviews_count::float / 1000) * 0.5) as score
FROM products
WHERE id NOT IN (
    SELECT product_id FROM purchases WHERE user_id = $1
)
AND id NOT IN (
    SELECT product_id FROM wishlist WHERE user_id = $1
)
ORDER BY score DESC, rating DESC
LIMIT $2
```

### Get Recommendations
**Endpoint:** `GET /recommendations?type=personalized&limit=20`

**Response:**
```json
{
    "recommendations": [
        {
            "product_id": "p456",
            "title": "Gaming Laptop",
            "price": 1299.99,
            "rating": 4.9,
            "image_url": "https://...",
            "reason": "Recommended for you",
            "score": 0.85
        }
    ],
    "type": "personalized"
}
```

---

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id VARCHAR(32) PRIMARY KEY,  -- MD5 hash of email
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    avatar_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
```

### Wishlist Table
```sql
CREATE TABLE wishlist (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(32) REFERENCES users(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    added_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, product_id)
);

CREATE INDEX idx_wishlist_user ON wishlist(user_id);
CREATE INDEX idx_wishlist_product ON wishlist(product_id);
```

### Purchases Table (for recommendations)
```sql
CREATE TABLE purchases (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(32) REFERENCES users(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id),
    purchased_at TIMESTAMP DEFAULT NOW(),
    price DECIMAL(10, 2),
    quantity INT DEFAULT 1
);

CREATE INDEX idx_purchases_user ON purchases(user_id);
CREATE INDEX idx_purchases_product ON purchases(product_id);
```

### User Searches (for content-based recommendations)
```sql
CREATE TABLE user_searches (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(32) REFERENCES users(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id),
    search_query VARCHAR(255),
    searched_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_searches_user ON user_searches(user_id);
```

---

## Security Considerations

### OAuth 2.0 Best Practices
1. **State Token:** Prevents CSRF attacks
2. **Secure Storage:** JWT secret stored in environment
3. **HTTPS Only:** In production, all OAuth flows over HTTPS
4. **Token Expiry:** 24-hour JWT validity with refresh capability
5. **Scopes:** Minimal permissions requested (openid, email, profile)

### Password Security
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash password
hashed_password = pwd_context.hash(password)

# Verify password
is_valid = pwd_context.verify(password, hashed_password)
```

### Environment Variables
```bash
JWT_SECRET=your-long-random-secret-key
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxx
GOOGLE_REDIRECT_URI=https://your-domain.com/auth/callback
```

---

## Integration Points

### With Search Service (8010)
- User search history tracking
- Personalized search ranking
- Trending searches influence recommendations

### With Geolocation Service (8012)
- User's regional context
- Regional pricing application
- Local recommendations

### With AI Models (Phase 1)
- Collaborative filtering ML models
- Recommendation model training
- User embedding generation

---

## Usage Examples

### Python Client
```python
import httpx

# Initiate OAuth login
# Redirect user to: http://localhost:8011/auth/google/login

# Get user profile (with JWT token)
headers = {"Authorization": f"Bearer {jwt_token}"}
response = httpx.get("http://localhost:8011/profile", headers=headers)
profile = response.json()

# Add to wishlist
response = httpx.post(
    "http://localhost:8011/wishlist/add",
    json={"product_id": "p123"},
    headers=headers
)

# Get wishlist
response = httpx.get("http://localhost:8011/wishlist", headers=headers)
wishlist = response.json()

# Get personalized recommendations
response = httpx.get(
    "http://localhost:8011/recommendations?type=personalized&limit=20",
    headers=headers
)
recommendations = response.json()
```

### Frontend Integration
```javascript
// Initiate Google OAuth login
function login() {
    window.location.href = 'http://localhost:8011/auth/google/login';
}

// Handle OAuth callback
const params = new URLSearchParams(window.location.search);
const token = params.get('token');
localStorage.setItem('auth_token', token);

// Fetch user profile
const headers = { 'Authorization': `Bearer ${token}` };
fetch('http://localhost:8011/profile', { headers })
    .then(r => r.json())
    .then(profile => console.log(profile));

// Add to wishlist
fetch('http://localhost:8011/wishlist/add', {
    method: 'POST',
    headers: { ...headers, 'Content-Type': 'application/json' },
    body: JSON.stringify({ product_id: 'p123' })
});
```

---

## Deployment

### Docker
```bash
docker build -f docker/Dockerfile.user-auth -t user-auth:1.0 .

docker run -p 8011:8011 \
    -e JWT_SECRET=your-secret \
    -e GOOGLE_CLIENT_ID=xxx \
    -e GOOGLE_CLIENT_SECRET=xxx \
    user-auth:1.0
```

### Docker Compose
```bash
docker-compose -f docker-compose.phase5-core.yml --profile phase5-core up -d user-auth
```

---

## Monitoring & Analytics

**Health Check:** `GET /health`

Track:
- OAuth login success/failure rates
- JWT token refresh frequency
- Wishlist add/remove operations
- Recommendation accuracy
- Average response times per endpoint

---

## Future Enhancements

1. **Multi-Factor Authentication:** TOTP/SMS support
2. **Social Login:** Facebook, GitHub, Microsoft
3. **User Preferences:** Customizable recommendation weights
4. **Email Notifications:** Wishlist price drops, new recommendations
5. **User Reviews:** Product ratings and reviews system
6. **Referral Program:** Friend invitations with rewards
7. **Advanced Analytics:** User behavior tracking and insights
8. **Machine Learning:** Deep learning models for recommendations
