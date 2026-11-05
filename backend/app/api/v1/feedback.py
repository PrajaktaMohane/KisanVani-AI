from fastapi import APIRouter
from app.models.chat import FeedbackCreate
from app.db.repositories.feedback_repo import FeedbackRepository

router = APIRouter()

@router.post("/record")
async def record_user_feedback(feedback: FeedbackCreate):
    """
    Records farmer feedback (helpful/unhelpful, star rating, comments) to continuously improve advice.
    """
    await FeedbackRepository.record_feedback(feedback.model_dump())
    return {"status": "success", "message": "Thank you for your feedback!"}
