# app/schemas/attendance.py
from pydantic import BaseModel
from datetime import date
from typing import Optional


class AttendanceRecord(BaseModel):
    swimmer_id: int
    present: bool


class AttendanceBulkCreate(BaseModel):
    session_id: Optional[int] = None
    date: date
    records: list[AttendanceRecord]


class AttendanceOut(BaseModel):
    swimmer_id: int
    swimmer_name: str
    present: bool
    date: date


class AttendanceSummary(BaseModel):
    swimmer_id: int
    swimmer_name: str
    total_sessions: int
    present_count: int
    attendance_rate: float  # porcentaje 0-100