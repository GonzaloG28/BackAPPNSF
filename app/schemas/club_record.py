# app/schemas/club_record.py
from pydantic import BaseModel
from typing import Optional


class ClubRecordOut(BaseModel):
    event_type_id: int
    event_name: str
    distance_m: int
    stroke: str
    category: str
    gender: str
    pool_length: int
    time_seconds: Optional[float] = None
    swimmer_id: Optional[int] = None
    swimmer_name: Optional[str] = None
    achieved_date: Optional[str] = None
