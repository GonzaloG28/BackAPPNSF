# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware


from app.database import Base, engine
import app.models

from app.routers import imports, swimmers, attendance, attendance_v2, competitions, convocatorias, exports, auth, gym, performance, calendar, swimmer_auth, swimmer_self, reports

app = FastAPI(title="SwimAI API", version="0.1.0")


Base.metadata.create_all(bind=engine)

# 1. Defines explícitamente quién puede conectarse a tu API
origenes_permitidos = [
    "http://localhost:8081",
    "http://localhost:8082",             # Para que puedas seguir probando en tu PC
    "https://swimmobilensf.vercel.app"   # El enlace oficial para tus profesores
]

# 2. Configuras el middleware con esa lista
app.add_middleware(
    CORSMiddleware,
    allow_origins=origenes_permitidos, 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=500)

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
app.include_router(calendar.router)
app.include_router(swimmer_auth.router)
app.include_router(swimmer_self.router)
app.include_router(reports.router)

@app.get("/")
def root():
    return {"status": "SwimAI backend corriendo"}