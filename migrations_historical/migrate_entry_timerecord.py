from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # 1. Agregar las nuevas columnas permitiendo nulos temporalmente
    conn.execute(text("ALTER TABLE day_notes ADD COLUMN IF NOT EXISTS profile VARCHAR;"))
    conn.execute(text("ALTER TABLE day_notes ADD COLUMN IF NOT EXISTS category VARCHAR;"))

    # 2. Llenar los registros existentes con un valor por defecto
    conn.execute(text("UPDATE day_notes SET profile = 'FORMATIVE' WHERE profile IS NULL;"))
    conn.execute(text("UPDATE day_notes SET category = 'General' WHERE category IS NULL;"))

    # 3. Forzar que las columnas no sean nulas
    conn.execute(text("ALTER TABLE day_notes ALTER COLUMN profile SET NOT NULL;"))
    conn.execute(text("ALTER TABLE day_notes ALTER COLUMN category SET NOT NULL;"))

    # 4. Eliminar la restricción única antigua de la columna 'date'
    conn.execute(text("ALTER TABLE day_notes DROP CONSTRAINT IF EXISTS day_notes_date_key;"))

    # 5. Agregar la nueva restricción única compuesta (date, profile, category)
    conn.execute(text("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 
                FROM pg_constraint 
                WHERE conname = 'uix_day_note_profile_cat'
            ) THEN
                ALTER TABLE day_notes ADD CONSTRAINT uix_day_note_profile_cat UNIQUE (date, profile, category);
            END IF;
        END $$;
    """))

    conn.commit()

print("Migrado")