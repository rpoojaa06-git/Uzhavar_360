from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

# 10 Stages of Farmer Journey (Section 5)
FARMING_STAGES = [
    "Planning",
    "Crop Selection",
    "Land Preparation",
    "Seed/Input Selection",
    "Sowing",
    "Crop Management",
    "Pest/Disease Management",
    "Harvest",
    "Selling / Marketing",
    "Next Season Planning"
]

class FarmerProfile(BaseModel):
    name: Optional[str] = "Farmer"
    language: Optional[str] = "English"
    district: Optional[str] = "Thanjavur"
    land_acres: Optional[float] = 2.0
    land_ownership: Optional[str] = "Owner"  # Owner, Tenant, Lease
    soil_type: Optional[str] = "Alluvial Soil"
    water_source: Optional[str] = "Borewell"
    crop: Optional[str] = "Paddy"
    farming_stage: Optional[str] = "Planning"
    experience_years: Optional[int] = 5
    farmer_category: Optional[str] = "Small"  # Marginal (<2.5 ac), Small (2.5-5 ac), Medium/Large (>5 ac)
    equipment_owned: Optional[List[str]] = Field(default_factory=list)
    current_goal: Optional[str] = "Maximize yield and explore water-saving methods"


class Source(BaseModel):
    source: str
    page: int
    score: float


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    question: str
    language: Optional[str] = None
    district: Optional[str] = None
    land_acres: Optional[float] = None
    crop: Optional[str] = None
    stage: Optional[str] = None
    water_source: Optional[str] = None
    # Advanced fields
    profile: Optional[FarmerProfile] = None
    history: Optional[List[ChatMessage]] = Field(default_factory=list)


class DeepLink(BaseModel):
    """A ready-to-open deep link into the Uzhavar demo UI."""
    id: str                      # service id, or "home" for the app grid
    label_en: Optional[str] = None
    label_ta: Optional[str] = None
    emoji: Optional[str] = None
    url: str
    spoken: Optional[str] = None  # instruction to be spoken/TTS'd, not the URL


class ChatResponse(BaseModel):
    answer: str
    sources: List[Source]
    current_stage: Optional[str] = None
    next_step_recommendation: Optional[str] = None
    deep_link: Optional[DeepLink] = None  # present when the question maps to a demo page
