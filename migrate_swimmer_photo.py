from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text("ALTER TABLE swimmers ADD COLUMN IF NOT EXISTS photo_base64 TEXT"))
    conn.commit()
print("Migrado")