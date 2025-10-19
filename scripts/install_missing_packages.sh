#!/bin/bash
# Install ALL missing packages that might be needed
# Run this inside the container to avoid rebuilds

echo "🔧 Installing missing packages..."

# Core missing packages we've discovered
pip install --no-cache-dir \
    prophet \
    textblob \
    python-dotenv \
    && echo "✅ Core packages installed"

# Download TextBlob corpora
python -m textblob.download_corpora && echo "✅ TextBlob corpora downloaded"

# Additional packages that might be missing (from comprehensive scan)
pip install --no-cache-dir \
    nltk \
    spacy \
    gensim \
    statsmodels \
    pmdarima \
    holidays \
    && echo "✅ Additional NLP/Time-series packages installed"

# Optional: Install system dependencies for OpenCV if needed
apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && echo "✅ OpenCV system dependencies installed"

echo "🎉 All packages installed successfully!"
