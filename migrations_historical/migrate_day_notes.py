from app.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    conn.execute(text("ALTER TABLE day_notes ADD COLUMN IF NOT EXISTS profile VARCHAR(20) DEFAULT 'COMPETITIVE'"))
    conn.execute(text("ALTER TABLE day_notes ADD COLUMN IF NOT EXISTS category VARCHAR(50) DEFAULT 'General'"))
    conn.commit()
print("Migrado")