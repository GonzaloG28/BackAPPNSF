# app/models/custom_group.py
from sqlalchemy import Column, Integer, String, JSON, Enum
from sqlalchemy.orm import relationship  # <-- 1. Agrega esta importación
import enum
from app.database import Base

class GroupProfile(str, enum.Enum):
    COMPETITIVE = "COMPETITIVE"
    FORMATIVE = "FORMATIVE"

class CustomGroup(Base):
    __tablename__ = "custom_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    profile = Column(Enum(GroupProfile), nullable=False)
    categories = Column(JSON, nullable=False)  # ["Juvenil A", "Todo Competidor"]

    # <-- 2. AGREGA ESTA RELACIÓN -->
    # Esto le dice a la base de datos: "Si borro este grupo, borra también sus entrenamientos"
    training_sessions = relationship(
        "TrainingSessions",             
        back_populates="target_group",  
        cascade="all, delete-orphan"
    )