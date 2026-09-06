from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text("ALTER TABLE swimmers ADD COLUMN IF NOT EXISTS hashed_password VARCHAR(255)"))
    conn.execute(text("ALTER TABLE swimmers ADD COLUMN IF NOT EXISTS must_change_password BOOLEAN NOT NULL DEFAULT true"))
    conn.execute(text("ALTER TABLE swimmers ADD COLUMN IF NOT EXISTS payment_active BOOLEAN NOT NULL DEFAULT false"))
    conn.commit()
print("Migrado")