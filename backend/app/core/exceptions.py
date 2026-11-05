"""
Custom Application Exceptions for KisanVani AI
"""
from fastapi import HTTPException, status

class AudioProcessingException(HTTPException):
    def __init__(self, detail: str = "Error processing audio input"):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)

class SpeechToTextException(HTTPException):
    def __init__(self, detail: str = "Failed to transcribe voice query"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)

class TextToSpeechException(HTTPException):
    def __init__(self, detail: str = "Failed to generate speech audio"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)

class RAGRetrievalException(HTTPException):
    def __init__(self, detail: str = "Error retrieving agricultural knowledge documents"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)

class LLMGenerationException(HTTPException):
    def __init__(self, detail: str = "Error generating agricultural advisory via Gemini"):
        super().__init__(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail)
