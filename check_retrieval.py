
import sys
sys.path.insert(0, "backend")

from app.rag.vector_store import FAISSVectorStoreManager

questions = [
    "गेहूं में पीला रतुआ का प्रकोप है, कौन सी दवा का छिड़काव करें?",
    "सोयाबीन में चक्र भृंग (गर्डल बीटल) का नियंत्रण कैसे करें?",
    "धान में जिंक की कमी (खैरा रोग) के क्या लक्षण हैं और कितनी मात्रा दें?",
    "पीएम किसान सम्मान निधि योजना में कितने रुपये मिलते हैं?"
]

for question in questions:
    print("\n" + "=" * 80)
    print("QUESTION:", question)

    docs = FAISSVectorStoreManager.search_similar(
        query=question,
        top_k=5
    )

    for i, doc in enumerate(docs, start=1):
        print(f"\nResult {i}")
        print("Crop:", doc.metadata.get("crop"))
        print("Score:", doc.metadata.get("score"))
        print("Record:", doc.metadata.get("record_id"))
        print("Content:", doc.page_content[:400])
