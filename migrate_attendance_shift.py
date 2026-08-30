from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # 1. Crear el tipo ENUM de Postgres para el shift (si no existe)
    conn.execute(text("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'attendanceshift') THEN
                CREATE TYPE attendanceshift AS ENUM ('AM', 'PM', 'AM_PM');
            END IF;
        END $$;
    """))

    # 2. Agregar la columna permitiendo nulos temporalmente
    conn.execute(text("ALTER TABLE attendance_logs ADD COLUMN IF NOT EXISTS shift attendanceshift;"))

    # 3. Llenar los registros existentes con el valor por defecto
    #    (AM_PM = compatibilidad hacia atrás, registros previos a este cambio)
    conn.execute(text("UPDATE attendance_logs SET shift = 'AM_PM' WHERE shift IS NULL;"))

    # 4. Forzar que la columna no sea nula
    conn.execute(text("ALTER TABLE attendance_logs ALTER COLUMN shift SET NOT NULL;"))

    # 5. Eliminar la restricción única antigua sobre (swimmer_id, date)
    #    Ajusta el nombre si en tu base tiene otro (revisa con \d attendance_logs en psql)
    conn.execute(text("ALTER TABLE attendance_logs DROP CONSTRAINT IF EXISTS uq_swimmer_date;"))
    conn.execute(text("ALTER TABLE attendance_logs DROP CONSTRAINT IF EXISTS uq_attendance_swimmer_date;"))
    conn.execute(text("ALTER TABLE attendance_logs DROP CONSTRAINT IF EXISTS attendance_logs_swimmer_id_date_key;"))

    # 6. Agregar la nueva restricción única compuesta (swimmer_id, date, shift)
    #    Mismo nombre que usa el modelo: uq_swimmer_date
    conn.execute(text("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'uq_swimmer_date'
            ) THEN
                ALTER TABLE attendance_logs ADD CONSTRAINT uq_swimmer_date UNIQUE (swimmer_id, date, shift);
            END IF;
        END $$;
    """))

    conn.commit()

print("Migrado")
