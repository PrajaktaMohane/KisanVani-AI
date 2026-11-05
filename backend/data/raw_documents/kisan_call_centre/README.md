# Kisan Call Centre (KCC) Query-Answer Dataset

## Source Information
- **Dataset / Source Name**: Kisan Call Centre (KCC) Farmers' Query-Answer Repository
- **Official Source**: [Government of India Open Data Portal (data.gov.in)](https://data.gov.in/keywords/kisan-call-center) / Department of Agriculture & Farmers Welfare (DA&FW)
- **Status**: Sample farmer transcripts loaded locally. Full historical archive (~millions of records) **REQUIRES MANUAL DOWNLOAD** from data.gov.in.

## Purpose
- Captures authentic conversational language patterns used by Indian farmers when speaking to agricultural call officers.
- Used for evaluating Whisper STT accuracy, regional query understanding, and benchmarking RAG retrieval.

## Expected File Format
- CSV / JSON / TXT containing: `QueryText`, `KisanCallCentreAnswer`, `StateName`, `DistrictName`, `CropName`, `Sector`, `Category`, `CreatedOn`.

## Manual Download Instructions
1. Visit https://data.gov.in and search for "Kisan Call Centre".
2. Download state-wise quarterly CSV archives (e.g. Maharashtra, Uttar Pradesh, Punjab).
3. Place exported CSV/TXT files in this directory (`backend/data/raw_documents/kisan_call_centre/`).
4. Run `python -m app.rag.ingest` to re-index.
