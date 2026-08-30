# app/models/attendance_log.py
from sqlalchemy import Column, Integer, Date, Boolean, ForeignKey, UniqueConstraint, Enum
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class AttendanceShift(str, enum.Enum):
    AM = "AM"
    PM = "PM"
    AM_PM = "AM_PM"

class AttendanceLog(Base):
    """
    Log simple: un registro por nadador por día. Solo Cumplió/No Cumplió.
    Reemplaza el modelo de turnos AM/PM para el flujo de asistencia diaria.
    """
    __tablename__ = "attendance_logs"

    id = Column(Integer, primary_key=True, index=True)
    swimmer_id = Column(Integer, ForeignKey("swimmers.id"), nullable=False)
    date = Column(Date, nullable=False)
    complied = Column(Boolean, nullable=False)  # True=Cumplió, False=No Cumplió
    shift = Column(Enum(AttendanceShift), nullable=False, default=AttendanceShift.AM_PM)

    swimmer = relationship("Swimmer")

    __table_args__ = (UniqueConstraint("swimmer_id", "date", "shift", name="uq_swimmer_date",),)