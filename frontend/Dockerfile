# Multi-stage build for React Vite app
# Use full node image instead of alpine to avoid SWC compilation issues
FROM node:18 AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies with legacy peer deps and increased memory
RUN npm ci --legacy-peer-deps --maxsockets=1 || \
    (rm -rf node_modules package-lock.json && npm install --legacy-peer-deps)

# Copy source code
COPY . .

# Build the application with increased memory
ENV NODE_OPTIONS="--max-old-space-size=4096"
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]