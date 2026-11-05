@echo off
REM ==============================================================================
REM KisanVani AI — One-Command Startup Script (Windows)
REM ==============================================================================

echo ======================================================================
echo Starting KisanVani Voice-First Multilingual Agri-Advisory System
echo ======================================================================

REM Check Dataset
if not exist "data\original\kcc_dataset.csv" (
    if not exist "data\kcc_dataset.csv" (
        echo Error: KCC dataset not found in data\original\kcc_dataset.csv!
        pause
        exit /b 1
    )
)
echo [OK] Kisan Call Centre dataset found

REM Check Vector Store
if not exist "data\vectorstore\kcc_faiss_index\index.faiss" (
    echo Building FAISS Vector Index from KCC Dataset...
    python scripts\build_index.py --max-records 10000
)
echo [OK] FAISS Vector index is ready

REM Start Backend and Frontend
echo Starting FastAPI Backend on http://localhost:8000...
start /b uvicorn backend.main:app --host 0.0.0.0 --port 8000

echo Starting Streamlit UI on http://localhost:8501...
streamlit run frontend\app.py --server.port 8501
