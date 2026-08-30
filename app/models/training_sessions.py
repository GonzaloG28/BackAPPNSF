# app/models/training_session.py — versión corregida y completa
from sqlalchemy import Column, Integer, String, Date, Enum, ForeignKey, Text, DateTime, func
from sqlalchemy.orm import relationship
import enum
from app.database import Base
from app.models.custom_group import GroupProfile

class SessionShift(str, enum.Enum):
    AM = "AM"
    PM = "PM"
    GYM = "GYM"

class TargetType(str, enum.Enum):
    CATEGORY = "CATEGORY"
    CUSTOM_GROUP = "CUSTOM_GROUP"

class TrainingSessions(Base):
    __tablename__ = "training_sessions_plan"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    shift = Column(Enum(SessionShift), nullable=False)
    profile = Column(Enum(GroupProfile), nullable=False)
    target_type = Column(Enum(TargetType), nullable=False)
    target_category = Column(String(50), nullable=True)
    target_group_id = Column(Integer, ForeignKey("custom_groups.id"), nullable=True)

    week_number = Column(Integer, nullable=True)
    objective = Column(String(255), nullable=True)
    total_volume_m = Column(Integer, nullable=True)

    warmup_text = Column(Text, nullable=True)
    technique_text = Column(Text, nullable=True)
    work1_text = Column(Text, nullable=True)
    work2_text = Column(Text, nullable=True)
    cooldown_text = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now())

    target_group = relationship("CustomGroup", back_populates="training_sessions")