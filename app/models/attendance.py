# app/models/attendance.py
from sqlalchemy import Column, Integer, Date, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class AttendanceShift(str, enum.Enum):
    AM = "AM"
    PM = "PM"
    AM_PM = "AM_PM"
    ABSENT = "ABSENT"


class Attendance(Base):
    __tablename__ = "attendances"

    id = Column(Integer, primary_key=True, index=True)
    swimmer_id = Column(Integer, ForeignKey("swimmers.id"), nullable=False)
    date = Column(Date, nullable=False)
    shift = Column(Enum(AttendanceShift), nullable=False, default=AttendanceShift.ABSENT)
    session_id = Column(Integer, ForeignKey("training_sessions.id"), nullable=True)

    swimmer = relationship("Swimmer", back_populates="attendances")