# app/schemas/time_record.py — nuevo
from pydantic import BaseModel
from datetime import date
from typing import Optional

class TimeRecordUpdate(BaseModel):
    time_seconds: Optional[float] = None
    recorded_date: Optional[date] = None
    pool_length: Optional[int] = None
    location_note: Optional[str] = None