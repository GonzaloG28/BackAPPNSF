# app/scripts/reset_db_state.py
"""
Reinicia y puebla los datos de UN nadador de prueba con volumen alto,
para probar carga masiva en la UI. No toca otros nadadores.
"""
import random
from datetime import date, timedelta
from app.database import SessionLocal
from app.models.swimmer import Swimmer, SwimmerStatus
from app.models.time_record import TimeRecord, TimeSource
from app.models.attendance_log import AttendanceLog
from app.models.gym_record import GymRecord, Exercise
from app.models.event_type import EventType, StrokeType
from app.models.competition import Competition
from app.models.convocatoria import Convocatoria, ConvocatoriaStatus
from app.models.convocatoria_entry import ConvocatoriaEntry

TEST_SWIMMER_RUT = "11111111-1"  # ajusta al RUT del nadador de prueba


def reset_db_state():
    db = SessionLocal()

    swimmer = db.query(Swimmer).filter(Swimmer.document_id == TEST_SWIMMER_RUT).first()
    if not swimmer:
        swimmer = Swimmer(
            first_name_1="Nadador", last_name_1="DePrueba", document_id=TEST_SWIMMER_RUT,
            birth_date=date(2010, 5, 15), status=SwimmerStatus.ACTIVE,
            category="Juvenil A", payment_active=True,
        )
        db.add(swimmer)
        db.commit()
        db.refresh(swimmer)

    # Limpia datos previos de este nadador (no toca otros)
    db.query(TimeRecord).filter(TimeRecord.swimmer_id == swimmer.id).delete()
    db.query(AttendanceLog).filter(AttendanceLog.swimmer_id == swimmer.id).delete()
    db.query(GymRecord).filter(GymRecord.swimmer_id == swimmer.id).delete()
    db.query(ConvocatoriaEntry).filter(ConvocatoriaEntry.swimmer_id == swimmer.id).delete()
    db.commit()

    # ── Tiempos: 6 pruebas x 8 marcas cada una, evolución realista descendente ──
    events = [(50, StrokeType.FREE), (100, StrokeType.FREE), (200, StrokeType.FREE),
              (50, StrokeType.BACK), (100, StrokeType.BREAST), (200, StrokeType.MEDLEY)]
    for distance, stroke in events:
        et = db.query(EventType).filter(EventType.distance_m == distance, EventType.stroke == stroke).first()
        if not et:
            et = EventType(name=f"{distance}m {stroke.value}", distance_m=distance, stroke=stroke)
            db.add(et); db.commit(); db.refresh(et)

        base_time = distance * 0.7
        for i in range(8):
            improvement = i * random.uniform(0.3, 1.2)
            db.add(TimeRecord(
                swimmer_id=swimmer.id, event_type_id=et.id,
                time_seconds=round(base_time - improvement, 2),
                recorded_date=date.today() - timedelta(days=(8 - i) * 20),
                pool_length=random.choice([25, 50]), source=TimeSource.COMPETITION, is_official=True,
            ))

    # ── Asistencia: últimos 90 días, 85% de cumplimiento ──
    for i in range(90):
        d = date.today() - timedelta(days=i)
        if d.weekday() < 6:  # lunes a sábado
            db.add(AttendanceLog(swimmer_id=swimmer.id, date=d, complied=random.random() < 0.85))

    # ── Gym: 5 ejercicios con progresión de RM ──
    exercise_names = ["Sentadilla", "Press banca", "Peso muerto", "Dominadas", "Press militar"]
    for name in exercise_names:
        ex = db.query(Exercise).filter(Exercise.name == name).first()
        if not ex:
            ex = Exercise(name=name); db.add(ex); db.commit(); db.refresh(ex)
        base_rm = random.uniform(40, 90)
        for i in range(5):
            db.add(GymRecord(swimmer_id=swimmer.id, exercise_id=ex.id, one_rm_kg=round(base_rm + i * 2.5, 1)))

    db.commit()

    # ── Convocatoria confirmada de prueba ──
    comp = Competition(
        name="Copa Regional de Prueba", start_date=date.today() + timedelta(days=15),
        end_date=date.today() + timedelta(days=16), location="Temuco", pool_length=50,
    )
    db.add(comp); db.commit(); db.refresh(comp)

    conv = Convocatoria(competition_id=comp.id, status=ConvocatoriaStatus.CONFIRMED)
    db.add(conv); db.commit(); db.refresh(conv)

    first_event = db.query(EventType).first()
    db.add(ConvocatoriaEntry(
        convocatoria_id=conv.id, swimmer_id=swimmer.id, event_type_id=first_event.id,
        best_time_seconds=32.10, selected=True,
    ))
    db.commit()

    print(f"Nadador de prueba (id={swimmer.id}) poblado con datos completos.")
    db.close()


if __name__ == "__main__":
    reset_db_state()