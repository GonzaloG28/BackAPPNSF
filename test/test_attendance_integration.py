from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_attendance_flow(auth_headers, active_swimmer):
    response = client.post("/attendance", json={
        "date": "2026-08-05",
        "records": [{"swimmer_id": active_swimmer.id, "shift": "AM"}]
    }, headers=auth_headers)
    assert response.status_code == 201 or response.status_code == 200

    today = client.get("/attendance/today", headers=auth_headers)
    assert today.status_code == 200
    marked = [s for s in today.json() if s["swimmer_id"] == active_swimmer.id]
    assert marked[0]["shift"] == "AM"