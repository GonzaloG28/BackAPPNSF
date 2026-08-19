# app/services/matching_service.py
from rapidfuzz import fuzz
from sqlalchemy.orm import Session
from app.models.swimmer import Swimmer


class MatchResult:
    def __init__(self, swimmer=None, confidence: float = 0, method: str = "", candidates: list = None):
        self.swimmer = swimmer
        self.confidence = confidence
        self.method = method
        self.candidates = candidates or []


def _full_name(first_name_1, last_name_1) -> str:
    return f"{first_name_1 or ''} {last_name_1 or ''}".lower().strip()


def find_swimmer_match(db, row: dict) -> MatchResult:
    if row.get("document_id"):
        exact = db.query(Swimmer).filter(Swimmer.document_id == row["document_id"]).first()
        if exact:
            return MatchResult(swimmer=exact, confidence=100, method="document_id")

    first = row.get("first_name")
    last = row.get("last_name")

    # Si no hay ni RUT ni nombre, no hay forma de identificar/matchear: se crea como "nuevo" en blanco
    if not first and not last and not row.get("document_id"):
        return MatchResult(confidence=0, method="none")

    if row.get("birth_date") and first and last:
        candidates = db.query(Swimmer).filter(Swimmer.birth_date == row["birth_date"]).all()
        for c in candidates:
            score = fuzz.token_sort_ratio(_full_name(first, last), _full_name(c.first_name_1, c.last_name_1))
            if score >= 92:
                return MatchResult(swimmer=c, confidence=score, method="fuzzy+dob")

    if first or last:
        all_active = db.query(Swimmer).filter(Swimmer.status != "DELETED").all()
        scored = []
        full_name = _full_name(first, last)
        for c in all_active:
            score = fuzz.token_sort_ratio(full_name, _full_name(c.first_name_1, c.last_name_1))
            if score >= 75:
                scored.append((c, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        if scored:
            if len(scored) == 1 or (scored[0][1] - scored[1][1] > 15):
                if scored[0][1] >= 85:
                    return MatchResult(swimmer=scored[0][0], confidence=scored[0][1], method="fuzzy_name")
            return MatchResult(confidence=scored[0][1], method="ambiguous", candidates=[c for c, s in scored[:5]])

    return MatchResult(confidence=0, method="none")