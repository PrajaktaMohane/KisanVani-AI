import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
import sys
import json
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.rag import retrieve_kcc_evidence
from backend.config import settings

# Configure logger
logging.basicConfig(level=logging.WARNING)

def main():
    questions_file = os.path.join(settings.BASE_DIR, "data", "test_questions.json")
    if not os.path.exists(questions_file):
        print(f"❌ Error: {questions_file} not found!")
        sys.exit(1)

    with open(questions_file, "r", encoding="utf-8") as f:
        test_questions = json.load(f)

    print("=" * 80)
    print("🌾 KISANVANI 60-QUESTION MULTILINGUAL RETRIEVAL TEST")
    print(f"Total Test Questions: {len(test_questions)}")
    print("=" * 80 + "\n")

    lang_stats = {"mr": {"total": 0, "supported": 0}, "hi": {"total": 0, "supported": 0}, "en": {"total": 0, "supported": 0}}
    failed_questions = []

    for q_data in test_questions:
        q_id = q_data["id"]
        lang = q_data["language"]
        question = q_data["question"]
        expected_crop = q_data.get("expected_crop", "General")
        expected_topic = q_data.get("expected_topic", "advisory")

        lang_stats[lang]["total"] += 1

        # Perform RAG retrieval
        records, confidence, is_grounded, context_str = retrieve_kcc_evidence(
            query=question,
            top_k=6,
            language_code=lang
        )

        top_record = records[0] if records else {}
        top_source = top_record.get("source", "N/A")
        top_file = top_record.get("filename") or top_record.get("file_name", "N/A")
        top_page = top_record.get("page_number")
        page_str = str(top_page) if top_page is not None else "N/A"
        score = top_record.get("similarity_distance", top_record.get("similarity_score", 99.0))
        retrieved_text = top_record.get("answer", "No text retrieved").strip()
        short_text = (retrieved_text[:280] + "...") if len(retrieved_text) > 280 else retrieved_text

        # Determine if genuinely supported by knowledge base
        # Supported if is_grounded is True AND score <= SIMILARITY_THRESHOLD AND text has content
        supported = is_grounded and score <= settings.SIMILARITY_THRESHOLD and len(retrieved_text) >= 20

        if supported:
            lang_stats[lang]["supported"] += 1
            status_str = "YES"
        else:
            status_str = "NO"
            failed_questions.append({
                "id": q_id,
                "language": lang,
                "question": question,
                "score": score,
                "reason": f"Distance {score} exceeds threshold {settings.SIMILARITY_THRESHOLD}" if score > settings.SIMILARITY_THRESHOLD else "Insufficient content"
            })

        print("--------------------------------")
        print(f"ID:       {q_id}")
        print(f"Language: {lang.upper()}")
        print(f"Question: {question}")
        print()
        print(f"Top Retrieved Source: {top_source}")
        print(f"File:                 {top_file}")
        print(f"Page:                 {page_str}")
        print(f"Score:                {score:.4f}")
        print()
        print(f"Retrieved Text:")
        print(f"{short_text}")
        print()
        print(f"Supported by Knowledge Base:")
        print(f"{status_str}")
        print("--------------------------------\n")

    # Summary Report
    mr_sup = lang_stats["mr"]["supported"]
    mr_tot = lang_stats["mr"]["total"]
    hi_sup = lang_stats["hi"]["supported"]
    hi_tot = lang_stats["hi"]["total"]
    en_sup = lang_stats["en"]["supported"]
    en_tot = lang_stats["en"]["total"]
    total_sup = mr_sup + hi_sup + en_sup
    total_tot = mr_tot + hi_tot + en_tot

    print("=" * 80)
    print("📊 FINAL RETRIEVAL EVALUATION SUMMARY")
    print("=" * 80)
    print(f"Marathi:")
    print(f"{mr_sup} / {mr_tot} supported ({mr_sup/mr_tot*100:.1f}%)")
    print()
    print(f"Hindi:")
    print(f"{hi_sup} / {hi_tot} supported ({hi_sup/hi_tot*100:.1f}%)")
    print()
    print(f"English:")
    print(f"{en_sup} / {en_tot} supported ({en_sup/en_tot*100:.1f}%)")
    print()
    print(f"Overall:")
    print(f"{total_sup} / {total_tot} supported ({total_sup/total_tot*100:.1f}%)")
    print("=" * 80)

    if failed_questions:
        print("\n❌ Failed Questions Analysis:")
        for f in failed_questions:
            print(f"  • [{f['id']}] ({f['language'].upper()}) '{f['question']}' -> {f['reason']}")
    else:
        print("\n✅ All 60 questions successfully retrieved and supported by the Knowledge Base!")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
