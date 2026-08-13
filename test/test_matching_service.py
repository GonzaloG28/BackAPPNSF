# tests/test_matching_service.py
# Casos que DEBEN estar cubiertos antes de tocar el resto del sistema:

from app.services.matching_service import find_swimmer_match

def test_exact_document_id_match(db_session, existing_swimmer):
    result = find_swimmer_match(db_session, {"document_id": existing_swimmer.document_id, "first_name": "X", "last_name": "Y"})
    assert result.method == "document_id"
    assert result.confidence == 100