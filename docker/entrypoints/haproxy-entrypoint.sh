#!/bin/bash
set -e

echo "🔀 Starting HAProxy Ingress Controller..."

# Get environment variables with defaults
export HAPROXY_PORT=${HAPROXY_PORT:-80}
export HAPROXY_STATS_PORT=${HAPROXY_STATS_PORT:-8404}
export HAPROXY_ADMIN_USER=${HAPROXY_ADMIN_USER:-admin}
export HAPROXY_ADMIN_PASSWORD=${HAPROXY_ADMIN_PASSWORD:-admin}

echo "📝 Configuration:"
echo "   - HTTP Port: $HAPROXY_PORT"
echo "   - Stats Port: $HAPROXY_STATS_PORT"
echo "   - Admin User: $HAPROXY_ADMIN_USER"

# Generate HAProxy config from template
if [ -f /etc/haproxy/haproxy.cfg.template ]; then
    echo "📄 Generating HAProxy configuration..."
    envsubst < /etc/haproxy/haproxy.cfg.template > /etc/haproxy/haproxy.cfg
    echo "✅ Configuration generated"
else
    echo "⚠️  No template found, using existing config"
fi

# Validate configuration
echo "🔍 Validating HAProxy configuration..."
haproxy -c -f /etc/haproxy/haproxy.cfg

# Start HAProxy
echo "✅ Starting HAProxy..."
exec haproxy -f /etc/haproxy/haproxy.cfg
