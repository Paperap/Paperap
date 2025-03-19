#!/bin/bash
set -e

echo "🚀 Setting up Paperap development environment..."

# Install dependencies using uv
echo "📦 Installing dependencies with uv..."
uv pip install -e ".[dev,test,docs]"

# Wait for Paperless-NGX to be ready
echo "⏳ Waiting for Paperless-NGX to be ready..."
timeout=120
elapsed=0
while ! curl -s http://paperless:8000/api/ > /dev/null; do
    sleep 5
    elapsed=$((elapsed + 5))
    if [ "$elapsed" -ge "$timeout" ]; then
        echo "❌ Timed out waiting for Paperless-NGX to start"
        exit 1
    fi
    echo "⏳ Still waiting for Paperless-NGX... ($elapsed seconds elapsed)"
done

# Create API token for integration tests if it doesn't exist
echo "🔑 Setting up API token for integration tests..."
TOKEN_NAME="paperap-dev"
TOKEN_VALUE="paperap-dev-token"

# Check if token exists
TOKEN_EXISTS=$(curl -s -H "Authorization: Basic $(echo -n admin:password | base64)" \
    http://paperless:8000/api/token/ | grep -c "$TOKEN_NAME" || true)

if [ "$TOKEN_EXISTS" -eq 0 ]; then
    echo "🔑 Creating new API token..."
    curl -s -X POST \
        -H "Authorization: Basic $(echo -n admin:password | base64)" \
        -H "Content-Type: application/json" \
        -d "{\"name\":\"$TOKEN_NAME\",\"token\":\"$TOKEN_VALUE\"}" \
        http://paperless:8000/api/token/ > /dev/null
    echo "✅ API token created"
else
    echo "✅ API token already exists"
fi

# Create a .env file for local development
echo "📝 Creating .env file for local development..."
cat > .env << EOF
PAPERLESS_URL=http://localhost:8010
PAPERLESS_TOKEN=$TOKEN_VALUE
EOF

echo "✅ Development environment setup complete!"
echo "🌐 Paperless-NGX is available at: http://localhost:8010"
echo "👤 Username: admin"
echo "🔑 Password: password"
echo "🔄 API Token: $TOKEN_VALUE"
