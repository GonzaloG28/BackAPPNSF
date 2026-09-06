from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Agrega la columna split_increment como INTEGER para coincidir con tu esquema Pydantic
    conn.execute(text("ALTER TABLE time_records ADD COLUMN IF NOT EXISTS split_increment INTEGER"))
    conn.commit()

print("Columna split_increment migrada con éxito")