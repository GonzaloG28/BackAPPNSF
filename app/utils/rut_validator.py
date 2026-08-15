# app/utils/rut_validator.py
import re


def _clean_rut(rut: str) -> str:
    """Deja solo dígitos y K/k, en mayúscula. Quita puntos, guión y espacios."""
    return re.sub(r"[^0-9kK]", "", rut).upper()


def _compute_dv(body: str) -> str:
    """Calcula el dígito verificador de un RUT chileno (algoritmo módulo 11)."""
    total = 0
    multiplier = 2
    for digit in reversed(body):
        total += int(digit) * multiplier
        multiplier = multiplier + 1 if multiplier < 7 else 2
    remainder = 11 - (total % 11)
    if remainder == 11:
        return "0"
    if remainder == 10:
        return "K"
    return str(remainder)


def validate_rut(rut: str) -> bool:
    if not rut:
        return False

    clean = _clean_rut(rut)
    if len(clean) < 2:
        return False

    body, dv = clean[:-1], clean[-1]
    if not body.isdigit():
        return False

    return _compute_dv(body) == dv


def normalize_rut(rut: str) -> str:
    """Devuelve el RUT limpio (sin puntos) con guión, para guardar consistente en BD.
    Ej: '12.345.678-9' -> '12345678-9'
    """
    clean = _clean_rut(rut)
    if len(clean) < 2:
        return clean
    return f"{clean[:-1]}-{clean[-1]}"