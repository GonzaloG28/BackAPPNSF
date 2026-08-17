# app/schemas/competition.py
from pydantic import BaseModel
from datetime import date
from typing import Optional


class CompetitionCreate(BaseModel):
    name: str
    start_date: date
    end_date: date
    organizer: Optional[str] = None
    location: Optional[str] = None
    pool_length: Optional[int] = None
    categories: Optional[list[str]] = None
    max_events_per_swimmer: int = 3


class QualifyingTimeUpdate(BaseModel):
    event_type_id: Optional[int] = None
    min_time_seconds: Optional[float] = None
    gender: Optional[str] = None
    category: Optional[str] = None

class CompetitionUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    organizer: Optional[str] = None
    location: Optional[str] = None
    pool_length: Optional[int] = None
    categories: Optional[list[str]] = None
    max_events_per_swimmer: Optional[int] = None