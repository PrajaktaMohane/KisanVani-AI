
import sys
sys.path.insert(0, "backend")

from app.rag.vector_store import FAISSVectorStoreManager

store = FAISSVectorStoreManager.load_vector_store()

if store is None:
    print("FAISS index not loaded.")
else:
    documents = list(store.docstore._dict.values())

    search_terms = [
        "girdle beetle",
        "Thiamethoxam",
        "Chlorantraniliprole",
        "PM Kisan",
        "6000",
        "2,000",
        "2000"
    ]

    for term in search_terms:
        print("\n" + "=" * 70)
        print("SEARCH TERM:", term)

        matches = [
            doc for doc in documents
            if term.lower() in doc.page_content.lower()
        ]

        print("MATCHES FOUND:", len(matches))

        for doc in matches[:5]:
            print("\nCrop:", doc.metadata.get("crop"))
            print("Record:", doc.metadata.get("record_id"))
            print("Content:\n", doc.page_content[:1500])
