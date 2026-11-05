# 🌾 KisanVani AI — Voice-First Multilingual Agri-Advisory

> **Trusted Agricultural Guidance Grounded in Kisan Call Centre (KCC), ICAR/KVK, and National Agromet Advisory Knowledge Bases**

A complete, runnable hackathon prototype providing verified agricultural advisory in **English**, **हिन्दी (Hindi)**, and **मराठी (Marathi)** strictly grounded in official agricultural datasets and documents.

---

## 🌟 Unified Multi-Source Knowledge Architecture

```
                                  ┌────────────────────────┐
                                  │         FARMER         │
                                  │ (English/Hindi/Marathi)│
                                  └───────────┬────────────┘
                                              ↓
                                  ┌────────────────────────┐
                                  │  WhatsApp Voice UI     │
                                  │  (Streamlit / FastAPI) │
                                  └───────────┬────────────┘
                                              ↓
                                  ┌────────────────────────┐
                                  │     FastAPI Backend    │
                                  │     (/voice, /ask)     │
                                  └───────────┬────────────┘
                                              ↓
                                  ┌────────────────────────┐
                                  │  Whisper STT / Lang    │
                                  │   Query Processing     │
                                  └───────────┬────────────┘
                                              ↓
                                  ┌────────────────────────┐
                                  │  Unified RAG Search    │
                                  │ (13,098 FAISS Chunks)  │
                                  └───────────┬────────────┘
                                              │
         ┌────────────────────────────────────┼────────────────────────────────────┐
         ↓                                    ↓                                    ↓
┌──────────────────┐               ┌──────────────────────┐             ┌─────────────────────┐
│ Kisan Call Centre│               │   ICAR/KVK Advisory  │             │   National Agromet  │
│ (10,000 Records) │               │(2,955 Chunks, 310 Pgs)│             │ (143 Chunks, 22 Pgs)│
└────────┬─────────┘               └──────────┬───────────┘             └──────────┬──────────┘
         └────────────────────────────────────┼────────────────────────────────────┘
                                              ↓
                                  ┌────────────────────────┐
                                  │   Grounded AI Engine   │
                                  │ (Gemini 3.6 / Synthes.)│
                                  └───────────┬────────────┘
                                              ↓
                                  ┌────────────────────────┐
                                  │ Text-to-Speech (gTTS)  │
                                  │ + Source Citation      │
                                  └───────────┬────────────┘
                                              ↓
                                  ┌────────────────────────┐
                                  │ Native Voice Note      │
                                  │ Delivered to Farmer    │
                                  └────────────────────────┘
```

---

## 📁 Knowledge Base Sources & Statistics

| Source Type | Document / File | Chunks / Records | Coverage |
| :--- | :--- | :--- | :--- |
| **Kisan Call Centre** | `data/original/kcc_dataset.csv` | **10,000 records** | Pests, chemical sprays, disease remedies, fertilizer doses |
| **ICAR / KVK Advisory** | `data/ICAR En-Kharif Agro-Advisories for Farmers 2025.pdf` | **2,955 chunks** (310 pages) | Kharif crop agronomy, sowing dates, seed rates, irrigation, fertilizer management |
| **National Agromet Bulletin** | `data/Natioanl_Bulletin_2026-08-21.pdf` | **143 chunks** (22 pages) | State & district rainfall advisories, weather-based crop measures |
| **Total Knowledge Store** | **Unified FAISS Vector Index** | **13,098 chunks** | Multilingual semantic search across EN, HI, MR |

---

## 📁 Project Directory Layout

```
KisanVani-AI/
│
├── data/
│   ├── original/
│   │   └── kcc_dataset.csv                      # Uploaded KCC dataset (untouched)
│   ├── ICAR En-Kharif Agro-Advisories 2025.pdf  # Uploaded ICAR Kharif Advisory PDF
│   ├── Natioanl_Bulletin_2026-08-21.pdf         # Uploaded IMD/Agromet Bulletin PDF
│   ├── processed/
│   │   ├── kcc_cleaned.csv                      # Enriched clean KCC records
│   │   └── kcc_cleaned.jsonl
│   ├── vectorstore/
│   │   └── kcc_faiss_index/                     # 13,098 unified FAISS vectors
│   └── audio/
│       ├── input/                               # Incoming farmer voice notes
│       └── output/                              # Generated advisory voice notes
│
├── backend/
│   ├── main.py                                  # FastAPI app (/voice, /ask, /health, /status)
│   ├── rag.py                                   # Multi-source FAISS retrieval & scoring
│   ├── data_loader.py                           # PDF extractor, chunker & metadata tagging
│   ├── language.py                              # Multilingual detection & safety fallbacks
│   ├── voice.py                                 # Whisper STT & gTTS audio synthesis
│   ├── llm.py                                   # Grounded Gemini 3.6 Flash / Extractive reasoning
│   └── config.py                                # System configurations
│
├── frontend/
│   └── app.py                                   # WhatsApp mobile chat UI (Light/Dark mode)
│
├── scripts/
│   ├── build_index.py                           # Multi-source automated vector index builder
│   ├── inspect_data.py                          # Dataset inspection script
│   └── verify_multi_source.py                   # Multi-source retrieval validation test
│
├── tests/
│   └── test_kcc_system.py                       # 11 automated pytest test suites (100% pass)
│
├── run.sh                                       # Single command launcher (Mac/Linux)
├── run.bat                                      # Single command launcher (Windows)
└── README.md
```

---

## 🚀 Execution Guide

### STEP 1 — Install Dependencies
```bash
python -m venv backend/venv
source backend/venv/bin/activate    # On Windows: backend\venv\Scripts\activate
pip install -r requirements.txt
```

### STEP 2 — Index Unified Knowledge Base (KCC + All Discovered PDFs)
```bash
python scripts/build_index.py
```
**Output:**
```
======================================================================
🎉 Knowledge Base Indexing Complete
======================================================================
KCC Records:                  10,000
PDF 1 (ICAR Kharif Advisory) Chunks: 2,955
PDF 2 (National Agromet Bulletin) Chunks: 143
Total Knowledge Chunks:       13,098

Sources:
✓ Kisan Call Centre
✓ ICAR/KVK Advisory
✓ National Agromet Bulletin
======================================================================
```

### STEP 3 — Run One-Command Startup
```bash
./run.sh
```
*(On Windows: `run.bat`)*

Or manually:
```bash
# Terminal 1: Backend
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Frontend
streamlit run frontend/app.py --server.port 8501
```
Open `http://localhost:8501`.

---

## 🧪 Automated Test Verification

Run all 11 unit and integration tests:
```bash
pytest tests/test_kcc_system.py -v
```

---

## 💡 Demo Scenarios (For Judges)

1. **ICAR PDF Advisory (English)**:
   - *Query*: `"What is the recommended sowing time and fertilizer dose for soybean in kharif season according to ICAR?"`
   - *Retrieved Source*: **ICAR/KVK Advisory (Page 236 • ICAR En-Kharif Agro-Advisories 2025.pdf)**
   - *Advisory*: Sowing by June 15 with irrigation or onset of monsoon, 20 kg N, 40 kg P2O5, 40 kg K2O/ha.
2. **KCC Advisory (Marathi)**:
   - *Query*: `"कापसावरील गुलाबी बोंड अळीचे नियंत्रण कसे करावे?"`
   - *Retrieved Source*: **Kisan Call Centre**
   - *Advisory*: Monocrotophos + lime smearing and pheromone trap recommendations.
3. **Agromet Bulletin Advisory (Hindi / English)**:
   - *Query*: `"National Agromet Advisory Bulletin weather forecast and rainfall advisory"`
   - *Retrieved Source*: **National Agromet Bulletin / IMD**
4. **Out-of-Domain Safety Refusal**:
   - *Query*: `"How to construct a quantum teleportation logic gate with topological qubits?"`
   - *Result*: Low confidence refusal: *"Verified information for this question was not found in the agricultural advisory knowledge base."*
