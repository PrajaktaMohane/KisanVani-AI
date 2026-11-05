import pytest
from app.services.rag_service import RAGService
from app.core.prompts import KISAN_MITRA_SYSTEM_PROMPT, GROUNDED_RAG_USER_PROMPT_TEMPLATE

def test_prompt_contains_strict_dosage_safety_rules():
    """Verify that the system prompt strictly forbids guessing pesticide/fertilizer dosages."""
    assert "ZERO-TOLERANCE DOSAGE GUARDRAIL" in KISAN_MITRA_SYSTEM_PROMPT
    assert "DO NOT GUESS OR ESTIMATE" in KISAN_MITRA_SYSTEM_PROMPT
    assert "Krishi Vigyan Kendra" in KISAN_MITRA_SYSTEM_PROMPT
    assert "EVIDENCE-ONLY POLICY" in KISAN_MITRA_SYSTEM_PROMPT

def test_ungrounded_query_flagging():
    """Verify that completely ungrounded / non-agricultural queries are flagged as ungrounded."""
    nonsense_query = "quantum mechanical wave function superposition in qubits"
    context_str, sources, is_grounded = RAGService.retrieve_grounded_context(query=nonsense_query)

    # Non-agricultural text should either have no matches or be flagged with weak relevance
    assert is_grounded is False or len(sources) == 0 or "NO_TRUSTED_CONTEXT_FOUND" in context_str
