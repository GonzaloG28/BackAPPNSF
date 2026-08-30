from app.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    conn.execute(text("""
        DO $$ BEGIN
            CREATE TYPE swimmershift AS ENUM ('AM', 'PM', 'AM_PM');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """))
    conn.execute(text("ALTER TABLE swimmers ADD COLUMN IF NOT EXISTS schedule_shift swimmershift"))
    conn.commit()
print("Migrado")