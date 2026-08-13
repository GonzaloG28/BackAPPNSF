import re


def validate_rut(rut: str) -> bool:
    rut = rut.replace(".", "").replace("-", "").upper()
    if not re.fullmatch(r"\d{7,8}[0-9K]", rut):
        return False

    body, dv = rut[:-1], rut[-1]
    total, factor = 0, 2
    for digit in reversed(body):
        total += int(digit) * factor
        factor = 2 if factor == 7 else factor + 1

    remainder = 11 - (total % 11)
    expected_dv = {11: "0", 10: "K"}.get(remainder, str(remainder))
    return dv == expected_dv