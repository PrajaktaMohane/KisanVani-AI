import pytest
from app.services.rag_service import RAGService

# 10 Multilingual Agricultural Test Cases
AGRICULTURAL_TEST_CASES = [
    # 1. Marathi: Cotton Pink Bollworm
    {
        "query": "माझ्या कापसाच्या पिकावर गुलाबी बोंडअळी आली आहे, काय करावे?",
        "expected_crop": "Cotton",
        "expected_keywords": ["Profenofos", "Emamectin", "फेरोमन", "बोंड", "Cotton"]
    },
    # 2. Marathi: Pheromone trap dosage
    {
        "query": "कापसात एका एकरात किती कामगंध सापळे लावावेत?",
        "expected_crop": "Cotton",
        "expected_keywords": ["सापळे", "5", "8", "Gossyplure", "Cotton"]
    },
    # 3. Hindi: Wheat Yellow Rust
    {
        "query": "गेहूं में पीला रतुआ का प्रकोप है, कौन सी दवा का छिड़काव करें?",
        "expected_crop": "Wheat",
        "expected_keywords": ["Propiconazole", "गेहूं", "रतुआ", "200"]
    },
    # 4. Hindi: Wheat CRI irrigation stage
    {
        "query": "गेहूं में पहली सिंचाई और यूरिया कब देना चाहिए?",
        "expected_crop": "Wheat",
        "expected_keywords": ["20", "25", "CRI", "यूरिया", "सिंचाई"]
    },
    # 5. Hindi: Soybean Girdle Beetle
    {
        "query": "सोयाबीन में चक्र भृंग (गर्डल बीटल) का नियंत्रण कैसे करें?",
        "expected_crop": "Soybean",
        "expected_keywords": ["Thiamethoxam", "Chlorantraniliprole", "सोयाबीन", "Girdle"]
    },
    # 6. English: Rice Yellow Stem Borer
    {
        "query": "How to control yellow stem borer in paddy crop?",
        "expected_crop": "Rice",
        "expected_keywords": ["Cartap", "Chlorantraniliprole", "Dead Heart", "Rice"]
    },
    # 7. English: Rice Blast Disease
    {
        "query": "What is the recommended fungicide for leaf blast in rice?",
        "expected_crop": "Rice",
        "expected_keywords": ["Tricyclazole", "Blast", "Rice"]
    },
    # 8. Hindi: Zinc Micronutrient Deficiency in Paddy
    {
        "query": "धान में जिंक की कमी (खैरा रोग) के क्या लक्षण हैं और कितनी मात्रा दें?",
        "expected_crop": "Rice",
        "expected_keywords": ["Zinc", "जिंक", "सल्फेट", "खैरा"]
    },
    # 9. English: Agromet Spray Weather Timing
    {
        "query": "Should I spray pesticide if rain is predicted tomorrow?",
        "expected_crop": None,
        "expected_keywords": ["rain", "24", "wash", "humidity"]
    },
    # 10. Hindi: PM-KISAN Scheme Benefits
    {
        "query": "पीएम किसान सम्मान निधि योजना में कितने रुपये मिलते हैं?",
        "expected_crop": None,
        "expected_keywords": ["6,000", "2,000", "किस्त"]
    }
]

@pytest.mark.parametrize("case", AGRICULTURAL_TEST_CASES)
def test_agricultural_rag_retrieval(case):
    query = case["query"]
    crop = case["expected_crop"]

    context_str, sources, is_grounded = RAGService.retrieve_grounded_context(
        query=query,
        crop=crop
    )

    # Retrieval should return non-empty context and valid sources
    assert context_str is not None
    assert len(sources) > 0

    # Verify that at least one of the expected agronomic terms is present in the retrieved context
    matches = [kw for kw in case["expected_keywords"] if kw.lower() in context_str.lower()]
    assert len(matches) > 0, f"None of {case['expected_keywords']} found in retrieved context for query: {query}"
