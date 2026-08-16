from app.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    conn.execute(text("ALTER TABLE convocatoria_entries ADD COLUMN IF NOT EXISTS time_record_id INTEGER"))
    conn.commit()
print("Migrado")