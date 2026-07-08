# Emmanuel Otieno — Real-Time Push-Notification Visitor Management System

Flask + SQLite prototype for a shared office hub where reception checks in visitors and hosts receive instant alerts with SMS fallback simulation.

## Features
- Secure login for Administrator, Receptionist and Host
- Tenant company and host records
- Reception visitor check-in form
- Instant push notification record when visitor arrives
- Host notification panel with acknowledgement
- SMS fallback simulation for unreachable hosts
- Visitor checkout/status tracking
- Admin reports, visitor CSV export and audit log

## Run Locally
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
Open: http://127.0.0.1:5052

## Render Deployment
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`

## Demo Accounts
- Administrator: `admin` / `Admin@2026`
- Receptionist: `reception` / `Reception@2026`
- Host: `otieno` / `Host@2026`

The SQLite database is created and seeded automatically on first run.
