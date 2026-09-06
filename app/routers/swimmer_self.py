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

MONTH_NAMES_ES = [
    "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def _compute_improvement(records: list) -> dict | None:
    """
    Compara, por cada prueba con al menos 2 marcas, el primer tiempo registrado
    contra el más reciente, y promedia el % de mejora entre todas esas pruebas.
    `records` ya viene ordenado por (event_type_id, recorded_date asc).
    """
    by_event: dict = {}
    for event_type_id, time_seconds, recorded_date in records:
        by_event.setdefault(event_type_id, []).append((recorded_date, float(time_seconds)))

    deltas = []
    earliest_overall = None
    latest_overall = None
    for rows in by_event.values():
        if len(rows) < 2:
            continue
        first_date, first_time = rows[0]
        last_date, last_time = rows[-1]
        deltas.append((first_time - last_time) / first_time * 100)  # positivo = más rápido = mejora
        if earliest_overall is None or first_date < earliest_overall:
            earliest_overall = first_date
        if latest_overall is None or last_date > latest_overall:
            latest_overall = last_date

    if not deltas or earliest_overall is None:
        return None

    avg_pct = sum(deltas) / len(deltas)

    if earliest_overall.year == latest_overall.year and earliest_overall.month == latest_overall.month:
        period_label = MONTH_NAMES_ES[earliest_overall.month]
    elif earliest_overall.year == latest_overall.year:
        period_label = str(earliest_overall.year)
    else:
        years_span = latest_overall.year - earliest_overall.year
        period_label = "el último año" if years_span <= 1 else f"los últimos {years_span} años"

    return {
        "pct": round(avg_pct, 1),
        "period_label": period_label,
        "events_considered": len(deltas),
    }


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
    since_7 = today - timedelta(days=7)
    since_30 = today - timedelta(days=30)
    since_90 = today - timedelta(days=90)

    attendance_30 = db.query(
        func.count(AttendanceLog.id).label("total"),
        func.sum(func.cast(AttendanceLog.complied, db.bind.dialect.name == "postgresql" and __import__("sqlalchemy").Integer or __import__("sqlalchemy").Integer)).label("complied"),
    ).filter(AttendanceLog.swimmer_id == swimmer.id, AttendanceLog.date >= since_30).first()

    # Últimos 7 días — para el widget de impacto rápido ("cumpliste 4/6 días"),
    # que necesita un conteo puntual y no el promedio de 30 días.
    attendance_7 = db.query(
        func.count(AttendanceLog.id).label("total"),
        func.sum(func.cast(AttendanceLog.complied, __import__("sqlalchemy").Integer)).label("complied"),
    ).filter(AttendanceLog.swimmer_id == swimmer.id, AttendanceLog.date >= since_7).first()

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

    # ── 5. Récord del Club (noticia): último récord OPEN (sin distinción de
    # categoría) roto en TODO el club, no solo los del propio nadador — fomenta
    # la cultura de equipo. Lectura directa, sin agregación (ya está materializado
    # por app/services/club_records_engine.py cada vez que se sube un tiempo).
    latest_club_record_row = db.query(ClubRecord).filter(
        ClubRecord.category == "OPEN"
    ).order_by(desc(ClubRecord.achieved_date), desc(ClubRecord.updated_at)).first()

    # ── 6. Mejora de pruebas: primer vs. último tiempo por prueba, promediado ──
    event_history = db.query(
        TimeRecord.event_type_id, TimeRecord.time_seconds, TimeRecord.recorded_date
    ).filter(TimeRecord.swimmer_id == swimmer.id).order_by(
        TimeRecord.event_type_id, TimeRecord.recorded_date.asc()
    ).all()
    improvement = _compute_improvement(event_history)

    latest_club_record = None
    if latest_club_record_row:
        latest_club_record = {
            "event_name": latest_club_record_row.event_type.name,
            "gender": latest_club_record_row.gender.value,
            "pool_length": latest_club_record_row.pool_length,
            "time_seconds": float(latest_club_record_row.time_seconds),
            "swimmer_name": latest_club_record_row.swimmer.full_name,
            "achieved_date": latest_club_record_row.achieved_date.isoformat(),
            "is_mine": latest_club_record_row.swimmer_id == swimmer.id,
        }

    return {
        **base,
        "attendance": {
            "rate_30d": round(attendance_complied / attendance_total * 100, 0) if attendance_total else 0,
            "total_sessions_30d": attendance_total,
            "weekly_trend": weekly_trend,  # 8 enteros, ideal para sparkline
            "last_7d": {
                "complied": attendance_7.complied or 0,
                "total": attendance_7.total or 0,
            },
        },
        "marks_summary": marks_summary,       # resumen liviano; detalle completo vía /swimmer-self/marks/{event_type_id}
        "gym_summary": gym_summary,
        "upcoming_convocatorias": upcoming_convocatorias,
        "latest_club_record": latest_club_record,
        "improvement": improvement,
    }


def _empty_dashboard_payload():
    return {
        "attendance": {"rate_30d": 0, "total_sessions_30d": 0, "weekly_trend": [0] * 8, "last_7d": {"complied": 0, "total": 0}},
        "marks_summary": [], "gym_summary": [], "upcoming_convocatorias": [], "latest_club_record": None,
        "improvement": None,
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