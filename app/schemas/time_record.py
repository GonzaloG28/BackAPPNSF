# app/schemas/time_record.py
from pydantic import BaseModel, ConfigDict
from datetime import date
from typing import Optional


class TimeSplitIn(BaseModel):
    distance_mark: int
    segment_seconds: float


class TimeSplitOut(TimeSplitIn):
    id: int
    cumulative_seconds: float
    model_config = ConfigDict(from_attributes=True)


class TimeRecordCreate(BaseModel):
    event_type_id: int
    time_seconds: float
    recorded_date: date
    pool_length: Optional[int] = None
    location_note: Optional[str] = None
    split_increment: Optional[int] = None       # 50 | 100
    splits: Optional[list[TimeSplitIn]] = None  # segmentos, en orden


class TimeRecordUpdate(BaseModel):
    time_seconds: Optional[float] = None
    recorded_date: Optional[date] = None
    pool_length: Optional[int] = None
    location_note: Optional[str] = None
    split_increment: Optional[int] = None
    splits: Optional[list[TimeSplitIn]] = None