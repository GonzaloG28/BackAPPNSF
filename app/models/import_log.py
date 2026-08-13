# app/models/import_log.py
from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, func
import enum

from app.database import Base


class ImportType(str, enum.Enum):
    ROSTER = "ROSTER"
    ATTENDANCE = "ATTENDANCE"
    TIMES = "TIMES"
    QUALIFYING_TIMES = "QUALIFYING_TIMES"


class ImportStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class ImportLog(Base):
    __tablename__ = "import_logs"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(255), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    type = Column(Enum(ImportType), nullable=False)
    row_count = Column(Integer, default=0)
    matched_count = Column(Integer, default=0)
    unmatched_count = Column(Integer, default=0)
    status = Column(Enum(ImportStatus), default=ImportStatus.SUCCESS)
    created_at = Column(DateTime, server_default=func.now())