from app.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    conn.execute(text("ALTER TABLE convocatoria_entries ADD COLUMN IF NOT EXISTS is_nt_inscription BOOLEAN DEFAULT false"))
    conn.commit()
print("Migrado")