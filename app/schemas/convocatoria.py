# app/schemas/convocatoria.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum


class ConvocatoriaStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    EXPORTED = "EXPORTED"


class ConvocatoriaCreate(BaseModel):
    competition_id: int


class ConvocatoriaOut(BaseModel):
    id: int
    competition_id: int
    status: ConvocatoriaStatusEnum
    created_at: datetime

    class Config:
        from_attributes = True


class MatrixEntry(BaseModel):
    event_type_id: int
    event_name: str
    best_time: Optional[float] = None
    best_time_date: Optional[str] = None 
    qualifying_time: Optional[float] = None
    qualifies: bool
    selected: bool


class MatrixSwimmerRow(BaseModel):
    swimmer_id: int
    name: str
    entries: list[MatrixEntry]


class ConvocatoriaMatrix(BaseModel):
    convocatoria_id: int
    swimmers: list[MatrixSwimmerRow]


class EntrySelectionUpdate(BaseModel):
    swimmer_id: int
    event_type_id: int
    time_record_id: int
    selected: bool


class ConvocatoriaEntriesUpdate(BaseModel):
    entries: list[EntrySelectionUpdate]