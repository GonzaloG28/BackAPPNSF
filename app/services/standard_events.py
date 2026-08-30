# app/services/standard_events.py
from app.models.event_type import EventType, StrokeType

STANDARD_EVENTS = [
    (50, StrokeType.FREE), (100, StrokeType.FREE), (200, StrokeType.FREE),
    (400, StrokeType.FREE), (800, StrokeType.FREE), (1500, StrokeType.FREE),
    (50, StrokeType.BACK), (100, StrokeType.BACK), (200, StrokeType.BACK),
    (50, StrokeType.BREAST), (100, StrokeType.BREAST), (200, StrokeType.BREAST),
    (50, StrokeType.FLY), (100, StrokeType.FLY), (200, StrokeType.FLY),
    (200, StrokeType.MEDLEY), (400, StrokeType.MEDLEY),
]

STROKE_LABELS = {
    StrokeType.FREE: "Libre", StrokeType.BACK: "Espalda", StrokeType.BREAST: "Pecho",
    StrokeType.FLY: "Mariposa", StrokeType.MEDLEY: "Combinado",
}


def ensure_standard_events(db) -> list[EventType]:
    """Garantiza que las 14 pruebas estándar existan como EventType. Idempotente."""
    result = []
    for distance, stroke in STANDARD_EVENTS:
        et = db.query(EventType).filter(EventType.distance_m == distance, EventType.stroke == stroke).first()
        if not et:
            et = EventType(name=f"{distance}m {STROKE_LABELS[stroke]}", distance_m=distance, stroke=stroke)
            db.add(et)
            db.commit()
            db.refresh(et)
        result.append(et)
    return result