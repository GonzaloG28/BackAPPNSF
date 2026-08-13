# app/models/event_type.py
from sqlalchemy import Column, Integer, String, Enum
import enum

from app.database import Base


class StrokeType(str, enum.Enum):
    FREE = "FREE"
    BACK = "BACK"
    BREAST = "BREAST"
    FLY = "FLY"
    MEDLEY = "MEDLEY"


class EventType(Base):
    __tablename__ = "event_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    distance_m = Column(Integer, nullable=False)
    stroke = Column(Enum(StrokeType), nullable=False)