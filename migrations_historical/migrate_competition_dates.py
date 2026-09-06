from app.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    conn.execute(text("ALTER TABLE competitions ADD COLUMN IF NOT EXISTS start_date DATE"))
    conn.execute(text("ALTER TABLE competitions ADD COLUMN IF NOT EXISTS end_date DATE"))
    conn.execute(text("ALTER TABLE competitions ADD COLUMN IF NOT EXISTS categories JSON"))
    conn.execute(text("UPDATE competitions SET start_date = date, end_date = date WHERE start_date IS NULL"))
    conn.commit()
print("Migrado")