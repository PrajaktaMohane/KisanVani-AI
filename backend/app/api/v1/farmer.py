from fastapi import APIRouter, HTTPException, status
from app.models.farmer import FarmerCreate, FarmerProfile
from app.db.repositories.farmer_repo import FarmerRepository

router = APIRouter()

@router.post("/profile", response_model=FarmerProfile)
async def create_or_update_profile(farmer_data: FarmerCreate):
    """
    Creates or updates the farmer's personal profile (crops, land holding, language, region).
    """
    if not farmer_data.phone_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number or unique identifier is required."
        )

    result = await FarmerRepository.create_or_update_farmer(
        phone_number=farmer_data.phone_number,
        data=farmer_data.model_dump()
    )
    return result

@router.get("/profile/{phone_number}", response_model=FarmerProfile)
async def get_profile(phone_number: str):
    """
    Retrieves farmer profile by phone number.
    """
    profile = await FarmerRepository.get_farmer_by_phone(phone_number)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farmer profile not found."
        )
    return profile
