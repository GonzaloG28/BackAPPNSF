# app/main.py
from fastapi import FastAPI

from app.database import Base, engine
import app.models

from app.routers import imports, swimmers, attendance,attendance_v2, competitions, convocatorias,exports, auth, gym, performance
app = FastAPI(title="SwimAI API", version="0.1.0")

Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(imports.router)
app.include_router(swimmers.router)
app.include_router(attendance.router)
app.include_router(competitions.router)
app.include_router(convocatorias.router)
app.include_router(exports.router)
app.include_router(gym.exercises_router)
app.include_router(performance.router)
app.include_router(attendance_v2.router)
@app.get("/")
def root():
    return {"status": "SwimAI backend corriendo"}