# app/routers/swimmer_self.py — reemplaza get_own_profile por esta versión completa
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import date, timedelta

from app.core.deps import get_db, get_current_swimmer
from app.models.swimmer import Swimmer
from app.models.time_record import TimeRecord
from app.models.attendance_log import AttendanceLog
from app.models.gym_record import GymRecord
from app.models.convocatoria import Convocatoria, ConvocatoriaStatus
from app.models.convocatoria_entry import ConvocatoriaEntry
from app.models.test_battery import TestBattery
from app.models.test_battery_result import TestBatteryResult
from app.models.club_record import ClubRecord

router = APIRouter(prefix="/swimmer-self", tags=["swimmer-self"])


@router.get("/dashboard")
def get_dashboard(swimmer: Swimmer = Depends(get_current_swimmer), db: Session = Depends(get_db)):
    is_paid = swimmer.payment_active

    # ── God Mode: si viene inyectado por el middleware de testing, se ignora el paywall ──
    # (ver PARTE 3 del testing: el interceptor setea swimmer.payment_active=True en memoria
    #  antes de llegar aquí, así que este endpoint no necesita saber nada de "modo pruebas")

    base = {
        "id": swimmer.id, "full_name": swimmer.full_name, "category": swimmer.category,
        "status": swimmer.status.value, "is_federated": swimmer.is_federated,
        "payment_active": is_paid, "has_photo": swimmer.photo_base64 is not None,
    }

    if not is_paid:
        return {**base, **_empty_dashboard_payload()}

    # ── 1. Asistencia: agregado en SQL, no traemos filas individuales ──
    today = date.today()
    since_30 = today - timedelta(days=30)
    since_90 = today - timedelta(days=90)

    attendance_30 = db.query(
        func.count(AttendanceLog.id).label("total"),
        func.sum(func.cast(AttendanceLog.complied, db.bind.dialect.name == "postgresql" and __import__("sqlalchemy").Integer or __import__("sqlalchemy").Integer)).label("complied"),
    ).filter(AttendanceLog.swimmer_id == swimmer.id, AttendanceLog.date >= since_30).first()

    # Tendencia semanal (últimas 8 semanas) — 8 números, no 8 semanas de filas crudas
    weekly_trend = []
    for i in range(7, -1, -1):
        week_start = today - timedelta(days=today.weekday() + i * 7)
        week_end = week_start + timedelta(days=6)
        week_logs = db.query(AttendanceLog).filter(
            AttendanceLog.swimmer_id == swimmer.id,
            AttendanceLog.date >= week_start, AttendanceLog.date <= week_end,
        ).all()
        rate = round(sum(1 for l in week_logs if l.complied) / len(week_logs) * 100, 0) if week_logs else 0
        weekly_trend.append(int(rate))

    attendance_total = attendance_30.total or 0
    attendance_complied = attendance_30.complied or 0

    # ── 2. Métricas/Marcas: solo el resumen por prueba (mejor tiempo + cantidad), no el historial completo ──
    best_per_event = db.query(
        TimeRecord.event_type_id,
        func.min(TimeRecord.time_seconds).label("best_time"),
        func.count(TimeRecord.id).label("total_marks"),
    ).filter(TimeRecord.swimmer_id == swimmer.id).group_by(TimeRecord.event_type_id).all()

    from app.models.event_type import EventType
    event_names = {et.id: et.name for et in db.query(EventType).filter(
        EventType.id.in_([r.event_type_id for r in best_per_event])
    ).all()} if best_per_event else {}

    marks_summary = [
        {
            "event_type_id": r.event_type_id,
            "event_name": event_names.get(r.event_type_id, "—"),
            "best_time": float(r.best_time),
            "total_marks": r.total_marks,
        }
        for r in best_per_event
    ]

    # ── 3. Gym: último RM por ejercicio (no el historial completo) ──
    latest_gym_subquery = db.query(
        GymRecord.exercise_id, func.max(GymRecord.recorded_at).label("max_date")
    ).filter(GymRecord.swimmer_id == swimmer.id).group_by(GymRecord.exercise_id).subquery()

    latest_gym = db.query(GymRecord).join(
        latest_gym_subquery,
        (GymRecord.exercise_id == latest_gym_subquery.c.exercise_id) &
        (GymRecord.recorded_at == latest_gym_subquery.c.max_date)
    ).filter(GymRecord.swimmer_id == swimmer.id).all()

    gym_summary = [
        {"exercise_id": g.exercise_id, "exercise_name": g.exercise.name, "one_rm_kg": float(g.one_rm_kg)}
        for g in latest_gym
    ]

    # ── 4. Convocatorias: SOLO confirmadas, solo entries seleccionadas de este nadador ──
    confirmed_entries = db.query(ConvocatoriaEntry).join(Convocatoria).filter(
        ConvocatoriaEntry.swimmer_id == swimmer.id,
        ConvocatoriaEntry.selected == True,
        Convocatoria.status.in_([ConvocatoriaStatus.CONFIRMED, ConvocatoriaStatus.EXPORTED]),  # is_confirmed_by_coach
        Convocatoria.competition.has(),  # asegura join válido
    ).all()

    convocatorias_by_id: dict = {}
    for e in confirmed_entries:
        comp = e.convocatoria.competition
        cid = e.convocatoria.id
        if cid not in convocatorias_by_id:
            convocatorias_by_id[cid] = {
                "convocatoria_id": cid, "competition_name": comp.name,
                "start_date": comp.start_date.isoformat(), "end_date": comp.end_date.isoformat(),
                "location": comp.location, "events": [],
            }
        convocatorias_by_id[cid]["events"].append({
            "event_name": e.event_type.name,
            "inscription_time": float(e.best_time_seconds) if e.best_time_seconds is not None else "NT",
        })

    upcoming_convocatorias = sorted(convocatorias_by_id.values(), key=lambda c: c["start_date"])

    return {
        **base,
        "attendance": {
            "rate_30d": round(attendance_complied / attendance_total * 100, 0) if attendance_total else 0,
            "total_sessions_30d": attendance_total,
            "weekly_trend": weekly_trend,  # 8 enteros, ideal para sparkline
        },
        "marks_summary": marks_summary,       # resumen liviano; detalle completo vía /swimmer-self/marks/{event_type_id}
        "gym_summary": gym_summary,
        "upcoming_convocatorias": upcoming_convocatorias,
    }


def _empty_dashboard_payload():
    return {
        "attendance": {"rate_30d": 0, "total_sessions_30d": 0, "weekly_trend": [0] * 8},
        "marks_summary": [], "gym_summary": [], "upcoming_convocatorias": [],
    }


@router.get("/marks/{event_type_id}")
def get_marks_detail(event_type_id: int, swimmer: Swimmer = Depends(get_current_swimmer), db: Session = Depends(get_db)):
    """Historial completo de UNA prueba — se pide bajo demanda, no en el dashboard inicial."""
    if not swimmer.payment_active:
        return []
    records = db.query(TimeRecord).filter(
        TimeRecord.swimmer_id == swimmer.id, TimeRecord.event_type_id == event_type_id
    ).order_by(TimeRecord.recorded_date.asc()).all()
    return [{"date": r.recorded_date.isoformat(), "time_seconds": float(r.time_seconds), "pool_length": r.pool_length} for r in records]



# app/routers/swimmer_self.py — agrega
@router.get("/gym/{exercise_id}/history")
def get_gym_history_detail(exercise_id: int, swimmer: Swimmer = Depends(get_current_swimmer), db: Session = Depends(get_db)):
    if not swimmer.payment_active:
        return []
    records = db.query(GymRecord).filter(
        GymRecord.swimmer_id == swimmer.id, GymRecord.exercise_id == exercise_id
    ).order_by(GymRecord.recorded_at.asc()).all()
    return [{"date": r.recorded_at.isoformat(), "one_rm_kg": float(r.one_rm_kg)} for r in records]


@router.get("/test-batteries")
def get_my_test_batteries(swimmer: Swimmer = Depends(get_current_swimmer), db: Session = Depends(get_db)):
    """Mejor marca + cantidad de registros por batería, mismo patrón que marks_summary del dashboard."""
    if not swimmer.payment_active:
        return []
    best_per_battery = db.query(
        TestBatteryResult.battery_id,
        func.min(TestBatteryResult.value_seconds).label("best_time"),
        func.count(TestBatteryResult.id).label("total_results"),
    ).filter(TestBatteryResult.swimmer_id == swimmer.id).group_by(TestBatteryResult.battery_id).all()

    if not best_per_battery:
        return []

    batteries = {
        b.id: b for b in db.query(TestBattery).filter(
            TestBattery.id.in_([r.battery_id for r in best_per_battery])
        ).all()
    }

    return [
        {
            "battery_id": r.battery_id,
            "battery_name": batteries[r.battery_id].name if r.battery_id in batteries else "—",
            "best_time_seconds": float(r.best_time) if r.best_time is not None else None,
            "total_results": r.total_results,
        }
        for r in best_per_battery
    ]


@router.get("/test-batteries/{battery_id}/history")
def get_my_test_battery_history(battery_id: int, swimmer: Swimmer = Depends(get_current_swimmer), db: Session = Depends(get_db)):
    if not swimmer.payment_active:
        return []
    results = db.query(TestBatteryResult).filter(
        TestBatteryResult.battery_id == battery_id, TestBatteryResult.swimmer_id == swimmer.id
    ).order_by(TestBatteryResult.recorded_date.asc()).all()
    return [
        {
            "date": r.recorded_date.isoformat(),
            "time_seconds": float(r.value_seconds) if r.value_seconds is not None else None,
            "value_reps": r.value_reps,
        }
        for r in results
    ]


@router.get("/club-records")
def get_my_club_records(swimmer: Swimmer = Depends(get_current_swimmer), db: Session = Depends(get_db)):
    """Solo los récords del club que el propio nadador sostiene actualmente."""
    if not swimmer.payment_active:
        return []
    records = db.query(ClubRecord).filter(ClubRecord.swimmer_id == swimmer.id).all()
    return [
        {
            "event_type_id": r.event_type_id,
            "event_name": r.event_type.name,
            "category": r.category,
            "gender": r.gender.value,
            "pool_length": r.pool_length,
            "time_seconds": float(r.time_seconds),
            "achieved_date": r.achieved_date.isoformat(),
        }
        for r in records
    ]