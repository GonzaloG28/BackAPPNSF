from app.database import SessionLocal
from app.models.import_config import ImportMappingConfig

db = SessionLocal()
db.query(ImportMappingConfig).delete()
db.commit()
print("Configuración eliminada, lista para reconfigurar limpio")