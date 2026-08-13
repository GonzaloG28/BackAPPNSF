# app/schemas/import_.py
from pydantic import BaseModel
from typing import Optional, Any
from enum import Enum


class ImportStatusEnum(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class UnmatchedRow(BaseModel):
    row: int
    raw_data: dict[str, Any]
    reason: str
    candidates: Optional[list[int]] = None


class ImportResult(BaseModel):
    import_log_id: int
    status: ImportStatusEnum
    row_count: int
    matched_count: int
    unmatched_count: int
    unmatched_rows: list[UnmatchedRow] = []


class ResolveUnmatchedRequest(BaseModel):
    row: int
    action: str  # "create_new" | "link_to_swimmer"
    swimmer_id: Optional[int] = None