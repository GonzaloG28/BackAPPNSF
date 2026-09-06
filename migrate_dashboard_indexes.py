# Índices compuestos: la clave real de rendimiento para este endpoint,
# no modelos nuevos. Sin esto, el dashboard hace table scans en tablas grandes.
from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_time_records_swimmer_event ON time_records (swimmer_id, event_type_id, recorded_date DESC)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_attendance_logs_swimmer_date ON attendance_logs (swimmer_id, date DESC)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_gym_records_swimmer_exercise ON gym_records (swimmer_id, exercise_id, recorded_at DESC)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_convocatoria_entries_swimmer ON convocatoria_entries (swimmer_id, selected)"))
    conn.commit()
print("Índices creados")