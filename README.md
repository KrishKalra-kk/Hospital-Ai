# 🏥 MedByte — Hospital AI Resource Management System

A full-fledged, AI-powered hospital resource acknowledgement and management website built entirely in **Python** using Flask.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.x-green?logo=flask)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Features

- **📊 Dashboard** — Real-time KPI cards, patient trend charts, resource donut charts, alerts & AI recommendations
- **🛏️ Resource Management** — Track beds, ICU, ventilators, equipment, blood bank with utilization progress bars
- **👥 Patient Management** — Admit, track, and discharge patients with severity levels and department assignments
- **🤖 AI Predictions** — ML-powered patient prediction simulator with confidence scores and risk levels
- **🚨 Alert Center** — Critical/warning/info alerts with AJAX-based acknowledgement
- **⚙️ Settings** — Manual data entry, department overview, full staff roster

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python, Flask |
| Database | SQLite |
| ML Model | scikit-learn (Linear Regression) |
| Charts | Chart.js (CDN) |
| Styling | Embedded CSS (white theme) |
| Frontend | Embedded HTML/JS in Python |

## Quick Start

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/HospitalAI.git
cd HospitalAI

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py

# Open http://localhost:5000
```

## Project Structure

```
HospitalAI/
├── app.py           # Flask routes & API endpoints
├── database.py      # SQLite database (6 tables + seed data)
├── model.py         # ML prediction model
├── decision.py      # Alert & recommendation engine
├── styles.py        # CSS design system (Python string)
├── templates_py.py  # HTML templates & JS (Python strings)
├── data.csv         # Training data for ML model
├── requirements.txt # Python dependencies
└── .gitignore
```

## Database Schema

- **hospital_data** — Hourly patient/bed/staff snapshots
- **departments** — 8 hospital departments
- **resources** — 15 tracked resources (beds, equipment, blood bank)
- **staff** — 25 staff members with roles and shifts
- **patients** — Patient records with conditions and severity
- **alerts** — System alerts with acknowledgement workflow

## Screenshots

### Dashboard
Clean white-themed dashboard with live metrics and Chart.js visualizations.

### Patient Management
Full patient table with severity badges, department assignments, and discharge actions.

## License

MIT License — feel free to use and modify.
