from sqlalchemy import create_engine, text

RENDER_DATABASE_URL = "postgresql://usuario:password@dpg-xxxxx.oregon-postgres.render.com/basededatos"

engine = create_engine(RENDER_DATABASE_URL)

with engine.connect() as conn:
    # Aquí van, EN ORDEN, todos los comandos SQL que has ido corriendo en tu base local.
    # Ejemplo con los que ya conocemos:

    conn.execute(text("ALTER TABLE time_records ADD COLUMN IF NOT EXISTS location_note VARCHAR(150)"))

    conn.execute(text("""
        DO $$ BEGIN
            CREATE TYPE attendanceshift AS ENUM ('AM', 'PM', 'AM_PM', 'ABSENT');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """))

    # ... y así con cada ALTER TABLE / CREATE TYPE que hayas corrido antes

    conn.commit()

print("Migraciones aplicadas en Render")