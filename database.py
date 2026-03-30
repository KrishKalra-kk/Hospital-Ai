import sqlite3
import os
from datetime import datetime, timedelta
import random

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hospital.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS hospital_data
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  hour INTEGER,
                  patients INTEGER,
                  beds_available INTEGER,
                  staff_available INTEGER,
                  recorded_at TEXT DEFAULT CURRENT_TIMESTAMP)''')

    c.execute('''CREATE TABLE IF NOT EXISTS departments
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT UNIQUE NOT NULL,
                  description TEXT,
                  floor INTEGER,
                  total_beds INTEGER DEFAULT 0,
                  icon TEXT DEFAULT '🏥')''')

    c.execute('''CREATE TABLE IF NOT EXISTS resources
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  category TEXT NOT NULL,
                  department_id INTEGER,
                  total INTEGER DEFAULT 0,
                  available INTEGER DEFAULT 0,
                  in_use INTEGER DEFAULT 0,
                  maintenance INTEGER DEFAULT 0,
                  status TEXT DEFAULT 'normal',
                  updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (department_id) REFERENCES departments(id))''')

    c.execute('''CREATE TABLE IF NOT EXISTS staff
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  role TEXT NOT NULL,
                  department_id INTEGER,
                  shift TEXT DEFAULT 'Day',
                  status TEXT DEFAULT 'On Duty',
                  phone TEXT,
                  email TEXT,
                  hired_at TEXT DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (department_id) REFERENCES departments(id))''')

    c.execute('''CREATE TABLE IF NOT EXISTS patients
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  age INTEGER,
                  gender TEXT,
                  condition TEXT,
                  severity TEXT DEFAULT 'Stable',
                  department_id INTEGER,
                  bed_number TEXT,
                  admitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
                  discharged_at TEXT,
                  status TEXT DEFAULT 'Admitted',
                  notes TEXT,
                  FOREIGN KEY (department_id) REFERENCES departments(id))''')

    c.execute('''CREATE TABLE IF NOT EXISTS alerts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  type TEXT NOT NULL,
                  severity TEXT NOT NULL,
                  message TEXT NOT NULL,
                  department TEXT,
                  acknowledged INTEGER DEFAULT 0,
                  acknowledged_by TEXT,
                  acknowledged_at TEXT,
                  created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')

    conn.commit()
    conn.close()


# ─── Hospital Data (hourly snapshots) ───

def insert_hospital_data(hour, patients, beds, staff):
    conn = get_conn()
    conn.execute(
        "INSERT INTO hospital_data (hour, patients, beds_available, staff_available) VALUES (?, ?, ?, ?)",
        (hour, patients, beds, staff))
    conn.commit()
    conn.close()


def get_hospital_data():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM hospital_data ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── Departments ───

def get_departments():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM departments ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_department(dept_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM departments WHERE id = ?", (dept_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ─── Resources ───

def get_resources():
    conn = get_conn()
    rows = conn.execute("""
        SELECT r.*, d.name as department_name
        FROM resources r
        LEFT JOIN departments d ON r.department_id = d.id
        ORDER BY r.category, r.name
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_resource(resource_id, available, in_use, maintenance):
    conn = get_conn()
    conn.execute("""
        UPDATE resources
        SET available = ?, in_use = ?, maintenance = ?,
            status = CASE
                WHEN ? = 0 THEN 'critical'
                WHEN CAST(? AS FLOAT) / NULLIF(total, 0) < 0.2 THEN 'warning'
                ELSE 'normal'
            END,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (available, in_use, maintenance, available, available, resource_id))
    conn.commit()
    conn.close()


def get_resource_summary():
    conn = get_conn()
    rows = conn.execute("""
        SELECT category,
               SUM(total) as total,
               SUM(available) as available,
               SUM(in_use) as in_use,
               SUM(maintenance) as maintenance
        FROM resources GROUP BY category
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── Staff ───

def get_staff():
    conn = get_conn()
    rows = conn.execute("""
        SELECT s.*, d.name as department_name
        FROM staff s
        LEFT JOIN departments d ON s.department_id = d.id
        ORDER BY s.name
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_staff_on_duty():
    conn = get_conn()
    row = conn.execute("SELECT COUNT(*) as count FROM staff WHERE status = 'On Duty'").fetchone()
    conn.close()
    return row['count'] if row else 0


def get_staff_summary():
    conn = get_conn()
    rows = conn.execute("""
        SELECT role, COUNT(*) as count,
               SUM(CASE WHEN status = 'On Duty' THEN 1 ELSE 0 END) as on_duty
        FROM staff GROUP BY role
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── Patients ───

def get_patients(status_filter=None):
    conn = get_conn()
    if status_filter:
        rows = conn.execute("""
            SELECT p.*, d.name as department_name
            FROM patients p
            LEFT JOIN departments d ON p.department_id = d.id
            WHERE p.status = ?
            ORDER BY p.admitted_at DESC
        """, (status_filter,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT p.*, d.name as department_name
            FROM patients p
            LEFT JOIN departments d ON p.department_id = d.id
            ORDER BY p.admitted_at DESC
        """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_patient(name, age, gender, condition, severity, department_id, bed_number, notes=""):
    conn = get_conn()
    conn.execute("""
        INSERT INTO patients (name, age, gender, condition, severity, department_id, bed_number, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, age, gender, condition, severity, department_id, bed_number, notes))
    conn.commit()
    conn.close()


def discharge_patient(patient_id):
    conn = get_conn()
    conn.execute("""
        UPDATE patients SET status = 'Discharged', discharged_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (patient_id,))
    conn.commit()
    conn.close()


def get_patient_counts():
    conn = get_conn()
    row = conn.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN status = 'Admitted' THEN 1 ELSE 0 END) as admitted,
            SUM(CASE WHEN severity = 'Critical' AND status = 'Admitted' THEN 1 ELSE 0 END) as critical,
            SUM(CASE WHEN status = 'Discharged' THEN 1 ELSE 0 END) as discharged
        FROM patients
    """).fetchone()
    conn.close()
    return dict(row) if row else {'total': 0, 'admitted': 0, 'critical': 0, 'discharged': 0}


# ─── Alerts ───

def get_alerts(pending_only=False):
    conn = get_conn()
    if pending_only:
        rows = conn.execute(
            "SELECT * FROM alerts WHERE acknowledged = 0 ORDER BY created_at DESC").fetchall()
    else:
        rows = conn.execute("SELECT * FROM alerts ORDER BY created_at DESC LIMIT 50").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_alert(alert_type, severity, message, department=None):
    conn = get_conn()
    conn.execute(
        "INSERT INTO alerts (type, severity, message, department) VALUES (?, ?, ?, ?)",
        (alert_type, severity, message, department))
    conn.commit()
    conn.close()


def acknowledge_alert(alert_id, acknowledged_by="Admin"):
    conn = get_conn()
    conn.execute("""
        UPDATE alerts SET acknowledged = 1, acknowledged_by = ?, acknowledged_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (acknowledged_by, alert_id))
    conn.commit()
    conn.close()


def get_alert_counts():
    conn = get_conn()
    row = conn.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN acknowledged = 0 THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN severity = 'CRITICAL' AND acknowledged = 0 THEN 1 ELSE 0 END) as critical
        FROM alerts
    """).fetchone()
    conn.close()
    return dict(row) if row else {'total': 0, 'pending': 0, 'critical': 0}


# ─── Seed Data ───

def seed_data():
    conn = get_conn()

    # Check if already seeded
    count = conn.execute("SELECT COUNT(*) as c FROM departments").fetchone()['c']
    if count > 0:
        conn.close()
        return

    # Departments
    departments = [
        ('Emergency', 'Emergency room and trauma center', 1, 30, '🚨'),
        ('ICU', 'Intensive Care Unit', 2, 20, '💉'),
        ('General Ward', 'General admission and recovery', 3, 60, '🛏️'),
        ('Pediatrics', 'Children\'s care unit', 2, 25, '👶'),
        ('Cardiology', 'Heart and cardiovascular care', 4, 15, '❤️'),
        ('Orthopedics', 'Bone and joint treatment', 3, 20, '🦴'),
        ('Neurology', 'Brain and nervous system care', 4, 10, '🧠'),
        ('Maternity', 'Pregnancy and childbirth care', 2, 15, '🤱'),
    ]
    for d in departments:
        conn.execute("INSERT INTO departments (name, description, floor, total_beds, icon) VALUES (?,?,?,?,?)", d)

    # Resources
    resources = [
        ('Hospital Beds', 'Beds', 3, 60, 42, 15, 3),
        ('ICU Beds', 'Beds', 2, 20, 5, 14, 1),
        ('Emergency Beds', 'Beds', 1, 30, 12, 16, 2),
        ('Ventilators', 'Equipment', 2, 30, 12, 16, 2),
        ('Oxygen Cylinders', 'Equipment', None, 100, 55, 40, 5),
        ('Defibrillators', 'Equipment', None, 15, 10, 4, 1),
        ('X-Ray Machines', 'Equipment', None, 8, 4, 3, 1),
        ('CT Scanners', 'Equipment', None, 3, 1, 2, 0),
        ('MRI Machines', 'Equipment', None, 2, 1, 1, 0),
        ('Wheelchairs', 'Mobility', None, 40, 25, 12, 3),
        ('Stretchers', 'Mobility', None, 20, 10, 8, 2),
        ('Blood Units (O+)', 'Blood Bank', None, 50, 32, 18, 0),
        ('Blood Units (A+)', 'Blood Bank', None, 40, 25, 15, 0),
        ('Blood Units (B+)', 'Blood Bank', None, 35, 20, 15, 0),
        ('Blood Units (AB+)', 'Blood Bank', None, 20, 12, 8, 0),
    ]
    for r in resources:
        conn.execute("""
            INSERT INTO resources (name, category, department_id, total, available, in_use, maintenance, status)
            VALUES (?, ?, ?, ?, ?, ?, ?,
                    CASE WHEN ? = 0 THEN 'critical'
                         WHEN CAST(? AS FLOAT) / NULLIF(?, 0) < 0.2 THEN 'warning'
                         ELSE 'normal' END)
        """, (r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[4], r[4], r[3]))

    # Staff
    first_names = ['Dr. Sarah', 'Dr. James', 'Dr. Priya', 'Dr. Michael', 'Dr. Aisha',
                   'Nurse Emily', 'Nurse Carlos', 'Nurse Fatima', 'Nurse David', 'Nurse Lisa',
                   'Dr. Chen', 'Dr. Rodriguez', 'Nurse Anna', 'Nurse Raj', 'Dr. Kim',
                   'Nurse Olivia', 'Dr. Patel', 'Nurse Thomas', 'Dr. Williams', 'Nurse Grace',
                   'Dr. Hassan', 'Nurse Sophie', 'Dr. Martinez', 'Nurse Jun', 'Dr. Brown']
    last_names = ['Johnson', 'Kumar', 'Smith', 'Chen', 'Al-Farsi',
                  'Rivera', 'Santos', 'Ahmed', 'Taylor', 'Nguyen',
                  'Wei', 'Garcia', 'Kowalski', 'Sharma', 'Park',
                  'Green', 'Mehta', 'Wright', 'Stone', 'Lee',
                  'Abbas', 'Laurent', 'Lopez', 'Tanaka', 'Davis']
    roles = ['Doctor', 'Doctor', 'Doctor', 'Nurse', 'Nurse', 'Nurse', 'Nurse',
             'Surgeon', 'Technician', 'Specialist']
    shifts = ['Day', 'Day', 'Day', 'Night', 'Night', 'Evening']
    statuses = ['On Duty', 'On Duty', 'On Duty', 'On Duty', 'Off Duty', 'On Leave']

    for i in range(25):
        conn.execute("""
            INSERT INTO staff (name, role, department_id, shift, status, phone, email)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            f"{first_names[i]} {last_names[i]}",
            random.choice(roles),
            random.randint(1, 8),
            random.choice(shifts),
            random.choice(statuses),
            f"+1-555-{random.randint(1000,9999)}",
            f"{first_names[i].split()[-1].lower()}.{last_names[i].lower()}@hospital.org"
        ))

    # Patients
    patient_names = [
        ('John', 'Miller', 45, 'M'), ('Maria', 'Garcia', 32, 'F'),
        ('Robert', 'Singh', 67, 'M'), ('Emma', 'Watson', 28, 'F'),
        ('Ahmed', 'Khan', 55, 'M'), ('Sophie', 'Chen', 41, 'F'),
        ('David', 'Brown', 73, 'M'), ('Aisha', 'Patel', 19, 'F'),
        ('Thomas', 'Lee', 60, 'M'), ('Olivia', 'Martinez', 35, 'F'),
        ('James', 'Taylor', 48, 'M'), ('Nina', 'Kowalski', 52, 'F'),
        ('Carlos', 'Rivera', 38, 'M'), ('Fatima', 'Ali', 29, 'F'),
        ('Michael', 'White', 71, 'M'), ('Grace', 'Obi', 44, 'F'),
        ('Raj', 'Sharma', 56, 'M'), ('Emily', 'Clark', 33, 'F'),
    ]
    conditions = ['Pneumonia', 'Fracture', 'Cardiac Arrest', 'Appendicitis',
                  'Diabetes', 'COVID-19', 'Stroke', 'Burns',
                  'Asthma', 'Hypertension', 'Migraine', 'Infection',
                  'Anemia', 'Kidney Stone', 'Dengue', 'Flu',
                  'Chest Pain', 'Head Injury']
    severities = ['Stable', 'Stable', 'Stable', 'Moderate', 'Moderate', 'Critical']

    for i, (first, last, age, gender) in enumerate(patient_names):
        dept_id = random.randint(1, 8)
        status = 'Admitted' if i < 14 else 'Discharged'
        admitted = (datetime.now() - timedelta(days=random.randint(0, 7),
                                                hours=random.randint(0, 23))).strftime('%Y-%m-%d %H:%M:%S')
        conn.execute("""
            INSERT INTO patients (name, age, gender, condition, severity, department_id,
                                  bed_number, admitted_at, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f"{first} {last}", age, gender, conditions[i],
            random.choice(severities), dept_id,
            f"{chr(64 + dept_id)}-{random.randint(1, 30):02d}",
            admitted, status, f"Patient admitted with {conditions[i].lower()}"
        ))

    # Hourly data (from existing CSV pattern, extended)
    hourly = [
        (1, 20, 50, 10), (2, 25, 48, 10), (3, 30, 45, 9), (4, 28, 43, 9),
        (5, 35, 40, 8), (6, 45, 35, 8), (7, 50, 30, 7), (8, 60, 25, 7),
        (9, 70, 20, 6), (10, 80, 15, 5), (11, 85, 12, 5), (12, 78, 14, 6),
        (13, 72, 18, 6), (14, 65, 22, 7), (15, 70, 20, 7), (16, 75, 18, 6),
        (17, 82, 14, 5), (18, 88, 10, 5), (19, 76, 16, 6), (20, 60, 24, 7),
        (21, 45, 32, 8), (22, 35, 38, 9), (23, 28, 42, 9), (24, 22, 46, 10),
    ]
    for h in hourly:
        conn.execute(
            "INSERT INTO hospital_data (hour, patients, beds_available, staff_available) VALUES (?,?,?,?)", h)

    # Alerts
    alerts_data = [
        ('Resource', 'CRITICAL', 'ICU beds critically low — only 5 remaining', 'ICU'),
        ('Resource', 'WARNING', 'Ventilator availability below 50%', 'ICU'),
        ('Staff', 'WARNING', 'Night shift understaffed in Emergency', 'Emergency'),
        ('Resource', 'INFO', 'New oxygen cylinder shipment received', None),
        ('Patient', 'CRITICAL', 'Code Blue — Cardiac arrest in Room A-12', 'Emergency'),
        ('Resource', 'WARNING', 'CT Scanner #2 scheduled for maintenance', None),
        ('Staff', 'INFO', 'Dr. Sarah Johnson shift change at 18:00', None),
        ('Resource', 'CRITICAL', 'Blood bank O+ units below threshold', None),
        ('Patient', 'WARNING', 'Patient overflow in General Ward', 'General Ward'),
        ('System', 'INFO', 'Daily backup completed successfully', None),
    ]
    for a in alerts_data:
        conn.execute(
            "INSERT INTO alerts (type, severity, message, department) VALUES (?,?,?,?)", a)

    conn.commit()
    conn.close()
    print("[OK] Database seeded with sample data")