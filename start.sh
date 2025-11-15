#!/bin/bash

# Podcast Analyzer Startup Script

echo "🎙️  Starting Podcast Analyzer..."
echo ""

# Check if requirements are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -q -r requirements.txt --break-system-packages
fi

echo "✅ Dependencies ready"
echo "🚀 Starting server on http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
python app.py
