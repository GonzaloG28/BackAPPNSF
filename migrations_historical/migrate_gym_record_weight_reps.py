from app.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    conn.execute(text("ALTER TABLE gym_records ADD COLUMN IF NOT EXISTS weight_kg NUMERIC(6,2)"))
    conn.execute(text("ALTER TABLE gym_records ADD COLUMN IF NOT EXISTS reps INTEGER"))
    conn.commit()
print("Migrado")
