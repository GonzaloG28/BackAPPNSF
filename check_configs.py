from app.database import SessionLocal
from app.models.import_config import ImportMappingConfig

db = SessionLocal()
configs = db.query(ImportMappingConfig).all()
print(f"Total de plantillas guardadas: {len(configs)}")
for c in configs:
    print(f"ID {c.id}: {c.mapping}")