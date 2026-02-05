from sqlalchemy import String, Integer, Float, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone

from .database import Base

def utcnow():
    return datetime.now(timezone.utc)

class VitalRecord(Base):
    __tablename__ = "vital_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[str] = mapped_column(String, index=True)

    received_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)

    alert_level: Mapped[str | None] = mapped_column(String, nullable=True)
    critical: Mapped[bool] = mapped_column(Boolean, default=False)

    heart_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    spo2: Mapped[float | None] = mapped_column(Float, nullable=True)
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    ecg_heart_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    battery: Mapped[float | None] = mapped_column(Float, nullable=True)

    fall_detected: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    lead_off: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    ecg_quality: Mapped[str | None] = mapped_column(String, nullable=True)

    rssi: Mapped[float | None] = mapped_column(Float, nullable=True)
