# scripts/seed_ghost_swimmer.py
#
# Crea (o actualiza) el nadador de pruebas "fantasma" — RUT 12345678-9 —
# con perfil 100% completo y al menos 2 marcas históricas en cada prueba
# oficial del sistema, para QA de features nuevas sin ensuciar el roster
# real (exclude_from_roster=True lo saca de los conteos del entrenador).
#
# Uso: venv/Scripts/python.exe scripts/seed_ghost_swimmer.py
import base64
from datetime import date, timedelta
from decimal import Decimal

from app.database import SessionLocal
from app.core.security import hash_password
from app.models.attendance_log import AttendanceLog, AttendanceShift
from app.models.event_type import EventType
from app.models.gym_record import Exercise, GymRecord
from app.models.swimmer import Swimmer, SwimmerGender, SwimmerProfile, SwimmerStatus
from app.models.swimmer_metric import SwimmerMetric
from app.models.time_record import TimeRecord, TimeSource
from app.utils.rut_auth import rut_default_password

GHOST_RUT = "12345678-9"

# PNG 1x1 naranjo — placeholder mínimo, real (no un string vacío) para que
# has_photo=True y la UI de foto de perfil tenga algo real que renderizar.
GHOST_PHOTO_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP6z8DwHwAFAAH/"
    "q3+AjwAAAABJRU5ErkJggg=="
)

# Tiempo base aproximado (segundos) por prueba, para un nadador competitivo
# adulto de nivel medio — solo necesita ser realista, no exacto.
BASE_TIME_SECONDS = {
    ("50m Libre", 50): 26.5, ("50m Espalda", 50): 30.0, ("50m Pecho", 50): 33.0, ("50m Mariposa", 50): 29.0,
    ("100m Libre", 100): 58.0, ("100m Espalda", 100): 65.0, ("100m Pecho", 100): 72.0,
    ("100m Mariposa", 100): 63.0, ("100m Combinado", 100): 66.0,
    ("200m Libre", 200): 125.0, ("200m Espalda", 200): 140.0, ("200m Pecho", 200): 155.0,
    ("200m Mariposa", 200): 135.0, ("200m Combinado", 200): 142.0,
    ("400m Libre", 400): 270.0, ("400m Combinado", 400): 300.0,
    ("800m Libre", 800): 560.0, ("1500m Libre", 1500): 1080.0,
}


def run():
    db = SessionLocal()
    try:
        swimmer = db.query(Swimmer).filter(Swimmer.document_id == GHOST_RUT).first()
        if not swimmer:
            swimmer = Swimmer(document_id=GHOST_RUT)
            db.add(swimmer)

        swimmer.first_name_1 = "Fantasma"
        swimmer.first_name_2 = "QA"
        swimmer.last_name_1 = "Testing"
        swimmer.last_name_2 = "Sistema"
        swimmer.birth_date = date(2005, 3, 15)
        swimmer.gender = SwimmerGender.MALE
        swimmer.category = "Todo Competidor"
        swimmer.comuna = "Temuco"
        swimmer.institution = "QA Test Club"
        swimmer.phone = "+56900000000"
        swimmer.email = "fantasma.qa@test.local"
        swimmer.profile = SwimmerProfile.COMPETITIVE
        swimmer.is_federated = True
        swimmer.status = SwimmerStatus.ACTIVE
        swimmer.payment_active = True
        swimmer.must_change_password = False
        swimmer.hashed_password = hash_password(rut_default_password(GHOST_RUT))
        swimmer.photo_base64 = GHOST_PHOTO_B64
        swimmer.exclude_from_roster = True
        db.flush()

        # ── Biometría ──────────────────────────────────────────────
        db.query(SwimmerMetric).filter(SwimmerMetric.swimmer_id == swimmer.id).delete()
        db.add(SwimmerMetric(
            swimmer_id=swimmer.id, recorded_at=date.today() - timedelta(days=30),
            weight_kg=72.0, height_cm=178.0, wingspan_cm=182.0, notes="Medición QA inicial",
        ))
        db.add(SwimmerMetric(
            swimmer_id=swimmer.id, recorded_at=date.today(),
            weight_kg=73.5, height_cm=178.0, wingspan_cm=182.0, notes="Medición QA reciente",
        ))

        # ── Marcas: 2+ por CADA prueba existente en el sistema ──────
        db.query(TimeRecord).filter(TimeRecord.swimmer_id == swimmer.id).delete()
        events = db.query(EventType).all()
        older_date = date.today() - timedelta(days=180)
        newer_date = date.today() - timedelta(days=14)
        for event in events:
            base = BASE_TIME_SECONDS.get((event.name, event.distance_m), event.distance_m * 0.55)
            # Marca antigua más lenta, marca reciente mejorada — patrón real de progreso.
            db.add(TimeRecord(
                swimmer_id=swimmer.id, event_type_id=event.id,
                time_seconds=Decimal(str(round(base * 1.03, 2))),
                recorded_date=older_date, source=TimeSource.COMPETITION,
                is_official=True, pool_length=50,
            ))
            db.add(TimeRecord(
                swimmer_id=swimmer.id, event_type_id=event.id,
                time_seconds=Decimal(str(round(base * 0.985, 2))),
                recorded_date=newer_date, source=TimeSource.COMPETITION,
                is_official=True, pool_length=50,
            ))

        # ── Asistencia: últimos 10 días, mayormente cumplida ────────
        db.query(AttendanceLog).filter(AttendanceLog.swimmer_id == swimmer.id).delete()
        for i in range(10, 0, -1):
            d = date.today() - timedelta(days=i)
            db.add(AttendanceLog(
                swimmer_id=swimmer.id, date=d, complied=(i % 4 != 0), shift=AttendanceShift.AM_PM,
            ))

        # ── Gimnasio: RM en los ejercicios ya existentes ────────────
        db.query(GymRecord).filter(GymRecord.swimmer_id == swimmer.id).delete()
        exercises = db.query(Exercise).all()
        base_rm = {"sentadilla": 90.0, "Press Banco con mancuernas": 60.0, "Peso muerto": 110.0}
        for ex in exercises:
            rm = base_rm.get(ex.name.strip(), 80.0)
            db.add(GymRecord(swimmer_id=swimmer.id, exercise_id=ex.id, one_rm_kg=Decimal(str(rm - 5))))
            db.add(GymRecord(swimmer_id=swimmer.id, exercise_id=ex.id, one_rm_kg=Decimal(str(rm))))

        db.commit()
        print(f"OK: nadador fantasma listo (id={swimmer.id}, RUT={swimmer.document_id}, "
              f"{len(events)} pruebas x2 marcas = {len(events) * 2} TimeRecord).")
    finally:
        db.close()


if __name__ == "__main__":
    run()
