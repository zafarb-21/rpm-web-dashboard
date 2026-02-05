from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime

app = FastAPI(title="Remote Patient Monitoring Web Dashboard API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VitalReading(BaseModel):
    patient_id: str
    heart_rate: float | None = None
    spo2: float | None = None
    temperature_c: float | None = None
    timestamp: datetime | None = None

@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}

@app.post("/vitals")
def ingest_vitals(reading: VitalReading):
    if reading.timestamp is None:
        reading.timestamp = datetime.utcnow()
    return {"received": reading.model_dump()}
