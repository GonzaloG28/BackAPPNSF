# app/schemas/test_battery.py
from pydantic import BaseModel, ConfigDict
from datetime import date
from typing import Optional

from app.models.test_battery import TestResultType


class TestBatterySplitIn(BaseModel):
    distance_mark: int
    segment_seconds: float


class TestBatteryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    structure_label: Optional[str] = None
    result_type: TestResultType = TestResultType.TIME
    distance_m: Optional[int] = None
    allows_splits: bool = False
    reps_count: Optional[int] = None
    is_control: bool = False
    event_type_id: Optional[int] = None


class TestBatteryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    structure_label: Optional[str] = None
    result_type: Optional[TestResultType] = None
    distance_m: Optional[int] = None
    allows_splits: Optional[bool] = None
    reps_count: Optional[int] = None
    is_control: Optional[bool] = None
    event_type_id: Optional[int] = None


class TestBatteryRepIn(BaseModel):
    rep_number: int
    time_seconds: float
    notes: Optional[str] = None
    splits: Optional[list[TestBatterySplitIn]] = None


class RepsResultIn(BaseModel):
    swimmer_id: int
    recorded_date: date
    reps: list[TestBatteryRepIn]
    notes: Optional[str] = None


class TestBatteryResultEntry(BaseModel):
    swimmer_id: int
    value_seconds: Optional[float] = None
    value_reps: Optional[int] = None
    notes: Optional[str] = None
    split_increment: Optional[int] = None
    splits: Optional[list[TestBatterySplitIn]] = None


class BulkResultsIn(BaseModel):
    recorded_date: date
    entries: list[TestBatteryResultEntry]


class TestBatteryResultUpdate(BaseModel):
    value_seconds: Optional[float] = None
    value_reps: Optional[int] = None
    recorded_date: Optional[date] = None
    notes: Optional[str] = None
    split_increment: Optional[int] = None
    splits: Optional[list[TestBatterySplitIn]] = None
