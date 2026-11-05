import os
import re
import csv
import glob
import json
import logging
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter
import pypdf

logger = logging.getLogger(__name__)

# Crop keyword mapping for automatic metadata enrichment
CROP_KEYWORDS = {
    "Mustard": ["mustard", "sarson", "rai", "मोहरी", "सरसों"],
    "Wheat": ["wheat", "gehu", "gehun", "गहू", "गेहूं", "कनक"],
    "Cotton": ["cotton", "kapas", "kapus", "कापूस", "कपास", "बोंड", "बोंडअळी", "bollworm", "pink bollworm", "gossypiella"],
    "Rice / Paddy": ["rice", "paddy", "dhan", "bhat", "धान", "चावल", "भात"],
    "Soybean": ["soybean", "soya", "सोयाबीन", "सोया", "girdle beetle"],
    "Potato": ["potato", "aloo", "alu", "बटाटा", "आलू"],
    "Tomato": ["tomato", "tamatar", "टोमॅटो", "टमाटर"],
    "Onion": ["onion", "pyaz", "kanda", "कांदा", "प्याज"],
    "Coconut": ["coconut", "nariyal", "naral", "नारळ", "नारियल"],
    "Maize / Corn": ["maize", "corn", "makka", "मका", "मक्का"],
    "Mango": ["mango", "aam", "amba", "आंबा", "आम"],
    "Chilli": ["chilli", "chili", "mirch", "mirchi", "मिरची", "मिर्च"],
    "Sugarcane": ["sugarcane", "ganna", "us", "ऊस", "गन्ना"],
    "Gram / Chickpea": ["gram", "chana", "harbara", "हरभरा", "चना", "chickpea"],
    "Groundnut": ["groundnut", "peanut", "moongfali", "bhuimug", "भुईमूग", "मूंगफली"],
    "Citrus / Orange": ["citrus", "orange", "santre", "mosambi", "संत्रा", "संतरा", "मोसंबी"],
    "Brinjal": ["brinjal", "eggplant", "baingan", "vangi", "वांगी", "बैंगन"],
    "Cabbage / Cauliflower": ["cabbage", "cauliflower", "gobhi", "patta gobhi", "phool gobhi", "कोबी"],
    "Garlic / Ginger": ["garlic", "ginger", "lahsun", "adrak", "ale", "लसूण", "अदरक"],
    "Cattle / Dairy": ["cow", "buffalo", "cattle", "calf", "bull", "bovine", "गाय", "म्हैस", "पशु", "दूध"],
    "Poultry / Birds": ["poultry", "chicken", "hen", "broiler", "कुक्कुटपालन", "मुर्गी"],
}

# Category classification rules (ordered by specificity)
CATEGORY_RULES = [
    ("Flower & Fruit Drop", ["flower drop", "fruit drop", "planofix", "fruit setting", "dropping", "फुलगळ", "फूल झड़ना"]),
    ("Animal Husbandry & Dairy", ["cow", "buffalo", "cattle", "mastitis", "milk", "dairy", "poultry", "calf", "diarrhoea in cow", "fmd", "deworming", "पशु", "दूध"]),
    ("Pest & Disease Management", ["aphid", "pest", "disease", "fungus", "blight", "rust", "borer", "wilt", "spray", "infestation", "caterpillar", "leaf curl", "yellowing", "fungicide", "insecticide", "rogor", "profenofos", "emamectin", "quinalphos", "coragen", "spinosad", "flubendiamide", "कीट", "रोग", "अळी", "फवारणी", "बोंडअळी", "प्रादुर्भाव"]),
    ("Fertilizer & Plant Nutrition", ["fertilizer", "urea", "ssp", "mop", "dap", "borax", "zinc", "nitrogen", "potash", "manure", "npk", "dose", "dosage", "खाद", "खत", "मात्रा"]),
    ("Sowing & Variety", ["seed", "variety", "sowing", "spacing", "germination", "hybrid", "nursery", "transplanting", "बीज", "पेरणी", "बुवाई"]),
    ("Irrigation & Water", ["irrigation", "water", "drip", "sprinkler", "drought", "moisture", "सिंचाई", "पाणी", "पाणी व्यवस्थापन"]),
    ("Weed Management", ["weed", "weedicide", "herbicide", "glyphosate", "pendimethalin", "तण", "खरपतवार"]),
    ("Government Schemes & Credit", ["kisan credit card", "kcc", "subsidy", "scheme", "pm-kisan", "insurance", "loan", "योजना", "विमा"]),
]

INDIAN_STATES = [
    "Maharashtra", "Gujarat", "Madhya Pradesh", "Punjab", "Haryana", "Rajasthan",
    "Andhra Pradesh", "Telangana", "Karnataka", "Tamil Nadu", "Uttar Pradesh",
    "Bihar", "Odisha", "West Bengal", "Assam", "Kerala", "Himachal Pradesh",
    "Jammu & Kashmir", "Uttarakhand", "Jharkhand", "Chhattisgarh", "मराठवाडा", "विदर्भ"
]

GENERIC_ANSWER_PHRASES = [
    "explain in detail", "explained in detail", "explained in details", "explain in details",
    "explained him in detail", "explained him in details", "explained her in detail",
    "explained to farmer", "transferred to", "call disconnected", "line busy",
    "talked with farmer", "wrong number", "no response", "disconnected", "call dropped",
    "advised to consult", "consult nearby kvk", "not available", "na", "explained",
    "given in details", "explin in details", "given in details about the package of practices"
]

def clean_text(text: str) -> str:
    """Removes extra whitespace and cleans string."""
    if not text:
        return ""
    text = re.sub(r"\s+", " ", str(text)).strip()
    return text

def is_unusable_record(question: str, answer: str) -> bool:
    """Identifies rows that lack meaningful agricultural information."""
    if not question or not answer:
        return True

    q_clean = clean_text(question).lower()
    a_clean = clean_text(answer).lower()

    if len(q_clean) < 8 or len(a_clean) < 20:
        return True

    for phrase in GENERIC_ANSWER_PHRASES:
        if a_clean == phrase or a_clean.startswith(phrase):
            return True

    return False

def extract_metadata(text_content: str) -> Dict[str, Any]:
    """Infers crop, category, location, language, and date from text content."""
    combined = text_content.lower()

    # 1. Crop Detection
    detected_crop = "General Agriculture"
    for crop_name, keywords in CROP_KEYWORDS.items():
        if any(kw in combined for kw in keywords):
            detected_crop = crop_name
            break

    # 2. Category Detection
    detected_category = "General Agronomy"
    for cat_name, keywords in CATEGORY_RULES:
        if any(kw in combined for kw in keywords):
            detected_category = cat_name
            break

    # 3. Location Detection
    detected_location = "All India"
    for st in INDIAN_STATES:
        if st.lower() in combined:
            detected_location = st
            break

    # 4. Language Detection
    has_devanagari = bool(re.search(r'[\u0900-\u097F]', text_content))
    detected_lang = "mr" if any(w in text_content for w in ["आहे", "करावे", "करावा", "पिकाला", "शेतकरी", "अळी"]) else ("hi" if has_devanagari else "en")

    # 5. Date / Season Detection
    detected_date = "Kharif 2025" if "kharif" in combined or "2025" in combined else ("April 2022" if "2022" in combined else "All Season")

    return {
        "crop": detected_crop,
        "category": detected_category,
        "location": detected_location,
        "language": detected_lang,
        "date": detected_date
    }

def discover_all_pdfs(search_directories: List[str]) -> List[str]:
    """
    Automatically finds all PDF files in the specified project directories.
    """
    pdf_files = set()
    for directory in search_directories:
        if os.path.exists(directory):
            for root, _, files in os.walk(directory):
                if "venv" in root or "node_modules" in root:
                    continue
                for f in files:
                    if f.lower().endswith(".pdf"):
                        pdf_files.add(os.path.join(root, f))
    return sorted(list(pdf_files))

def extract_and_chunk_pdf(
    pdf_path: str,
    chunk_size: int = 700,
    chunk_overlap: int = 120
) -> List[Dict[str, Any]]:
    """
    Extracts text page-by-page from a PDF, splits into coherent chunks,
    and attaches rich metadata (source, filename, page_number, crop, category, language, location, date).
    """
    if not os.path.exists(pdf_path):
        logger.warning(f"PDF file not found: {pdf_path}")
        return []

    file_name = os.path.basename(pdf_path)
    file_name_lower = file_name.lower()

    # Determine source name
    if "icar" in file_name_lower or "kharif" in file_name_lower:
        source_name = "ICAR/KVK Advisory"
    elif "bulletin" in file_name_lower or "national" in file_name_lower or "imd" in file_name_lower:
        source_name = "National Agromet Bulletin"
    else:
        source_name = "Agricultural Advisory PDF"

    chunks = []
    try:
        reader = pypdf.PdfReader(pdf_path)
        total_pages = len(reader.pages)
        logger.info(f"Extracting {total_pages} pages from '{file_name}'...")

        for page_idx, page in enumerate(reader.pages):
            page_num = page_idx + 1
            try:
                raw_text = page.extract_text() or ""
            except Exception as e:
                logger.warning(f"Error extracting page {page_num} in {file_name}: {e}")
                continue

            cleaned_page = clean_text(raw_text)
            if len(cleaned_page) < 30:
                continue

            # Split page text into chunks
            start = 0
            while start < len(cleaned_page):
                end = start + chunk_size
                chunk_text = cleaned_page[start:end]

                # Sentence boundary
                if end < len(cleaned_page):
                    last_period = chunk_text.rfind(".")
                    if last_period > chunk_size // 2:
                        chunk_text = chunk_text[:last_period + 1]
                        end = start + last_period + 1

                chunk_text = chunk_text.strip()
                if len(chunk_text) >= 40:
                    meta = extract_metadata(chunk_text)
                    chunk_id = f"{file_name[:8]}-P{page_num}-{len(chunks)+1}"

                    searchable_doc = (
                        f"Source: {source_name} (Document: {file_name} | Page {page_num})\n"
                        f"Crop: {meta['crop']} | Category: {meta['category']} | Location: {meta['location']} | Date: {meta['date']}\n"
                        f"Advisory Content:\n{chunk_text}"
                    )

                    chunks.append({
                        "record_id": chunk_id,
                        "question": f"Agricultural advisory on {meta['crop']} ({meta['category']})",
                        "answer": chunk_text,
                        "crop": meta["crop"],
                        "category": meta["category"],
                        "source": source_name,
                        "filename": file_name,
                        "file_name": file_name,
                        "page_number": page_num,
                        "location": meta["location"],
                        "language": meta["language"],
                        "date": meta["date"],
                        "document_type": "agricultural_advisory",
                        "searchable_doc": searchable_doc
                    })

                start = end - chunk_overlap
                if start < 0 or start >= len(cleaned_page):
                    break

    except Exception as e:
        logger.error(f"Failed to read PDF '{pdf_path}': {e}")

    return chunks

def clean_and_process_kcc_data(
    input_csv_path: str,
    output_csv_path: str,
    output_jsonl_path: Optional[str] = None,
    max_records: Optional[int] = None
) -> Dict[str, Any]:
    """Cleans raw KCC CSV records, filters noise, enriches with metadata."""
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
    if output_jsonl_path:
        os.makedirs(os.path.dirname(output_jsonl_path), exist_ok=True)

    if not os.path.exists(input_csv_path):
        raise FileNotFoundError(f"Input KCC dataset not found at: {input_csv_path}")

    total_read = 0
    total_kept = 0
    total_filtered = 0
    crop_counter = Counter()
    category_counter = Counter()

    cleaned_records: List[Dict[str, Any]] = []

    with open(input_csv_path, "r", encoding="utf-8", errors="replace") as f_in:
        reader = csv.DictReader(f_in)
        fieldnames = reader.fieldnames or []
        q_col = next((c for c in fieldnames if "question" in c.lower() or "query" in c.lower()), "questions")
        a_col = next((c for c in fieldnames if "answer" in c.lower() or "kccans" in c.lower() or "response" in c.lower()), "answers")

        for row in reader:
            total_read += 1
            if max_records and total_kept >= max_records:
                break

            q_raw = clean_text(row.get(q_col, ""))
            a_raw = clean_text(row.get(a_col, ""))

            if is_unusable_record(q_raw, a_raw):
                total_filtered += 1
                continue

            meta = extract_metadata(q_raw + " " + a_raw)
            total_kept += 1
            record_id = f"KCC-{total_kept:06d}"

            crop_counter[meta["crop"]] += 1
            category_counter[meta["category"]] += 1

            searchable_doc = (
                f"Source: Kisan Call Centre (Record: {record_id})\n"
                f"Crop: {meta['crop']} | Category: {meta['category']}\n"
                f"Farmer Query: {q_raw}\n"
                f"KCC Advisory: {a_raw}"
            )

            record = {
                "record_id": record_id,
                "question": q_raw,
                "answer": a_raw,
                "crop": meta["crop"],
                "category": meta["category"],
                "source": "Kisan Call Centre",
                "filename": "kcc_dataset.csv",
                "file_name": "kcc_dataset.csv",
                "page_number": None,
                "location": meta["location"],
                "language": meta["language"],
                "date": "KCC Official Advisory",
                "document_type": "kcc_qa_record",
                "searchable_doc": searchable_doc
            }
            cleaned_records.append(record)

    # Write to CSV
    csv_fields = ["record_id", "question", "answer", "crop", "category", "source", "filename", "file_name", "page_number", "location", "language", "date", "document_type", "searchable_doc"]
    with open(output_csv_path, "w", encoding="utf-8", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=csv_fields)
        writer.writeheader()
        writer.writerows(cleaned_records)

    # Write to JSONL
    if output_jsonl_path:
        with open(output_jsonl_path, "w", encoding="utf-8") as f_jsonl:
            for rec in cleaned_records:
                f_jsonl.write(json.dumps(rec, ensure_ascii=False) + "\n")

    return {
        "total_read": total_read,
        "total_kept": total_kept,
        "total_filtered": total_filtered,
        "unique_crops": len(crop_counter),
        "top_crops": dict(crop_counter.most_common(10)),
        "categories": dict(category_counter.most_common(10)),
        "output_csv": output_csv_path,
        "output_jsonl": output_jsonl_path
    }

def load_processed_data(processed_csv_path: str) -> List[Dict[str, Any]]:
    """Loads cleaned KCC dataset records."""
    if not os.path.exists(processed_csv_path):
        raise FileNotFoundError(f"Processed KCC file not found: {processed_csv_path}")

    records = []
    with open(processed_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            records.append(r)
    return records
