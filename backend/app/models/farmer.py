from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class FarmerBase(BaseModel):
    phone_number: Optional[str] = Field(None, description="Farmer phone number or session ID")
    name: Optional[str] = Field(None, description="Farmer full name")
    state: str = Field(default="Maharashtra", description="State in India")
    district: Optional[str] = Field(default=None, description="District")
    primary_language: str = Field(default="hi", description="ISO language code (e.g. hi, mr, te, ta, en)")
    crops_grown: List[str] = Field(default_factory=lambda: ["Wheat", "Cotton"], description="List of primary crops")
    soil_type: Optional[str] = Field(default="Black soil", description="Soil classification (Alluvial, Black, Red, etc.)")
    land_size_acres: Optional[float] = Field(default=2.5, description="Land holding in acres")

class FarmerCreate(FarmerBase):
    pass

class FarmerProfile(FarmerBase):
    id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Ramesh Patil",
                "phone_number": "+919876543210",
                "state": "Maharashtra",
                "district": "Nagpur",
                "primary_language": "mr",
                "crops_grown": ["Cotton", "Soybean"],
                "soil_type": "Black soil",
                "land_size_acres": 4.0
            }
        }
