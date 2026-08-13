from sqlalchemy import Column, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class ScheduleShift(str, enum.Enum):
    AM = "AM"
    PM = "PM"
    AM_PM = "AM_PM"
    NONE = "NONE"


class PersonalSchedule(Base):
    __tablename__ = "personal_schedules"

    id = Column(Integer, primary_key=True, index=True)
    swimmer_id = Column(Integer, ForeignKey("swimmers.id"), nullable=False)
    weekday = Column(Integer, nullable=False)
    shift = Column(Enum(ScheduleShift), nullable=False, default=ScheduleShift.NONE)

    swimmer = relationship("Swimmer")