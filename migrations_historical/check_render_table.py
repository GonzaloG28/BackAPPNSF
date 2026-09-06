from sqlalchemy import create_engine, text

RENDER_URL = "postgresql://usuario:password@dpg-xxxxx.oregon-postgres.render.com/basededatos"
engine = create_engine(RENDER_URL)

with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM import_mapping_configs"))
    rows = result.fetchall()
    print(f"Filas encontradas: {len(rows)}")
    for r in rows:
        print(r)