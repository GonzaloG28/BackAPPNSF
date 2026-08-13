# app/services/time_parser.py
import re


class TimeParseError(Exception):
    pass


def parse_time_to_seconds(raw_value) -> float:
    """
    Convierte distintos formatos de tiempo deportivo a segundos (float).

    Formatos soportados (confirmados con datos reales del club):
    - "20.01"        -> 20.01
    - "20,01"        -> 20.01   (coma decimal)
    - "1:02.45"       -> 62.45   (formato estándar min:seg)
    - "1'10,10"       -> 70.10   (apóstrofe como separador de minuto)
    - "1'10.10"       -> 70.10
    - "1"10.01"       -> 70.01   (comilla doble como separador de minuto — variante frecuente)
    """
    if raw_value is None:
        raise TimeParseError("Valor vacío")

    value = str(raw_value).strip()
    if not value:
        raise TimeParseError("Valor vacío")

    # Normaliza coma decimal a punto
    value = value.replace(",", ".")

    # Caso: solo segundos, ej "20.01"
    if re.fullmatch(r"\d{1,3}(\.\d{1,2})?", value):
        return round(float(value), 2)

    # Caso: "1:02.45" (min:seg.centésimas — formato estándar)
    match = re.fullmatch(r"(\d{1,2}):(\d{1,2})\.(\d{1,2})", value)
    if match:
        minutes, seconds, centis = match.groups()
        return _to_seconds(minutes, seconds, centis)

    # Caso: "1'10.10" o "1"10.01" — apóstrofe o comilla doble como separador de minuto,
    # seguido de segundos.centésimas (no hay separador extra para las centésimas)
    match = re.fullmatch(r"(\d{1,2})['\"](\d{1,2})\.(\d{1,2})", value)
    if match:
        minutes, seconds, centis = match.groups()
        return _to_seconds(minutes, seconds, centis)

    raise TimeParseError(f"Formato de tiempo no reconocido: '{raw_value}'")


def _to_seconds(minutes: str, seconds: str, centis: str) -> float:
    factor = 100 if len(centis) == 2 else 10
    total = int(minutes) * 60 + int(seconds) + int(centis) / factor
    return round(total, 2)