# app/models/import_config.py
from sqlalchemy import Column, Integer, String, JSON, DateTime, func

from app.database import Base


class ImportMappingConfig(Base):
    __tablename__ = "import_mapping_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, default="Plantilla principal")
    mapping = Column(JSON, nullable=False)
    sample_file_name = Column(String(255), nullable=True)
    sample_file_path = Column(String(500), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())