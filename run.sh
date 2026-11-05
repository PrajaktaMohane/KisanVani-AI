#!/usr/bin/env bash
# ==============================================================================
# KisanVani AI — One-Command Startup Script (Mac / Linux)
# ==============================================================================

set -e

echo "======================================================================"
echo "🌾 Starting KisanVani Voice-First Multilingual Agri-Advisory System"
echo "======================================================================"

# 1. Check Python Virtual Environment
if [ -d "backend/venv" ]; then
    echo "✓ Found virtual environment in backend/venv"
    PYTHON_CMD="backend/venv/bin/python"
    UVICORN_CMD="backend/venv/bin/uvicorn"
    STREAMLIT_CMD="backend/venv/bin/streamlit"
else
    echo "✓ Using system python3"
    PYTHON_CMD="python3"
    UVICORN_CMD="uvicorn"
    STREAMLIT_CMD="streamlit"
fi

# 2. Check Dataset
if [ ! -f "data/original/kcc_dataset.csv" ] && [ ! -f "data/kcc_dataset.csv" ]; then
    echo "✗ Error: Kisan Call Centre dataset not found in data/original/kcc_dataset.csv!"
    exit 1
fi
echo "✓ Kisan Call Centre dataset found"

# 3. Check Vector Store
if [ ! -f "data/vectorstore/kcc_faiss_index/index.faiss" ]; then
    echo "⚙️ Vector index not found. Building FAISS index from KCC dataset..."
    $PYTHON_CMD scripts/build_index.py --max-records 10000
fi
echo "✓ FAISS Vector index is ready"

# 4. Start FastAPI Backend in Background
echo "🚀 Starting FastAPI Backend on http://localhost:8000..."
$UVICORN_CMD backend.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Trap to kill backend when frontend exits
trap "echo 'Stopping backend...'; kill $BACKEND_PID" EXIT

# Wait for backend to be ready
echo "Waiting for backend health check..."
sleep 3

# 5. Start Streamlit Frontend
echo "🌾 Starting WhatsApp-Style Agri-Advisory Frontend on http://localhost:8501..."
$STREAMLIT_CMD run frontend/app.py --server.port 8501
