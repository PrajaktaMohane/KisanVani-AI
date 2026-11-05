from langchain_text_splitters import RecursiveCharacterTextSplitter

def get_agricultural_text_splitter(chunk_size: int = 600, chunk_overlap: int = 100):
    """
    Returns a RecursiveCharacterTextSplitter configured to maintain agricultural context
    (preserving dosages, symptoms, and tables).
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "। ", ". ", "; ", ", ", " "],
        keep_separator=True
    )
