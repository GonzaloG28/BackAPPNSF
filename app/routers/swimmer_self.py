# app/routers/swimmer_self.py — reemplaza get_own_profile por esta versión completa
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import date, timedelta

from app.core.deps import get_db, get_current_swimmer
from app.models.swimmer import Swimmer
from app.models.time_record import TimeRecord
from app.models.attendance_log import AttendanceLog, AttendanceShift
from app.models.gym_record import GymRecord
from app.models.convocatoria import Convocatoria, ConvocatoriaStatus
from app.models.convocatoria_entry import ConvocatoriaEntry
from app.models.test_battery import TestBattery
from app.models.test_battery_result import TestBatteryResult
from app.models.club_record import ClubRecord
from app.models.app_update_note import AppUpdateNote

router = APIRouter(prefix="/swimmer-self", tags=["swimmer-self"])


def _shift_label(day_logs) -> tuple[str | None, int]:
    """level: 0 = nada, 1 = una jornada (AM o PM), 2 = AM+PM."""
    if not day_logs:
        return None, 0
    am_pm = any(l.shift == AttendanceShift.AM_PM and l.complied for l in day_logs)
    am = any(l.shift == AttendanceShift.AM and l.complied for l in day_logs)
    pm = any(l.shift == AttendanceShift.PM and l.complied for l in day_logs)
    if am_pm or (am and pm):
        return "AM_PM", 2
    if am:
        return "AM", 1
    if pm:
        return "PM", 1
    return None, 0


def _attendance_history(db: Session, swimmer_id: int, days: int) -> list[dict]:
    """Historial de asistencia de los últimos `days` días terminando AYER,
    en una sola consulta (antes se hacía una consulta por día en un loop)."""
    today = date.today()
    since = today - timedelta(days=days)
    logs = db.query(AttendanceLog).filter(
        AttendanceLog.swimmer_id == swimmer_id, AttendanceLog.date >= since, AttendanceLog.date < today,
    ).all()
    by_day: dict = {}
    for l in logs:
        by_day.setdefault(l.date, []).append(l)

    history = []
    for i in range(days, 0, -1):
        d = today - timedelta(days=i)
        shift_label, level = _shift_label(by_day.get(d, []))
        history.append({"date": d.isoformat(), "shift": shift_label, "level": level})
    return history

MONTH_NAMES_ES = [
    "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def _compute_improvement(records: list) -> dict | None:
    """
    Compara, por cada prueba con al menos 2 marcas, el primer tiempo registrado
    contra el más reciente, y promedia el % de mejora entre todas esas pruebas.
    `records` ya viene ordenado por (event_type_id, recorded_date asc).
    También arma `trend`: cada marca posterior a la primera de su prueba,
    expresada como % de mejora vs. esa primera marca — para graficar.
    """
    by_event: dict = {}
    for event_type_id, time_seconds, recorded_date in records:
        by_event.setdefault(event_type_id, []).append((recorded_date, float(time_seconds)))

    deltas = []
    trend_points = []
    earliest_overall = None
    latest_overall = None
    for rows in by_event.values():
        if len(rows) < 2:
            continue
        first_date, first_time = rows[0]
        last_date, last_time = rows[-1]
        deltas.append((first_time - last_time) / first_time * 100)  # positivo = más rápido = mejora
        for d, t in rows[1:]:
            trend_points.append((d, (first_time - t) / first_time * 100))
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

    trend_points.sort(key=lambda x: x[0])

    return {
        "pct": round(avg_pct, 1),
        "period_label": period_label,
        "events_considered": len(deltas),
        "trend": [{"date": d.isoformat(), "pct": round(p, 1)} for d, p in trend_points[-10:]],
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

    # Los 30 días ANTERIORES a los últimos 30 (día 31 a 60 atrás) — para saber
    # si la asistencia mejoró o empeoró vs. el mes previo, no solo el número suelto.
    since_60 = today - timedelta(days=60)
    attendance_prev_30 = db.query(
        func.count(AttendanceLog.id).label("total"),
        func.sum(func.cast(AttendanceLog.complied, __import__("sqlalchemy").Integer)).label("complied"),
    ).filter(
        AttendanceLog.swimmer_id == swimmer.id,
        AttendanceLog.date >= since_60, AttendanceLog.date < since_30,
    ).first()

    # Últimos 7 días — para el widget de impacto rápido ("cumpliste 4/6 días"),
    # que necesita un conteo puntual y no el promedio de 30 días.
    attendance_7 = db.query(
        func.count(AttendanceLog.id).label("total"),
        func.sum(func.cast(AttendanceLog.complied, __import__("sqlalchemy").Integer)).label("complied"),
    ).filter(AttendanceLog.swimmer_id == swimmer.id, AttendanceLog.date >= since_7).first()

    attendance_total = attendance_30.total or 0
    attendance_complied = attendance_30.complied or 0

    # Tendencia diaria: 8 días terminando AYER (no hoy, que casi siempre está
    # vacío) — cada día indica la JORNADA asistida (AM, PM o AM+PM), no solo
    # un booleano, para que el gráfico de barras distinga media jornada de
    # jornada completa.
    daily_trend = _attendance_history(db, swimmer.id, 8)

    # Últimos 6 días día por día (cumplió / no cumplió / sin sesión) — para el
    # checklist visual del dashboard, no solo el agregado 4/6.
    last_6_days = []
    for i in range(5, -1, -1):
        d = today - timedelta(days=i)
        day_logs = db.query(AttendanceLog).filter(
            AttendanceLog.swimmer_id == swimmer.id, AttendanceLog.date == d
        ).all()
        complied = any(l.complied for l in day_logs) if day_logs else None
        last_6_days.append({"date": d.isoformat(), "complied": complied})

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
        {
            "exercise_id": g.exercise_id, "exercise_name": g.exercise.name, "one_rm_kg": float(g.one_rm_kg),
            "weight_kg": float(g.weight_kg) if g.weight_kg is not None else None,
            "reps": g.reps,
        }
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

    # ── 5. Récords del Club (noticia): los últimos 3 rotos en TODO el club —
    # cualquier categoría, no solo los del propio nadador — fomenta la
    # cultura de equipo. Lectura directa, sin agregación (ya está materializado
    # por app/services/club_records_engine.py cada vez que se sube un tiempo).
    recent_club_record_rows = db.query(ClubRecord).order_by(
        desc(ClubRecord.achieved_date), desc(ClubRecord.updated_at)
    ).limit(3).all()

    # ── 5b. Últimas 3 marcas registradas (cualquier prueba) — para el rotador. ──
    recent_marks_rows = db.query(TimeRecord).filter(
        TimeRecord.swimmer_id == swimmer.id
    ).order_by(TimeRecord.recorded_date.desc()).limit(3).all()
    recent_marks = [
        {
            "event_name": r.event_type.name,
            "time_seconds": float(r.time_seconds),
            "recorded_date": r.recorded_date.isoformat(),
        }
        for r in recent_marks_rows
    ]

    # ── 6. Mejora de pruebas: primer vs. último tiempo por prueba, promediado ──
    event_history = db.query(
        TimeRecord.event_type_id, TimeRecord.time_seconds, TimeRecord.recorded_date
    ).filter(TimeRecord.swimmer_id == swimmer.id).order_by(
        TimeRecord.event_type_id, TimeRecord.recorded_date.asc()
    ).all()
    improvement = _compute_improvement(event_history)

    recent_club_records = [
        {
            "event_name": r.event_type.name,
            "gender": r.gender.value,
            "pool_length": r.pool_length,
            "time_seconds": float(r.time_seconds),
            "swimmer_name": r.swimmer.full_name,
            "achieved_date": r.achieved_date.isoformat(),
            "is_mine": r.swimmer_id == swimmer.id,
        }
        for r in recent_club_record_rows
    ]

    rate_30d = round(attendance_complied / attendance_total * 100, 0) if attendance_total else 0
    prev_30_total = attendance_prev_30.total or 0
    prev_30_complied = attendance_prev_30.complied or 0
    rate_prev_30d = round(prev_30_complied / prev_30_total * 100, 0) if prev_30_total else None
    attendance_trend_cmp = None
    if rate_prev_30d is not None:
        delta = rate_30d - rate_prev_30d
        attendance_trend_cmp = {
            "current_rate": rate_30d, "previous_rate": rate_prev_30d,
            "delta": round(delta, 0), "improved": delta >= 0,
        }

    return {
        **base,
        "attendance": {
            "rate_30d": rate_30d,
            "total_sessions_30d": attendance_total,
            "daily_trend": daily_trend,  # 8 días con fecha, terminando ayer
            "last_7d": {
                "complied": attendance_7.complied or 0,
                "total": attendance_7.total or 0,
            },
            "last_6_days": last_6_days,
            "trend": attendance_trend_cmp,  # None si no hay historial del mes previo para comparar
        },
        "marks_summary": marks_summary,       # resumen liviano; detalle completo vía /swimmer-self/marks/{event_type_id}
        "recent_marks": recent_marks,
        "gym_summary": gym_summary,
        "upcoming_convocatorias": upcoming_convocatorias,
        "recent_club_records": recent_club_records,
        "improvement": improvement,
    }


def _empty_dashboard_payload():
    return {
        "attendance": {"rate_30d": 0, "total_sessions_30d": 0, "daily_trend": [], "last_7d": {"complied": 0, "total": 0}, "last_6_days": [], "trend": None},
        "marks_summary": [], "recent_marks": [], "gym_summary": [], "upcoming_convocatorias": [], "recent_club_records": [],
        "improvement": None,
    }


@router.get("/attendance/history")
def get_attendance_history(days: int = 30, swimmer: Swimmer = Depends(get_current_swimmer), db: Session = Depends(get_db)):
    """Historial de asistencia de un rango arbitrario (5, 30 días, etc.) —
    se pide bajo demanda desde la pantalla de Asistencia, no en el
    dashboard inicial (que solo trae los últimos 8 días)."""
    if not swimmer.payment_active:
        return {"history": [], "rate": 0, "total_sessions": 0}
    days = max(1, min(days, 90))
    history = _attendance_history(db, swimmer.id, days)
    total_sessions = sum(1 for h in history if h["level"] > 0)
    rate = round(total_sessions / days * 100, 0) if days else 0
    return {"history": history, "rate": rate, "total_sessions": total_sessions}


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
    return [
        {
            "date": r.recorded_at.isoformat(), "one_rm_kg": float(r.one_rm_kg),
            "weight_kg": float(r.weight_kg) if r.weight_kg is not None else None,
            "reps": r.reps,
        }
        for r in records
    ]


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


@router.get("/updates")
def get_app_updates(swimmer: Swimmer = Depends(get_current_swimmer), db: Session = Depends(get_db)):
    """Novedades de la app — a diferencia del resto de este router, no se paywallea:
    un aviso de "qué cambió" debe verse aunque la membresía esté vencida."""
    notes = db.query(AppUpdateNote).filter(
        AppUpdateNote.audience.in_(["SWIMMERS", "ALL"])
    ).order_by(AppUpdateNote.created_at.desc()).limit(20).all()
    return [
        {"id": n.id, "title": n.title, "body": n.body, "created_at": n.created_at.isoformat() if n.created_at else None}
        for n in notes
    ]


@router.get("/club-records")
def get_my_club_records(swimmer: Swimmer = Depends(get_current_swimmer), db: Session = Depends(get_db)):
    """Todos los récords vigentes del club (cualquier categoría/nadador) —
    antes filtraba solo los del propio nadador, lo que dejaba la pantalla
    vacía para casi todos. `is_mine` marca los propios para destacarlos."""
    if not swimmer.payment_active:
        return []
    records = db.query(ClubRecord).order_by(
        desc(ClubRecord.achieved_date), desc(ClubRecord.updated_at)
    ).all()
    return [
        {
            "event_type_id": r.event_type_id,
            "event_name": r.event_type.name,
            "category": r.category,
            "gender": r.gender.value,
            "pool_length": r.pool_length,
            "time_seconds": float(r.time_seconds),
            "swimmer_name": r.swimmer.full_name,
            "achieved_date": r.achieved_date.isoformat(),
            "is_mine": r.swimmer_id == swimmer.id,
        }
        for r in records
    ]


CATEGORY_LABEL_ES = {
    "COMPETITIVE": "Competitivo", "FORMATIVE": "Formativo",
}
GENDER_LABEL_ES = {"MALE": "Masculino", "FEMALE": "Femenino"}
STATUS_LABEL_ES = {"ACTIVE": "Activo", "FROZEN": "Congelado", "DELETED": "Eliminado"}


@router.get("/profile")
def get_my_profile(swimmer: Swimmer = Depends(get_current_swimmer)):
    """Ficha completa del nadador para el panel de "Mi perfil" — a diferencia
    de /dashboard (que solo trae lo mínimo para las cards), esto trae todos
    los datos personales, sin paywall (ver los propios datos no depende de
    la membresía)."""
    return {
        "id": swimmer.id,
        "first_name_1": swimmer.first_name_1, "first_name_2": swimmer.first_name_2,
        "last_name_1": swimmer.last_name_1, "last_name_2": swimmer.last_name_2,
        "full_name": swimmer.full_name,
        "document_id": swimmer.document_id,
        "birth_date": swimmer.birth_date.isoformat() if swimmer.birth_date else None,
        "gender": swimmer.gender.value if swimmer.gender else None,
        "gender_label": GENDER_LABEL_ES.get(swimmer.gender.value) if swimmer.gender else None,
        "category": swimmer.category,
        "profile": swimmer.profile.value if swimmer.profile else None,
        "profile_label": CATEGORY_LABEL_ES.get(swimmer.profile.value) if swimmer.profile else None,
        "comuna": swimmer.comuna,
        "institution": swimmer.institution,
        "phone": swimmer.phone,
        "email": swimmer.email,
        "is_federated": swimmer.is_federated,
        "status": swimmer.status.value,
        "status_label": STATUS_LABEL_ES.get(swimmer.status.value),
        "payment_active": swimmer.payment_active,
        "has_photo": swimmer.has_photo,
    }


class SwimmerContactUpdate(BaseModel):
    email: str | None = None
    phone: str | None = None


@router.patch("/profile")
def update_my_contact(
    payload: SwimmerContactUpdate,
    swimmer: Swimmer = Depends(get_current_swimmer),
    db: Session = Depends(get_db),
):
    """El nadador solo puede editar SU correo y teléfono — el resto de la
    ficha (nombre, RUT, categoría, etc.) lo administra el profesor."""
    if payload.email is not None:
        swimmer.email = payload.email.strip() or None
    if payload.phone is not None:
        swimmer.phone = payload.phone.strip() or None
    db.commit()
    db.refresh(swimmer)
    return {"email": swimmer.email, "phone": swimmer.phone}