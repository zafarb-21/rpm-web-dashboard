# RPM Web Dashboard – Software Documentation
## Overview

This repository contains the software stack for a cloud-based Remote Patient Monitoring (RPM) system.
It ingests real-time biomedical data from an ESP32 device via MQTT, stores time-series health data, and presents it through a responsive web dashboard accessible from any internet-connected device.

The system is designed using modern IoT and web engineering practices, with a strong focus on reliability, scalability, and clarity of data flow.

## Technology Stack
### Backend

Python 3

FastAPI – REST API framework

Paho-MQTT – MQTT client for cloud ingestion

SQLAlchemy – ORM for database access

SQLite – local time-series storage

Uvicorn – ASGI server

### Frontend

HTML5

CSS3 (Responsive Design)

JavaScript (Vanilla)

Chart.js – time-series data visualization

### Cloud & DevOps

Render – cloud hosting & deployment

HiveMQ Cloud – secure MQTT broker

GitHub – version control & CI/CD

TLS (MQTT over 8883) – encrypted communication

ESP32 (Sensors + Alerts)
        |
        |  MQTT over TLS
        v
HiveMQ Cloud Broker
        |
        |  MQTT subscription
        v
FastAPI Backend (Python)
        |
        |  ORM (SQLAlchemy)
        v
SQLite Database
        |
        |  REST API
        v
Web Dashboard (HTML/CSS/JS)
