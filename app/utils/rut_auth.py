# app/utils/rut_auth.py
import re

def clean_rut(rut: str) -> str:
    """Quita puntos y espacios, deja solo dígitos + guion + dígito verificador."""
    return re.sub(r"[.\s]", "", rut).upper()

def rut_username(rut: str) -> str:
    """Formato de username: sin puntos, con guion. Ej: 12345678-9"""
    return clean_rut(rut)

def rut_default_password(rut: str) -> str:
    """Formato de contraseña por defecto: con puntos y guion. Ej: 12.345.678-9"""
    clean = clean_rut(rut)
    if "-" not in clean:
        return clean
    body, dv = clean.rsplit("-", 1)
    body_with_dots = ""
    for i, digit in enumerate(reversed(body)):
        if i > 0 and i % 3 == 0:
            body_with_dots = "." + body_with_dots
        body_with_dots = digit + body_with_dots
    return f"{body_with_dots}-{dv}"