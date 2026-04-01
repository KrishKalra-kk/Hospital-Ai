"""
MedByte — Database layer
Extended schema supporting:
  - Typed bed inventory (ICU, General, Shared, Single, Deluxe)
  - Blood component breakdown (RBCs, Plasma, Platelets, Whole Blood)
  - RFID tracking for wheelchairs & stretchers
  - Patient ↔ ventilator / oxygen cylinder links
  - Departments, Staff, Alerts, Hourly snapshots
"""

import sqlite3
import os
from datetime import datetime, timedelta
import random
import uuid

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hospital.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def drop_and_recreate():
    """Drop and recreate all tables (dev only)."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    create_db()


def create_db():
    conn = get_conn()
    c = conn.cursor()

    # ── Departments ──
    c.execute("""CREATE TABLE IF NOT EXISTS departments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        floor INTEGER,
        total_beds INTEGER DEFAULT 0,
        icon TEXT DEFAULT '🏥'
    )""")

    # ── Beds (individual records) ──
    c.execute("""CREATE TABLE IF NOT EXISTS beds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bed_code TEXT UNIQUE NOT NULL,
        bed_type TEXT NOT NULL,   -- ICU, General, Shared, Single, Deluxe, Emergency
        department_id INTEGER,
        floor INTEGER DEFAULT 1,
        ward TEXT,
        room_number TEXT,          -- for shared rooms grouping
        capacity INTEGER DEFAULT 1,-- how many beds in this shared room
        status TEXT DEFAULT 'Available',  -- Available, Occupied, Maintenance, Reserved
        patient_id INTEGER,
        last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
        notes TEXT,
        FOREIGN KEY (department_id) REFERENCES departments(id),
        FOREIGN KEY (patient_id) REFERENCES patients(id)
    )""")

    # ── Blood Bank (by component & type) ──
    c.execute("""CREATE TABLE IF NOT EXISTS blood_inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        blood_group TEXT NOT NULL,   -- A+, A-, B+, B-, O+, O-, AB+, AB-
        component TEXT NOT NULL,     -- Whole Blood, RBC, Plasma, Platelets, FFP
        units_total INTEGER DEFAULT 0,
        units_available INTEGER DEFAULT 0,
        units_reserved INTEGER DEFAULT 0,
        expiry_date TEXT,
        status TEXT DEFAULT 'normal',  -- normal, low, critical
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    # ── Mobile Equipment with RFID ──
    c.execute("""CREATE TABLE IF NOT EXISTS mobile_equipment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rfid_tag TEXT UNIQUE NOT NULL,
        equipment_type TEXT NOT NULL,  -- Wheelchair, Stretcher
        asset_code TEXT UNIQUE NOT NULL,
        status TEXT DEFAULT 'Available',  -- Available, In Use, Maintenance, Missing
        current_location TEXT,
        department_id INTEGER,
        assigned_to_patient INTEGER,  -- patient_id if in use
        last_seen TEXT DEFAULT CURRENT_TIMESTAMP,
        condition TEXT DEFAULT 'Good', -- Good, Fair, Poor
        notes TEXT,
        FOREIGN KEY (department_id) REFERENCES departments(id),
        FOREIGN KEY (assigned_to_patient) REFERENCES patients(id)
    )""")

    # ── Life-support equipment linked to patients ──
    c.execute("""CREATE TABLE IF NOT EXISTS life_support (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        equipment_type TEXT NOT NULL,  -- Ventilator, Oxygen Cylinder
        asset_code TEXT UNIQUE NOT NULL,
        patient_id INTEGER,            -- null if available
        department_id INTEGER,
        status TEXT DEFAULT 'Available',  -- Available, In Use, Maintenance
        flow_rate TEXT,    -- e.g. "10L/min" for O2, "SIMV" for vent
        started_at TEXT,
        pressure_psi INTEGER,  -- for O2 cylinders
        battery_hours INTEGER, -- for ventilators
        notes TEXT,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(id),
        FOREIGN KEY (department_id) REFERENCES departments(id)
    )""")

    # ── Legacy resources (Equipment/Mobility general) ──
    c.execute("""CREATE TABLE IF NOT EXISTS resources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        department_id INTEGER,
        total INTEGER DEFAULT 0,
        available INTEGER DEFAULT 0,
        in_use INTEGER DEFAULT 0,
        maintenance INTEGER DEFAULT 0,
        status TEXT DEFAULT 'normal',
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (department_id) REFERENCES departments(id)
    )""")

    # ── Staff ──
    c.execute("""CREATE TABLE IF NOT EXISTS staff (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        role TEXT NOT NULL,
        department_id INTEGER,
        shift TEXT DEFAULT 'Day',
        status TEXT DEFAULT 'On Duty',
        phone TEXT,
        email TEXT,
        hired_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (department_id) REFERENCES departments(id)
    )""")

    # ── Patients ──
    c.execute("""CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        FOREIGN KEY (department_id) REFERENCES departments(id)
    )""")

    # ── Alerts ──
    c.execute("""CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        severity TEXT NOT NULL,
        message TEXT NOT NULL,
        department TEXT,
        acknowledged INTEGER DEFAULT 0,
        acknowledged_by TEXT,
        acknowledged_at TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    # ── Hourly operational snapshots ──
    c.execute("""CREATE TABLE IF NOT EXISTS hospital_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hour INTEGER,
        patients INTEGER,
        beds_available INTEGER,
        staff_available INTEGER,
        recorded_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    # ── App settings (theme, preferences) ──
    c.execute("""CREATE TABLE IF NOT EXISTS app_settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )""")

    conn.commit()
    conn.close()


def migrate_schema():
    conn = get_conn()
    c = conn.cursor()

    # Ensure weak compatibility for older DB
    def has_column(table, column):
        cols = [r['name'] for r in c.execute(f"PRAGMA table_info({table})").fetchall()]
        return column in cols

    if not has_column('patients', 'assigned_staff_id'):
        c.execute('ALTER TABLE patients ADD COLUMN assigned_staff_id INTEGER')
    if not has_column('patients', 'assigned_ventilator_id'):
        c.execute('ALTER TABLE patients ADD COLUMN assigned_ventilator_id INTEGER')
    if not has_column('patients', 'assigned_oxygen_id'):
        c.execute('ALTER TABLE patients ADD COLUMN assigned_oxygen_id INTEGER')
    if not has_column('patients', 'blood_group'):
        c.execute('ALTER TABLE patients ADD COLUMN blood_group TEXT')
    if not has_column('patients', 'blood_component'):
        c.execute('ALTER TABLE patients ADD COLUMN blood_component TEXT')
    if not has_column('patients', 'blood_units'):
        c.execute('ALTER TABLE patients ADD COLUMN blood_units INTEGER DEFAULT 0')

    if not has_column('beds', 'room_number'):
        c.execute("ALTER TABLE beds ADD COLUMN room_number TEXT")
    if not has_column('beds', 'capacity'):
        c.execute("ALTER TABLE beds ADD COLUMN capacity INTEGER DEFAULT 1")

    # Ensure app_settings exists if migrate called directly
    c.execute("""CREATE TABLE IF NOT EXISTS app_settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )""")

    conn.commit()
    conn.close()


def get_setting(key, default=None):
    conn = get_conn()
    row = conn.execute('SELECT value FROM app_settings WHERE key=?', (key,)).fetchone()
    conn.close()
    return row['value'] if row else default


def set_setting(key, value):
    conn = get_conn()
    conn.execute('INSERT INTO app_settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value', (key, value))
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════
#  SEED DATA
# ═══════════════════════════════════════════════

def seed_data():
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) as c FROM departments").fetchone()['c']
    if count > 0:
        conn.close()
        return
    _seed(conn)
    conn.commit()
    conn.close()
    print("[OK] Database seeded.")


def _seed(conn):
    # ── Departments ──
    departments = [
        ('Emergency',     'Emergency room and trauma center', 1, 30, '🚨'),
        ('ICU',           'Intensive Care Unit',              2, 20, '💉'),
        ('General Ward',  'General admission and recovery',   3, 60, '🛏️'),
        ('Pediatrics',    "Children's care unit",             2, 25, '👶'),
        ('Cardiology',    'Heart and cardiovascular care',    4, 15, '❤️'),
        ('Orthopedics',   'Bone and joint treatment',         3, 20, '🦴'),
        ('Neurology',     'Brain and nervous system care',    4, 10, '🧠'),
        ('Maternity',     'Pregnancy and childbirth care',    2, 15, '🤱'),
    ]
    for d in departments:
        conn.execute("INSERT INTO departments (name,description,floor,total_beds,icon) VALUES (?,?,?,?,?)", d)

    # ── Beds ──
    bed_types = {
        'ICU':     [('ICU', 2, 'ICU Ward')],
        'General Ward': [('General', 3, 'Ward B'), ('Single', 3, 'Ward C'), ('Deluxe', 3, 'Suite')],
        'Pediatrics': [('Single', 2, 'Peds Private')],
        'Cardiology': [('Single', 4, 'Cardio Ward'), ('ICU', 4, 'CICU')],
        'Orthopedics': [('Single', 3, 'Ortho Ward'), ('General', 3, 'Ortho Bay')],
        'Neurology': [('Single', 4, 'Neuro Ward'), ('ICU', 4, 'NICU')],
        'Maternity': [('Single', 2, 'Labor & Delivery'), ('Deluxe', 2, 'Suite')],
    }
    bed_counts = {'ICU': 5, 'General': 8, 'Single': 6, 'Deluxe': 3}
    status_weights = ['Available'] * 5 + ['Occupied'] * 4 + ['Maintenance']

    dept_rows = {row['name']: row['id'] for row in conn.execute("SELECT id,name FROM departments")}

    bed_records = []
    for dept_name, type_list in bed_types.items():
        dept_id = dept_rows.get(dept_name, 1)
        for (btype, floor, ward) in type_list:
            count = bed_counts.get(btype, 6)
            for i in range(1, count + 1):
                prefix = btype[0].upper()
                code = f"{dept_name[:2].upper()}-{prefix}{i:02d}"
                st = random.choice(status_weights)
                bed_records.append((code, btype, dept_id, floor, ward, st, None, None))

    for b in bed_records:
        conn.execute("""INSERT OR IGNORE INTO beds
            (bed_code, bed_type, department_id, floor, ward, status, patient_id, notes)
            VALUES (?,?,?,?,?,?,?,?)""", b)

    # ── Shared Rooms (multi-bed rooms with 2-6 capacity) ──
    shared_depts = [
        ('General Ward', 3, 'Ward A'),
        ('Pediatrics', 2, 'Peds Ward'),
    ]
    room_capacities = [2, 3, 4, 6, 2, 3]  # variety of room sizes
    room_idx = 0
    for dept_name, floor, ward in shared_depts:
        dept_id = dept_rows.get(dept_name, 1)
        for r in range(1, 4):  # 3 rooms per dept
            cap = room_capacities[room_idx % len(room_capacities)]
            room_num = f"{dept_name[:2].upper()}-R{r:02d}"
            for bed_i in range(1, cap + 1):
                code = f"{room_num}-B{bed_i}"
                st = random.choice(status_weights)
                conn.execute("""INSERT OR IGNORE INTO beds
                    (bed_code, bed_type, department_id, floor, ward, room_number, capacity, status)
                    VALUES (?,?,?,?,?,?,?,?)""",
                    (code, 'Shared', dept_id, floor, ward, room_num, cap, st))
            room_idx += 1

    # ── Emergency Beds (separate, reserved for General ward overflow) ──
    emergency_dept_id = dept_rows.get('Emergency', 1)
    for i in range(1, 11):
        code = f"EM-{i:02d}"
        conn.execute("""INSERT OR IGNORE INTO beds
            (bed_code, bed_type, department_id, floor, ward, status, patient_id, notes)
            VALUES (?,?,?,?,?,?,?,?)""",
            (code, 'Emergency', emergency_dept_id, 1, 'Emergency Bay', 'Available', None,
             'Emergency overflow bed — activates when General ward beds are full'))

    # ── Patients (seeded first so we can link) ──
    patient_data = [
        ('Arun Kumar',    45, 'M', 'Pneumonia',     'Critical',  1),
        ('Priya Sharma',  32, 'F', 'Fracture',      'Stable',    6),
        ('Mohan Singh',   67, 'M', 'Cardiac Arrest','Critical',  5),
        ('Divya Patel',   28, 'F', 'Appendicitis',  'Moderate',  3),
        ('Rajesh Verma',  55, 'M', 'Stroke',        'Critical',  7),
        ('Sunita Rao',    41, 'F', 'Burns',         'Moderate',  1),
        ('Vikram Bose',   73, 'M', 'COPD',          'Stable',    3),
        ('Ananya Das',    19, 'F', 'Dengue',        'Stable',    4),
        ('Sameer Khan',   60, 'M', 'Hypertension',  'Stable',    3),
        ('Kavya Nair',    35, 'F', 'COVID-19',      'Moderate',  2),
        ('Arjun Menon',   48, 'M', 'Chest Pain',    'Moderate',  5),
        ('Leila Ahmed',   52, 'F', 'Anemia',        'Stable',    3),
        ('Chetan Gupta',  38, 'M', 'Kidney Stone',  'Stable',    3),
        ('Meera Joshi',   29, 'F', 'Migraine',      'Stable',    7),
    ]
    sev_map = {'Critical': 0, 'Moderate': 1, 'Stable': 2}
    for i, (name, age, gender, cond, sev, dept_id) in enumerate(patient_data):
        admitted = (datetime.now() - timedelta(days=random.randint(0, 7),
                                                hours=random.randint(0, 23))).strftime('%Y-%m-%d %H:%M:%S')
        status = 'Admitted' if i < 12 else 'Discharged'
        conn.execute("""INSERT INTO patients
            (name,age,gender,condition,severity,department_id,admitted_at,status,notes)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (name, age, gender, cond, sev, dept_id, admitted, status,
             f"Patient admitted with {cond.lower()}"))

    # ── Assign patients to beds ──
    patient_ids = [r['id'] for r in conn.execute("SELECT id FROM patients WHERE status='Admitted'")]
    occupied_beds = conn.execute("SELECT id FROM beds WHERE status='Occupied' LIMIT ?", (len(patient_ids),)).fetchall()
    for i, bed in enumerate(occupied_beds):
        if i < len(patient_ids):
            pid = patient_ids[i]
            conn.execute("UPDATE beds SET patient_id=? WHERE id=?", (pid, bed['id']))
            bed_code = conn.execute("SELECT bed_code FROM beds WHERE id=?", (bed['id'],)).fetchone()['bed_code']
            conn.execute("UPDATE patients SET bed_number=? WHERE id=?", (bed_code, pid))

    # ── Blood Inventory ──
    components = ['Whole Blood', 'RBC', 'Plasma', 'Platelets', 'FFP']
    groups = ['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-']
    for grp in groups:
        for comp in components:
            total = random.randint(8, 40)
            avail = random.randint(2, total)
            reserved = random.randint(0, min(3, total - avail))
            exp_days = random.randint(5, 42)
            expiry = (datetime.now() + timedelta(days=exp_days)).strftime('%Y-%m-%d')
            status = 'critical' if avail < 5 else 'low' if avail < 10 else 'normal'
            conn.execute("""INSERT INTO blood_inventory
                (blood_group,component,units_total,units_available,units_reserved,expiry_date,status)
                VALUES (?,?,?,?,?,?,?)""",
                (grp, comp, total, avail, reserved, expiry, status))

    # ── RFID Mobile Equipment ──
    wc_locations = ['Emergency', 'General Ward', 'Radiology', 'Ortho Ward', 'Corridor A', 'Corridor B']
    for i in range(1, 26):
        rfid = f"WC-{uuid.uuid4().hex[:8].upper()}"
        code = f"WC-{i:03d}"
        st = random.choice(['Available', 'Available', 'Available', 'In Use', 'Maintenance'])
        loc = random.choice(wc_locations)
        dept_id = random.randint(1, 8)
        conn.execute("""INSERT INTO mobile_equipment
            (rfid_tag,equipment_type,asset_code,status,current_location,department_id,condition)
            VALUES (?,?,?,?,?,?,?)""",
            (rfid, 'Wheelchair', code, st, loc, dept_id,
             random.choice(['Good', 'Good', 'Good', 'Fair', 'Poor'])))

    str_locations = ['Emergency', 'ICU', 'OT', 'X-Ray', 'General Ward']
    for i in range(1, 16):
        rfid = f"ST-{uuid.uuid4().hex[:8].upper()}"
        code = f"ST-{i:03d}"
        st = random.choice(['Available', 'Available', 'In Use', 'Maintenance'])
        loc = random.choice(str_locations)
        conn.execute("""INSERT INTO mobile_equipment
            (rfid_tag,equipment_type,asset_code,status,current_location,department_id,condition)
            VALUES (?,?,?,?,?,?,?)""",
            (rfid, 'Stretcher', code, st, loc, random.randint(1, 8),
             random.choice(['Good', 'Good', 'Fair'])))

    # ── Life-support: Ventilators & O2 cylinders ──
    admitted_patients = [r['id'] for r in conn.execute(
        "SELECT id FROM patients WHERE status='Admitted' AND severity IN ('Critical','Moderate')")]

    vent_modes = ['SIMV', 'CPAP', 'BiPAP', 'CMV', 'PSV']
    for i in range(1, 21):
        code = f"VENT-{i:03d}"
        if i <= len(admitted_patients) and i <= 8:
            pid = admitted_patients[i - 1]
            dept_id = conn.execute("SELECT department_id FROM patients WHERE id=?", (pid,)).fetchone()['department_id']
            st = 'In Use'
            started = (datetime.now() - timedelta(hours=random.randint(1, 48))).strftime('%Y-%m-%d %H:%M:%S')
            mode = random.choice(vent_modes)
            batt = random.randint(2, 12)
        else:
            pid, dept_id, st, started, mode, batt = None, random.randint(1, 8), 'Available', None, None, random.randint(8, 12)
        conn.execute("""INSERT INTO life_support
            (equipment_type,asset_code,patient_id,department_id,status,flow_rate,started_at,battery_hours)
            VALUES (?,?,?,?,?,?,?,?)""",
            ('Ventilator', code, pid, dept_id, st, mode, started, batt))

    o2_locs = admitted_patients + [None] * 20
    random.shuffle(o2_locs)
    for i in range(1, 51):
        code = f"O2-{i:03d}"
        pid = o2_locs[i - 1] if i <= len(o2_locs) and o2_locs[i - 1] else None
        if pid:
            dept_id = conn.execute("SELECT department_id FROM patients WHERE id=?", (pid,)).fetchone()['department_id']
            st = 'In Use'
            pressure = random.randint(800, 2000)
            started = (datetime.now() - timedelta(hours=random.randint(1, 24))).strftime('%Y-%m-%d %H:%M:%S')
            flow = f"{random.randint(2, 15)}L/min"
        else:
            dept_id, st, pressure, started, flow = random.randint(1, 8), 'Available', random.randint(1500, 2200), None, None
        conn.execute("""INSERT INTO life_support
            (equipment_type,asset_code,patient_id,department_id,status,flow_rate,started_at,pressure_psi)
            VALUES (?,?,?,?,?,?,?,?)""",
            ('Oxygen Cylinder', code, pid, dept_id, st, flow, started, pressure))

    # ── Staff ──
    first_names = ['Dr. Anjali', 'Dr. Rohit', 'Dr. Priya', 'Dr. Suresh', 'Dr. Kavita',
                   'Nurse Rekha', 'Nurse Carlos', 'Nurse Fatima', 'Nurse David', 'Nurse Sunita',
                   'Dr. Vivek', 'Dr. Meena', 'Nurse Pooja', 'Nurse Raj', 'Dr. Kiran',
                   'Nurse Olivia', 'Dr. Patel', 'Nurse Thomas', 'Dr. Sanjay', 'Nurse Grace',
                   'Dr. Ravi', 'Nurse Sophie', 'Dr. Anita', 'Nurse Jun', 'Dr. Mohan']
    last_names = ['Sharma', 'Kumar', 'Singh', 'Patel', 'Gupta',
                  'Rao', 'Santos', 'Ahmed', 'Taylor', 'Nair',
                  'Joshi', 'Verma', 'Das', 'Bose', 'Menon',
                  'Green', 'Mehta', 'Wright', 'Kapoor', 'Lee',
                  'Abbas', 'Laurent', 'Mishra', 'Tanaka', 'Tiwari']
    roles = ['Doctor', 'Doctor', 'Doctor', 'Nurse', 'Nurse', 'Nurse', 'Nurse',
             'Surgeon', 'Technician', 'Specialist']
    shifts = ['Day', 'Day', 'Day', 'Night', 'Night', 'Evening']
    statuses = ['On Duty', 'On Duty', 'On Duty', 'On Duty', 'Off Duty', 'On Leave']
    for i in range(25):
        conn.execute("""INSERT INTO staff (name,role,department_id,shift,status,phone,email) VALUES (?,?,?,?,?,?,?)""",
            (f"{first_names[i]} {last_names[i]}", random.choice(roles),
             random.randint(1, 8), random.choice(shifts), random.choice(statuses),
             f"+91-98{random.randint(10000000,99999999)}",
             f"{first_names[i].split()[-1].lower()}.{last_names[i].lower()}@medbyte.org"))

    # ── Alerts ──
    alerts_data = [
        ('Resource', 'CRITICAL', 'ICU beds critically low — only 3 remaining', 'ICU'),
        ('Resource', 'WARNING',  'Ventilator VENT-009 battery below 3 hours', 'ICU'),
        ('Staff',    'WARNING',  'Night shift understaffed in Emergency', 'Emergency'),
        ('Resource', 'INFO',     'O2 cylinder O2-021 refilled to 2200 PSI', None),
        ('Patient',  'CRITICAL', 'Code Blue — Cardiac arrest Room CA-ICU01', 'Cardiology'),
        ('Resource', 'WARNING',  'Blood group O- critically low (3 units RBC)', None),
        ('Staff',    'INFO',     'Dr. Anjali Sharma shift change at 18:00', None),
        ('Resource', 'CRITICAL', 'Wheelchair WC-007 reported missing (RFID offline)', None),
        ('Patient',  'WARNING',  'Patient overflow in General Ward', 'General Ward'),
        ('System',   'INFO',     'Daily backup completed successfully', None),
    ]
    for a in alerts_data:
        conn.execute("INSERT INTO alerts (type,severity,message,department) VALUES (?,?,?,?)", a)

    # ── Hourly data ──
    hourly = [
        (0, 22, 46, 10), (1, 20, 50, 10), (2, 25, 48, 10), (3, 30, 45, 9),
        (4, 28, 43, 9),  (5, 35, 40, 8),  (6, 45, 35, 8),  (7, 50, 30, 7),
        (8, 60, 25, 25), (9, 70, 20, 26), (10, 80, 15, 25),(11, 85, 12, 25),
        (12, 78, 14, 26),(13, 72, 18, 26),(14, 65, 22, 27),(15, 70, 20, 27),
        (16, 75, 18, 26),(17, 82, 14, 25),(18, 88, 10, 25),(19, 76, 16, 26),
        (20, 60, 24, 17),(21, 45, 32, 18),(22, 35, 38, 9), (23, 28, 42, 9),
    ]
    for h in hourly:
        conn.execute("INSERT INTO hospital_data (hour,patients,beds_available,staff_available) VALUES (?,?,?,?)", h)


# ═══════════════════════════════════════════════
#  QUERY FUNCTIONS
# ═══════════════════════════════════════════════

# ── Hospital Data ──
def insert_hospital_data(hour, patients, beds, staff):
    conn = get_conn()
    conn.execute("INSERT INTO hospital_data (hour,patients,beds_available,staff_available) VALUES (?,?,?,?)",
                 (hour, patients, beds, staff))
    conn.commit()
    conn.close()


def get_hospital_data():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM hospital_data ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Departments ──
def get_departments():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM departments ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Beds ──
def get_beds(dept_id=None, bed_type=None, status=None):
    conn = get_conn()
    sql = """
        SELECT b.*, d.name as dept_name, d.icon as dept_icon,
               p.name as patient_name, p.condition, p.severity, p.admitted_at,
               p.age, p.gender
        FROM beds b
        LEFT JOIN departments d ON b.department_id = d.id
        LEFT JOIN patients p ON b.patient_id = p.id
        WHERE 1=1
    """
    params = []
    if dept_id:
        sql += " AND b.department_id = ?"
        params.append(dept_id)
    if bed_type:
        sql += " AND b.bed_type = ?"
        params.append(bed_type)
    if status:
        sql += " AND b.status = ?"
        params.append(status)
    sql += " ORDER BY b.bed_type, b.bed_code"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_bed(bed_id):
    conn = get_conn()
    row = conn.execute("""
        SELECT b.*, d.name as dept_name, p.name as patient_name,
               p.condition, p.severity, p.admitted_at, p.age, p.gender, p.notes as p_notes
        FROM beds b
        LEFT JOIN departments d ON b.department_id = d.id
        LEFT JOIN patients p ON b.patient_id = p.id
        WHERE b.id = ?
    """, (bed_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_bed_summary():
    conn = get_conn()
    rows = conn.execute("""
        SELECT bed_type,
               COUNT(*) as total,
               SUM(CASE WHEN status='Available' THEN 1 ELSE 0 END) as available,
               SUM(CASE WHEN status='Occupied' THEN 1 ELSE 0 END) as occupied,
               SUM(CASE WHEN status='Maintenance' THEN 1 ELSE 0 END) as maintenance,
               SUM(CASE WHEN status='Reserved' THEN 1 ELSE 0 END) as reserved
        FROM beds WHERE bed_type != 'Emergency'
        GROUP BY bed_type ORDER BY bed_type
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_emergency_bed_summary():
    """Get summary stats for Emergency beds specifically."""
    conn = get_conn()
    row = conn.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN status='Available' THEN 1 ELSE 0 END) as available,
               SUM(CASE WHEN status='Occupied' THEN 1 ELSE 0 END) as occupied,
               SUM(CASE WHEN status='Maintenance' THEN 1 ELSE 0 END) as maintenance
        FROM beds WHERE bed_type='Emergency'
    """).fetchone()
    conn.close()
    return dict(row) if row else {'total': 0, 'available': 0, 'occupied': 0, 'maintenance': 0}


def are_general_beds_full():
    """Check if all General ward beds are occupied/unavailable."""
    conn = get_conn()
    row = conn.execute("""
        SELECT SUM(CASE WHEN status='Available' THEN 1 ELSE 0 END) as available
        FROM beds WHERE bed_type='General'
    """).fetchone()
    conn.close()
    return (row['available'] or 0) == 0


def get_shared_room_summary():
    conn = get_conn()
    rows = conn.execute("""
        SELECT ward,
               COUNT(*) as total,
               SUM(CASE WHEN status='Occupied' THEN 1 ELSE 0 END) as occupied,
               SUM(CASE WHEN status='Available' THEN 1 ELSE 0 END) as available
        FROM beds
        WHERE bed_type='Shared'
        GROUP BY ward
        ORDER BY ward
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_bed_status(bed_id, status, patient_id=None, notes=None):
    conn = get_conn()
    conn.execute("""UPDATE beds SET status=?, patient_id=?, notes=?,
                    last_updated=CURRENT_TIMESTAMP WHERE id=?""",
                 (status, patient_id, notes, bed_id))
    conn.commit()
    conn.close()


def add_bed(bed_code, bed_type, department_id, floor, ward, notes=""):
    conn = get_conn()
    conn.execute("""INSERT INTO beds (bed_code, bed_type, department_id, floor, ward, notes)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                 (bed_code, bed_type, department_id, floor, ward, notes))
    conn.commit()
    conn.close()


def delete_bed(bed_id):
    conn = get_conn()
    conn.execute("DELETE FROM beds WHERE id=?", (bed_id,))
    conn.commit()
    conn.close()


# ── Blood Inventory ──
def get_blood_inventory(blood_group=None, component=None):
    conn = get_conn()
    sql = "SELECT * FROM blood_inventory WHERE 1=1"
    params = []
    if blood_group:
        sql += " AND blood_group=?"
        params.append(blood_group)
    if component:
        sql += " AND component=?"
        params.append(component)
    sql += " ORDER BY blood_group, component"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_blood_summary():
    conn = get_conn()
    rows = conn.execute("""
        SELECT blood_group,
               SUM(units_available) as total_available,
               SUM(units_reserved) as total_reserved,
               SUM(units_total) as total_units,
               GROUP_CONCAT(CASE WHEN status='critical' THEN component END) as critical_components
        FROM blood_inventory
        GROUP BY blood_group
        ORDER BY blood_group
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_blood_inventory(blood_group, component, units_total, units_available, units_reserved, expiry_date):
    status = 'critical' if units_available < 5 else 'low' if units_available < 10 else 'normal'
    conn = get_conn()
    conn.execute("""INSERT INTO blood_inventory (blood_group,component,units_total,units_available,units_reserved,expiry_date,status)
                    VALUES (?,?,?,?,?,?,?)""",
                 (blood_group, component, units_total, units_available, units_reserved, expiry_date, status))
    conn.commit()
    conn.close()


def update_blood_inventory(bid, units_total, units_available, units_reserved, expiry_date):
    status = 'critical' if units_available < 5 else 'low' if units_available < 10 else 'normal'
    conn = get_conn()
    conn.execute("""UPDATE blood_inventory SET units_total=?,units_available=?,units_reserved=?,
                    expiry_date=?,status=?,updated_at=CURRENT_TIMESTAMP WHERE id=?""",
                 (units_total, units_available, units_reserved, expiry_date, status, bid))
    conn.commit()
    conn.close()


def delete_blood_inventory(bid):
    conn = get_conn()
    conn.execute("DELETE FROM blood_inventory WHERE id=?", (bid,))
    conn.commit()
    conn.close()


def reserve_blood_units(blood_group, component, units):
    conn = get_conn()
    conn.execute("""UPDATE blood_inventory
                    SET units_available=MAX(units_available - ?, 0),
                        units_reserved=units_reserved + ?,
                        status=CASE WHEN units_available - ? <= 0 THEN 'critical'
                                    WHEN units_available - ? < 10 THEN 'low'
                                    ELSE 'normal' END,
                        updated_at=CURRENT_TIMESTAMP
                    WHERE blood_group=? AND component=?""",
                 (units, units, units, units, blood_group, component))
    conn.commit()
    conn.close()


def release_blood_units(blood_group, component, units):
    conn = get_conn()
    conn.execute("""UPDATE blood_inventory
                    SET units_available=units_available + ?,
                        units_reserved=MAX(units_reserved - ?, 0),
                        status=CASE WHEN units_available + ? <= 0 THEN 'critical'
                                    WHEN units_available + ? < 10 THEN 'low'
                                    ELSE 'normal' END,
                        updated_at=CURRENT_TIMESTAMP
                    WHERE blood_group=? AND component=?""",
                 (units, units, units, units, blood_group, component))
    conn.commit()
    conn.close()


# ── Mobile Equipment (RFID) ──
def get_mobile_equipment(equipment_type=None, status=None):
    conn = get_conn()
    sql = """
        SELECT me.*, d.name as dept_name,
               p.name as patient_name, p.condition as patient_condition
        FROM mobile_equipment me
        LEFT JOIN departments d ON me.department_id = d.id
        LEFT JOIN patients p ON me.assigned_to_patient = p.id
        WHERE 1=1
    """
    params = []
    if equipment_type:
        sql += " AND me.equipment_type = ?"
        params.append(equipment_type)
    if status:
        sql += " AND me.status = ?"
        params.append(status)
    sql += " ORDER BY me.asset_code"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_mobile_summary():
    conn = get_conn()
    rows = conn.execute("""
        SELECT equipment_type,
               COUNT(*) as total,
               SUM(CASE WHEN status='Available' THEN 1 ELSE 0 END) as available,
               SUM(CASE WHEN status='In Use' THEN 1 ELSE 0 END) as in_use,
               SUM(CASE WHEN status='Maintenance' THEN 1 ELSE 0 END) as maintenance,
               SUM(CASE WHEN status='Missing' THEN 1 ELSE 0 END) as missing
        FROM mobile_equipment
        GROUP BY equipment_type
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_mobile_equipment(equipment_type, asset_code, department_id, current_location, condition_state, notes=''):
    rfid = f"{equipment_type[:2].upper()}-{uuid.uuid4().hex[:8].upper()}"
    conn = get_conn()
    conn.execute("""INSERT INTO mobile_equipment (rfid_tag,equipment_type,asset_code,department_id,current_location,condition,notes)
                    VALUES (?,?,?,?,?,?,?)""",
                 (rfid, equipment_type, asset_code, department_id, current_location, condition_state, notes))
    conn.commit()
    conn.close()


def update_mobile_equipment(mid, status, current_location, department_id, condition_state, assigned_to_patient=None):
    conn = get_conn()
    conn.execute("""UPDATE mobile_equipment SET status=?,current_location=?,department_id=?,
                    condition=?,assigned_to_patient=?,last_seen=CURRENT_TIMESTAMP WHERE id=?""",
                 (status, current_location, department_id, condition_state, assigned_to_patient, mid))
    conn.commit()
    conn.close()


def delete_mobile_equipment(mid):
    conn = get_conn()
    conn.execute("DELETE FROM mobile_equipment WHERE id=?", (mid,))
    conn.commit()
    conn.close()


# ── Life Support ──
def get_life_support(equipment_type=None, status=None):
    conn = get_conn()
    sql = """
        SELECT ls.*, d.name as dept_name,
               p.name as patient_name, p.condition, p.severity, p.bed_number,
               p.age, p.gender
        FROM life_support ls
        LEFT JOIN departments d ON ls.department_id = d.id
        LEFT JOIN patients p ON ls.patient_id = p.id
        WHERE 1=1
    """
    params = []
    if equipment_type:
        sql += " AND ls.equipment_type = ?"
        params.append(equipment_type)
    if status:
        sql += " AND ls.status = ?"
        params.append(status)
    sql += " ORDER BY ls.equipment_type, ls.asset_code"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_life_support_summary():
    conn = get_conn()
    rows = conn.execute("""
        SELECT equipment_type,
               COUNT(*) as total,
               SUM(CASE WHEN status='In Use' THEN 1 ELSE 0 END) as in_use,
               SUM(CASE WHEN status='Available' THEN 1 ELSE 0 END) as available,
               SUM(CASE WHEN status='Maintenance' THEN 1 ELSE 0 END) as maintenance
        FROM life_support
        GROUP BY equipment_type
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_life_support(equipment_type, asset_code, department_id, notes=''):
    conn = get_conn()
    conn.execute("INSERT INTO life_support (equipment_type,asset_code,department_id,notes) VALUES (?,?,?,?)",
                 (equipment_type, asset_code, department_id, notes))
    conn.commit()
    conn.close()


def update_life_support(lid, status, patient_id, department_id, flow_rate, pressure_psi, battery_hours, notes):
    st_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S') if patient_id else None
    conn = get_conn()
    conn.execute("""UPDATE life_support SET status=?,patient_id=?,department_id=?,flow_rate=?,
                    pressure_psi=?,battery_hours=?,notes=?,started_at=?,updated_at=CURRENT_TIMESTAMP WHERE id=?""",
                 (status, patient_id, department_id, flow_rate, pressure_psi or None, battery_hours or None, notes, st_time, lid))
    conn.commit()
    conn.close()


def delete_life_support(lid):
    conn = get_conn()
    conn.execute("DELETE FROM life_support WHERE id=?", (lid,))
    conn.commit()
    conn.close()


# ── Resources (legacy) ──
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
        SET available=?, in_use=?, maintenance=?,
            status=CASE WHEN ?=0 THEN 'critical'
                        WHEN CAST(? AS FLOAT)/NULLIF(total,0)<0.2 THEN 'warning'
                        ELSE 'normal' END,
            updated_at=CURRENT_TIMESTAMP
        WHERE id=?
    """, (available, in_use, maintenance, available, available, resource_id))
    conn.commit()
    conn.close()


def get_resource_summary():
    conn = get_conn()
    rows = conn.execute("""
        SELECT category,
               SUM(total) as total, SUM(available) as available,
               SUM(in_use) as in_use, SUM(maintenance) as maintenance
        FROM resources GROUP BY category
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_resource(name, category, department_id, total, available, in_use, maintenance):
    status = 'normal'
    if available == 0:
        status = 'critical'
    elif total and available / total < 0.2:
        status = 'warning'
        
    conn = get_conn()
    conn.execute("""
        INSERT INTO resources (name, category, department_id, total, available, in_use, maintenance, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, category, department_id, total, available, in_use, maintenance, status))
    conn.commit()
    conn.close()


def delete_resource(resource_id):
    conn = get_conn()
    conn.execute("DELETE FROM resources WHERE id=?", (resource_id,))
    conn.commit()
    conn.close()


# ── Staff ──
def get_staff():
    conn = get_conn()
    rows = conn.execute("""
        SELECT s.*, d.name as department_name
        FROM staff s LEFT JOIN departments d ON s.department_id = d.id ORDER BY s.name
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_staff_on_duty():
    conn = get_conn()
    row = conn.execute("SELECT COUNT(*) as count FROM staff WHERE status='On Duty'").fetchone()
    conn.close()
    return row['count'] if row else 0


def get_staff_summary():
    conn = get_conn()
    rows = conn.execute("""
        SELECT role, COUNT(*) as count,
               SUM(CASE WHEN status='On Duty' THEN 1 ELSE 0 END) as on_duty
        FROM staff GROUP BY role
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_staff(name, role, department_id, shift, status, phone, email):
    conn = get_conn()
    conn.execute("""INSERT INTO staff (name,role,department_id,shift,status,phone,email)
                    VALUES (?,?,?,?,?,?,?)""",
                 (name, role, department_id, shift, status, phone, email))
    conn.commit()
    conn.close()


def update_staff(sid, name, role, department_id, shift, status, phone, email):
    conn = get_conn()
    conn.execute("""UPDATE staff SET name=?,role=?,department_id=?,shift=?,status=?,phone=?,email=?
                    WHERE id=?""",
                 (name, role, department_id, shift, status, phone, email, sid))
    conn.commit()
    conn.close()


def delete_staff(sid):
    conn = get_conn()
    conn.execute("DELETE FROM staff WHERE id=?", (sid,))
    conn.commit()
    conn.close()


def generate_real_alerts():
    """Scan resources and patients to produce real-time alerts."""
    alerts = []
    conn = get_conn()

    # 1. Critical patients
    crit_patients = conn.execute(
        "SELECT name, condition, department_id FROM patients WHERE severity='Critical' AND status='Admitted'"
    ).fetchall()
    for p in crit_patients:
        dept = conn.execute("SELECT name FROM departments WHERE id=?", (p['department_id'],)).fetchone()
        dept_name = dept['name'] if dept else None
        alerts.append({
            'type': 'Patient', 'severity': 'CRITICAL',
            'message': f"Critical patient: {p['name']} — {p['condition']}",
            'department': dept_name, 'id': None, 'acknowledged': 0, 'created_at': 'Live'
        })

    # 2. Blood inventory critical
    blood_crit = conn.execute(
        "SELECT blood_group, component, units_available FROM blood_inventory WHERE units_available < 5"
    ).fetchall()
    for b in blood_crit:
        alerts.append({
            'type': 'Resource', 'severity': 'CRITICAL',
            'message': f"Blood {b['blood_group']} {b['component']}: only {b['units_available']} units left",
            'department': None, 'id': None, 'acknowledged': 0, 'created_at': 'Live'
        })

    # 3. Bed type at capacity
    bed_types = conn.execute("""
        SELECT bed_type, COUNT(*) as total,
               SUM(CASE WHEN status='Available' THEN 1 ELSE 0 END) as available
        FROM beds GROUP BY bed_type
    """).fetchall()
    for bt in bed_types:
        if (bt['available'] or 0) == 0:
            alerts.append({
                'type': 'Resource', 'severity': 'CRITICAL',
                'message': f"{bt['bed_type']} beds fully occupied — {bt['total']} total, 0 available",
                'department': None, 'id': None, 'acknowledged': 0, 'created_at': 'Live'
            })
        elif (bt['available'] or 0) <= 2:
            alerts.append({
                'type': 'Resource', 'severity': 'WARNING',
                'message': f"{bt['bed_type']} beds critically low — only {bt['available']} of {bt['total']} available",
                'department': None, 'id': None, 'acknowledged': 0, 'created_at': 'Live'
            })

    # 4. Equipment in maintenance
    maint_equip = conn.execute(
        "SELECT asset_code, equipment_type FROM life_support WHERE status='Maintenance'"
    ).fetchall()
    for eq in maint_equip:
        alerts.append({
            'type': 'Resource', 'severity': 'WARNING',
            'message': f"{eq['equipment_type']} {eq['asset_code']} is under maintenance",
            'department': None, 'id': None, 'acknowledged': 0, 'created_at': 'Live'
        })

    # 5. Missing/maintenance RFID equipment
    rfid_issues = conn.execute(
        "SELECT asset_code, equipment_type, status FROM mobile_equipment WHERE status IN ('Maintenance','Missing')"
    ).fetchall()
    for eq in rfid_issues:
        sev = 'CRITICAL' if eq['status'] == 'Missing' else 'WARNING'
        alerts.append({
            'type': 'Resource', 'severity': sev,
            'message': f"{eq['equipment_type']} {eq['asset_code']} — {eq['status']}",
            'department': None, 'id': None, 'acknowledged': 0, 'created_at': 'Live'
        })

    # 6. Beds in maintenance
    maint_beds = conn.execute(
        "SELECT bed_code, bed_type FROM beds WHERE status='Maintenance'"
    ).fetchall()
    if len(maint_beds) > 3:
        alerts.append({
            'type': 'Resource', 'severity': 'WARNING',
            'message': f"{len(maint_beds)} beds currently under maintenance",
            'department': None, 'id': None, 'acknowledged': 0, 'created_at': 'Live'
        })

    conn.close()
    # Sort: CRITICAL first, then WARNING, then INFO
    order = {'CRITICAL': 0, 'WARNING': 1, 'INFO': 2}
    alerts.sort(key=lambda a: order.get(a['severity'], 3))
    return alerts


# ── Patients ──
def get_patients(status_filter=None):
    conn = get_conn()
    sql = """
        SELECT p.*, d.name as department_name,
               s.name as assigned_staff_name,
               v.asset_code as assigned_ventilator_code,
               o.asset_code as assigned_oxygen_code
        FROM patients p
        LEFT JOIN departments d ON p.department_id = d.id
        LEFT JOIN staff s ON p.assigned_staff_id = s.id
        LEFT JOIN life_support v ON p.assigned_ventilator_id = v.id
        LEFT JOIN life_support o ON p.assigned_oxygen_id = o.id
        WHERE 1=1
    """
    params = []
    if status_filter:
        sql += " AND p.status=?"
        params.append(status_filter)
    sql += " ORDER BY p.admitted_at DESC"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_patient(name, age, gender, condition, severity, department_id, bed_number, notes="",
                assigned_staff_id=None, assigned_ventilator_id=None, assigned_oxygen_id=None,
                blood_group=None, blood_component=None, blood_units=0):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""INSERT INTO patients
        (name,age,gender,condition,severity,department_id,bed_number,assigned_staff_id,assigned_ventilator_id,
         assigned_oxygen_id,blood_group,blood_component,blood_units,notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (name, age, gender, condition, severity, department_id, bed_number,
         assigned_staff_id, assigned_ventilator_id, assigned_oxygen_id,
         blood_group, blood_component, blood_units, notes))
    patient_id = cur.lastrowid
    conn.commit()
    conn.close()
    return patient_id


def discharge_patient(patient_id):
    conn = get_conn()
    patient = conn.execute("SELECT bed_number, assigned_ventilator_id, assigned_oxygen_id, assigned_staff_id, blood_group, blood_component, blood_units FROM patients WHERE id=?", (patient_id,)).fetchone()
    if patient:
        # Free assigned bed
        conn.execute("UPDATE beds SET status='Available', patient_id=NULL WHERE id=(SELECT id FROM beds WHERE bed_code=?)", (patient['bed_number'],))

        # Free ventilator and oxygen
        if patient['assigned_ventilator_id']:
            conn.execute("UPDATE life_support SET status='Available', patient_id=NULL, started_at=NULL WHERE id=?", (patient['assigned_ventilator_id'],))
        if patient['assigned_oxygen_id']:
            conn.execute("UPDATE life_support SET status='Available', patient_id=NULL, started_at=NULL WHERE id=?", (patient['assigned_oxygen_id'],))

        # Free staff link (no status change for staff)
        # Return any reserved blood units to available pool
        if patient['blood_group'] and patient['blood_component'] and patient['blood_units']:
            conn.execute("""UPDATE blood_inventory
                            SET units_available=units_available + ?,
                                units_reserved=MAX(units_reserved - ?, 0),
                                status = CASE
                                    WHEN units_available + ? <= 0 THEN 'critical'
                                    WHEN units_available + ? < 10 THEN 'low'
                                    ELSE 'normal'
                                END,
                                updated_at=CURRENT_TIMESTAMP
                            WHERE blood_group=? AND component=?""",
                         (patient['blood_units'], patient['blood_units'], patient['blood_units'], patient['blood_units'], patient['blood_group'], patient['blood_component']))

    conn.execute("""UPDATE patients SET status='Discharged', discharged_at=CURRENT_TIMESTAMP,
                    bed_number=NULL, assigned_staff_id=NULL, assigned_ventilator_id=NULL,
                    assigned_oxygen_id=NULL, blood_group=NULL, blood_component=NULL, blood_units=0
                    WHERE id=?""", (patient_id,))

    conn.commit()
    conn.close()

def get_patient_counts():
    conn = get_conn()
    row = conn.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN status='Admitted' THEN 1 ELSE 0 END) as admitted,
               SUM(CASE WHEN severity='Critical' AND status='Admitted' THEN 1 ELSE 0 END) as critical,
               SUM(CASE WHEN status='Discharged' THEN 1 ELSE 0 END) as discharged
        FROM patients
    """).fetchone()
    conn.close()
    return dict(row) if row else {'total': 0, 'admitted': 0, 'critical': 0, 'discharged': 0}


def update_patient(pid, name, age, gender, condition, severity, department_id, bed_number,
                   notes, status, assigned_staff_id=None, assigned_ventilator_id=None,
                   assigned_oxygen_id=None, blood_group=None, blood_component=None, blood_units=0):
    conn = get_conn()
    conn.execute("""UPDATE patients SET name=?,age=?,gender=?,condition=?,severity=?,
                    department_id=?,bed_number=?,notes=?,status=?,assigned_staff_id=?,
                    assigned_ventilator_id=?,assigned_oxygen_id=?,blood_group=?,blood_component=?,blood_units=?
                    WHERE id=?""",
                 (name, age, gender, condition, severity, department_id, bed_number,
                  notes, status, assigned_staff_id, assigned_ventilator_id,
                  assigned_oxygen_id, blood_group, blood_component, blood_units, pid))
    conn.commit()
    conn.close()


def delete_patient(pid):
    conn = get_conn()
    conn.execute("UPDATE beds SET status='Available',patient_id=NULL WHERE patient_id=?", (pid,))
    conn.execute("UPDATE life_support SET patient_id=NULL,status='Available' WHERE patient_id=?", (pid,))
    conn.execute("UPDATE mobile_equipment SET assigned_to_patient=NULL WHERE assigned_to_patient=?", (pid,))
    conn.execute("DELETE FROM patients WHERE id=?", (pid,))
    conn.commit()
    conn.close()


# ── Alerts ──
def get_alerts(pending_only=False):
    conn = get_conn()
    if pending_only:
        rows = conn.execute("SELECT * FROM alerts WHERE acknowledged=0 ORDER BY created_at DESC").fetchall()
    else:
        rows = conn.execute("SELECT * FROM alerts ORDER BY created_at DESC LIMIT 50").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_alert(alert_type, severity, message, department=None):
    conn = get_conn()
    conn.execute("INSERT INTO alerts (type,severity,message,department) VALUES (?,?,?,?)",
                 (alert_type, severity, message, department))
    conn.commit()
    conn.close()


def acknowledge_alert(alert_id, acknowledged_by="Admin"):
    conn = get_conn()
    conn.execute("""UPDATE alerts SET acknowledged=1, acknowledged_by=?,
                    acknowledged_at=CURRENT_TIMESTAMP WHERE id=?""",
                 (acknowledged_by, alert_id))
    conn.commit()
    conn.close()


def get_alert_counts():
    conn = get_conn()
    row = conn.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN acknowledged=0 THEN 1 ELSE 0 END) as pending,
               SUM(CASE WHEN severity='CRITICAL' AND acknowledged=0 THEN 1 ELSE 0 END) as critical
        FROM alerts
    """).fetchone()
    conn.close()
    return dict(row) if row else {'total': 0, 'pending': 0, 'critical': 0}