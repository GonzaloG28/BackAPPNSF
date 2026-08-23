# app/schemas/calendar.py
from pydantic import BaseModel
from datetime import date
from typing import Optional

class CustomGroupCreate(BaseModel):
    name: str
    profile: str  # COMPETITIVE | FORMATIVE
    categories: list[str]

class TrainingSessionCreate(BaseModel):
    date: date
    shift: str  # AM | PM | GYM
    profile: str
    target_type: str  # CATEGORY | CUSTOM_GROUP
    target_category: Optional[str] = None
    target_group_id: Optional[int] = None
    week_number: Optional[int] = None
    objective: Optional[str] = None
    total_volume_m: Optional[int] = None
    warmup_text: Optional[str] = None
    technique_text: Optional[str] = None
    work1_text: Optional[str] = None
    work2_text: Optional[str] = None
    cooldown_text: Optional[str] = None

class TrainingSessionUpdate(TrainingSessionCreate):
    pass