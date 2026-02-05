import json
import ssl
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List

import paho.mqtt.client as mqtt


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class MQTTService:
    """
    Background MQTT subscriber that updates shared stores with latest vitals and ECG.
    """

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        topics: List[str],
        latest_vitals_store: Dict[str, Any],
        latest_ecg_store: Dict[str, Any],
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.topics = [t.strip() for t in topics if t.strip()]
        self.latest_vitals_store = latest_vitals_store
        self.latest_ecg_store = latest_ecg_store

        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self._thread: threading.Thread | None = None

        self._client.username_pw_set(self.username, self.password)

        # HiveMQ Cloud TLS on 8883
        self._client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
        self._client.tls_insecure_set(False)

        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect

    def start(self) -> None:
        self._client.connect(self.host, self.port, keepalive=60)
        self._thread = threading.Thread(target=self._client.loop_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        try:
            self._client.disconnect()
        except Exception:
            pass

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            print(f"[MQTT] Connected. Subscribing to: {self.topics}")
            for t in self.topics:
                client.subscribe(t, qos=0)
        else:
            print(f"[MQTT] Connect failed. reason_code={reason_code}")

    def _on_disconnect(self, client, userdata, reason_code, properties):
        print(f"[MQTT] Disconnected. reason_code={reason_code}")

    def _on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = msg.payload.decode("utf-8", errors="replace")
            data = json.loads(payload)

            patient_id = data.get("patient_id") or data.get("PATIENT_ID") or "unknown"
            data.setdefault("received_at", _utc_now_iso())
            data.setdefault("mqtt_topic", topic)

            # Route based on topic (your ESP32 uses these exact topics)
            if topic == "patient/vitals":
                self.latest_vitals_store[patient_id] = data
            elif topic == "patient/ecg_stream":
                self.latest_ecg_store[patient_id] = data
            else:
                # Unknown topic, store nowhere (or log)
                print(f"[MQTT] Received on unhandled topic: {topic}")
                return

            print(f"[MQTT] Updated {topic} for {patient_id}")

        except Exception as e:
            print(f"[MQTT] Error parsing message: {e}")
