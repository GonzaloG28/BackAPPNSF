from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text("ALTER TABLE time_records ADD COLUMN IF NOT EXISTS pool_length INTEGER"))
    conn.commit()
print("Migrado")