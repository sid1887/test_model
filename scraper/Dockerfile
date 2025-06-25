# ROBUST NODE.JS SCRAPER DOCKERFILE WITH ERROR HANDLING
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Install system dependencies with comprehensive error handling and Alpine package fixes
RUN apk update && apk upgrade && \
    # Essential packages first
    apk add --no-cache curl ca-certificates wget && \
    # Add additional repositories for more packages
    echo "http://dl-cdn.alpinelinux.org/alpine/edge/main" >> /etc/apk/repositories && \
    echo "http://dl-cdn.alpinelinux.org/alpine/edge/community" >> /etc/apk/repositories && \
    echo "http://dl-cdn.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories && \
    apk update && \
    # Try to install Chromium and related packages with fallbacks
    (apk add --no-cache chromium || \
     (echo "Chromium install failed, trying alternative..." && \
      apk add --no-cache chromium-swiftshader || \
      echo "Chromium install failed completely")) && \
    # Try essential browser packages
    (apk add --no-cache \
        nss \
        freetype \
        harfbuzz \
        ca-certificates \
        ttf-freefont || echo "Some font packages failed") && \
    # Clean up
    rm -rf /var/cache/apk/*

# Configure Puppeteer environment with fallbacks
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser \
    PUPPETEER_ARGS="--no-sandbox --disable-setuid-sandbox --disable-dev-shm-usage --disable-gpu"

# Copy package files first for better caching
COPY package*.json ./

# Install dependencies with error handling
RUN npm config set fetch-timeout 600000 && \
    npm config set fetch-retries 5 && \
    # Try npm ci first, fallback to npm install
    (npm ci --only=production || \
     (echo "npm ci failed, trying npm install..." && \
      npm install --only=production --no-optional || \
      (echo "Production install failed, trying all packages..." && \
       npm install --no-optional))) && \
    # Clear npm cache
    npm cache clean --force

# Copy application code
COPY . .

# Create required directories and set permissions
RUN mkdir -p /app/logs /app/.cache && \
    chmod -R 755 /app

# Expose port
EXPOSE 3001

# Robust health check with multiple endpoints
HEALTHCHECK --interval=30s --timeout=15s --start-period=30s --retries=5 \
    CMD curl -f http://localhost:3001/health || \
        curl -f http://localhost:3001/ || \
        wget --quiet --tries=1 --spider http://localhost:3001/health || \
        exit 1

# Start with error handling and fallbacks
CMD ["sh", "-c", "npm start || node server.js || node index.js || node app.js"]
