from datetime import datetime
import os
from typing import Any, Dict, List
from .database import engine
from .models import Base
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .database import SessionLocal
from .models import VitalRecord
from .mqtt_client import MQTTService

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

app = FastAPI(title="RPM Web Dashboard API", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LATEST_VITALS: Dict[str, Any] = {}
LATEST_ECG: Dict[str, Any] = {}

mqtt_service: MQTTService | None = None


def _get_topics() -> List[str]:
    # Prefer MQTT_TOPICS=topic1,topic2
    topics = os.getenv("MQTT_TOPICS", "").strip()
    if topics:
        return [t.strip() for t in topics.split(",") if t.strip()]
    # Backward-compatible fallback
    return [os.getenv("MQTT_TOPIC", "patient/vitals")]


@app.on_event("startup")
def on_startup():
    global mqtt_service
    Base.metadata.create_all(bind=engine)
    host = os.getenv("MQTT_HOST", "")
    port = int(os.getenv("MQTT_PORT", "8883"))
    user = os.getenv("MQTT_USERNAME", "")
    pw = os.getenv("MQTT_PASSWORD", "")
    topics = _get_topics()

    if not host or not user or not pw:
        print("[WARN] MQTT env vars missing. MQTT subscriber will NOT start.")
        return

    mqtt_service = MQTTService(
        host=host,
        port=port,
        username=user,
        password=pw,
        topics=topics,
        latest_vitals_store=LATEST_VITALS,
        latest_ecg_store=LATEST_ECG,
    )
    mqtt_service.start()
    print("[OK] MQTT service started.")


@app.on_event("shutdown")
def on_shutdown():
    if mqtt_service:
        mqtt_service.stop()


@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


@app.get("/patients")
def list_patients():
    # union of both stores
    patients = sorted(set(LATEST_VITALS.keys()) | set(LATEST_ECG.keys()))
    return {"patients": patients}


@app.get("/latest/vitals/{patient_id}")
def latest_vitals(patient_id: str):
    if patient_id not in LATEST_VITALS:
        raise HTTPException(status_code=404, detail="No vitals received for this patient_id yet.")
    return {"patient_id": patient_id, "latest": LATEST_VITALS[patient_id]}


@app.get("/latest/ecg/{patient_id}")
def latest_ecg(patient_id: str):
    if patient_id not in LATEST_ECG:
        raise HTTPException(status_code=404, detail="No ECG stream received for this patient_id yet.")
    return {"patient_id": patient_id, "latest": LATEST_ECG[patient_id]}


@app.get("/history/vitals/{patient_id}")
def vitals_history(patient_id: str, limit: int = 100):
    db = SessionLocal()
    try:
        rows = (
            db.query(VitalRecord)
            .filter(VitalRecord.patient_id == patient_id)
            .order_by(VitalRecord.received_at.desc())
            .limit(min(limit, 500))
            .all()
        )
        # Return newest->oldest
        return {
            "patient_id": patient_id,
            "count": len(rows),
            "records": [
                {
                    "received_at": r.received_at.isoformat(),
                    "alert_level": r.alert_level,
                    "critical": r.critical,
                    "heart_rate": r.heart_rate,
                    "spo2": r.spo2,
                    "temperature": r.temperature,
                    "ecg_heart_rate": r.ecg_heart_rate,
                    "battery": r.battery,
                    "fall_detected": r.fall_detected,
                    "lead_off": r.lead_off,
                    "ecg_quality": r.ecg_quality,
                    "rssi": r.rssi,
                }
                for r in rows
            ],
        }
    finally:
        db.close()
