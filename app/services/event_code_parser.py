import re

from app.models.event_type import StrokeType

STROKE_CODE_MAP = {
    "L": StrokeType.FREE,     # Libre
    "E": StrokeType.BACK,     # Espalda
    "P": StrokeType.BREAST,   # Pecho
    "M": StrokeType.FLY,      # Mariposa
    "IM": StrokeType.MEDLEY,   # Combinado / IM
}


class EventCodeParseError(Exception):
    pass


def parse_event_code(raw_code: str) -> tuple[int, StrokeType]:
    """
    Convierte códigos como "200L", "100P", "50E", "400IM" en (distancia, estilo).
    """
    if raw_code is None:
        raise EventCodeParseError("Código de prueba vacío")

    code = str(raw_code).strip().upper()
    match = re.fullmatch(r"(\d{2,4})([LEPMC])", code)
    if not match:
        raise EventCodeParseError(f"Código de prueba no reconocido: '{raw_code}'")

    distance_str, stroke_code = match.groups()
    return int(distance_str), STROKE_CODE_MAP[stroke_code]