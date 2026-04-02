"""
MedByte — AI-Based Hospital Resource Optimization System
Problem Statement 23
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime
import os

from database import (
    create_db, seed_data,
    get_departments,
    # Beds
    get_beds, get_bed, get_bed_summary, get_emergency_bed_summary, are_general_beds_full, update_bed_status, add_bed, delete_bed,
    # Blood
    get_blood_inventory, get_blood_summary, add_blood_inventory, update_blood_inventory, delete_blood_inventory, reserve_blood_units, release_blood_units,
    # Mobile / RFID
    get_mobile_equipment, get_mobile_summary, add_mobile_equipment, update_mobile_equipment, delete_mobile_equipment,
    # Life support
    get_life_support, get_life_support_summary, add_life_support, update_life_support, delete_life_support,
    # Hospital Equipment & Services
    get_resources, get_resources_by_category, get_resource_category_summary,
    update_resource, get_resource_summary, add_resource, edit_resource, delete_resource,
    toggle_resource_maintenance,
    # Trauma Bays
    get_trauma_bays, get_trauma_summary, add_trauma_bay, update_trauma_bay, delete_trauma_bay,
    # Staff
    get_staff, get_staff_on_duty, get_staff_summary, add_staff, update_staff, delete_staff,
    # Patients
    get_patients, add_patient, discharge_patient, get_patient_counts, update_patient, delete_patient,
    is_patient_on_ventilator, wean_off_ventilator,
    # Alerts
    get_alerts, add_alert, acknowledge_alert, get_alert_counts, generate_real_alerts,
    # Data
    insert_hospital_data, get_setting, set_setting, migrate_schema,
)
from decision import generate_recommendations, generate_alert
from ml.model import load_or_train
from ml.predictor import get_predictions, get_24h_forecast, get_monthly_trend

app = Flask(__name__)
app.secret_key = 'medcore-ai-hospital-2026-secret'

# ── Startup ──
create_db()
migrate_schema()
seed_data()

print("[ML] Loading / training models...")
ML_BUNDLE = load_or_train()
print("[OK] ML models ready.")


# ─────────────────────────────────────
#  Helpers
# ─────────────────────────────────────
def _pa():
    return get_alert_counts().get('pending', 0)


def _current_state():
    resources = get_resources()
    beds_avail = sum(r['available'] for r in resources if r['category'] == 'Beds')
    beds_total = sum(r['total'] for r in resources if r['category'] == 'Beds')
    # Fall back to bed table counts if resources table is empty
    if beds_total == 0:
        bed_summ = get_bed_summary()
        beds_avail = sum(b['available'] for b in bed_summ)
        beds_total = sum(b['total'] for b in bed_summ)

    beds_occ = beds_total - beds_avail

    icu_res = [r for r in resources if 'ICU' in r.get('name', '')]
    icu_occ  = sum(r['in_use'] for r in icu_res) if icu_res else 8
    icu_avail = sum(r['available'] for r in icu_res) if icu_res else 12

    equip = [r for r in resources if r['category'] == 'Equipment']
    equip_in_use = sum(r['in_use'] for r in equip) if equip else 12

    sod = get_staff_on_duty()
    now = datetime.now()
    return {
        "hour": now.hour, "day_of_week": now.weekday(), "month": now.month,
        "beds_available": beds_avail, "beds_occupied": beds_occ,
        "icu_occupied": icu_occ, "icu_available": icu_avail,
        "staff_count": sod, "er_arrivals": 5, "equipment_in_use": equip_in_use,
    }


@app.context_processor
def inject_theme():
    return {'theme': get_setting('theme', 'dark')}


# ─────────────────────────────────────
#  Dashboard
# ─────────────────────────────────────
@app.route('/')
def dashboard():
    state    = _current_state()
    pred     = get_predictions(ML_BUNDLE, state)
    forecast = get_24h_forecast(ML_BUNDLE, state)

    bed_summ  = get_bed_summary()
    beds_avail = sum(b['available'] for b in bed_summ)
    beds_total = sum(b['total'] for b in bed_summ)
    bed_util   = round((1 - beds_avail / max(beds_total, 1)) * 100, 1)

    res_summary = get_resource_summary()
    ls_summary  = get_life_support_summary()
    pc  = get_patient_counts()
    sod = get_staff_on_duty()
    ts  = len(get_staff())
    recs = generate_recommendations(pred, get_resources(), sod)

    # Chart data
    rl = [s['category'] for s in res_summary] + [s['equipment_type'] for s in ls_summary]
    rd = [s['in_use'] for s in res_summary] + [s['in_use'] for s in ls_summary]

    # Live alerts
    from database import generate_real_alerts, get_icu_transfer_candidates
    live_alerts = generate_real_alerts()[:5]
    icu_transfers = get_icu_transfer_candidates()

    return render_template('dashboard.html',
        page='dashboard', pa=_pa(),
        pc=pc, ba=beds_avail, bt=beds_total, bu=bed_util, sod=sod, ts=ts,
        pred=pred, alerts=live_alerts, recs=recs,
        forecast_labels=[f['label'] for f in forecast],
        forecast_patients=[f['patients'] for f in forecast],
        forecast_beds=[f['beds_needed'] for f in forecast],
        rl=rl, rd=rd,
        bed_type_labels=[s['bed_type'] for s in bed_summ],
        bed_type_occ=[s['total'] - s['available'] for s in bed_summ],
        bed_type_avail=[s['available'] for s in bed_summ],
        icu_transfers=icu_transfers,
    )


# ─────────────────────────────────────
#  Resources (full overhaul)
# ─────────────────────────────────────
@app.route('/resources')
def resources_page():
    bed_summ    = get_bed_summary()
    beds        = get_beds()
    blood_summ  = get_blood_summary()
    blood_inv   = get_blood_inventory()
    mobile_summ = get_mobile_summary()
    mobiles     = get_mobile_equipment()
    ls_summ     = get_life_support_summary()
    ls_items    = get_life_support()

    # Group beds by type (exclude Emergency — they get their own section)
    bed_by_type = {}
    emergency_beds = []
    for b in beds:
        if b['bed_type'] == 'Emergency':
            emergency_beds.append(b)
        else:
            bed_by_type.setdefault(b['bed_type'], []).append(b)

    # Group blood by group
    blood_by_group = {}
    for item in blood_inv:
        blood_by_group.setdefault(item['blood_group'], []).append(item)

    # Group life-support by type
    ls_by_type = {}
    for item in ls_items:
        ls_by_type.setdefault(item['equipment_type'], []).append(item)

    # Group mobile by type
    mob_by_type = {}
    for item in mobiles:
        mob_by_type.setdefault(item['equipment_type'], []).append(item)

    # Emergency bed data
    em_summ = get_emergency_bed_summary()
    general_full = are_general_beds_full()

    return render_template('resources.html',
        page='resources', pa=_pa(),
        bed_summ=bed_summ, bed_by_type=bed_by_type,
        emergency_beds=emergency_beds, em_summ=em_summ, general_full=general_full,
        blood_summ=blood_summ, blood_by_group=blood_by_group,
        mobile_summ=mobile_summ, mob_by_type=mob_by_type,
        ls_summ=ls_summ, ls_by_type=ls_by_type,
        res_by_category=get_resources_by_category(),
        res_cat_summary=get_resource_category_summary(),
        trauma_bays=get_trauma_bays(),
        trauma_summ=get_trauma_summary(),
        depts=get_departments(),
    )


@app.route('/resources/bed/<int:bed_id>')
def bed_detail(bed_id):
    bed = get_bed(bed_id)
    if not bed:
        flash('Bed not found.', 'error')
        return redirect(url_for('resources_page'))
    return render_template('bed_detail.html', page='resources', pa=_pa(), bed=bed)


@app.route('/resources/bed/<int:bed_id>/update', methods=['POST'])
def bed_update(bed_id):
    status     = request.form.get('status', 'Available')
    patient_id = request.form.get('patient_id') or None
    notes      = request.form.get('notes', '')
    update_bed_status(bed_id, status, patient_id, notes)
    flash('Bed status updated.', 'success')
    return redirect(url_for('resources_page'))


@app.route('/resources/bed/add', methods=['POST'])
def bed_add():
    bed_code  = request.form.get('bed_code', '')
    bed_type  = request.form.get('bed_type', '')
    dept_id   = request.form.get('department_id', type=int)
    floor     = request.form.get('floor', type=int)
    ward      = request.form.get('ward', '')
    notes     = request.form.get('notes', '')
    if bed_code and bed_type:
        add_bed(bed_code, bed_type, dept_id, floor, ward, notes)
        flash('Bed added.', 'success')
    return redirect(url_for('resources_page'))


@app.route('/resources/bed/<int:bed_id>/delete', methods=['POST'])
def bed_delete_route(bed_id):
    delete_bed(bed_id)
    flash('Bed deleted.', 'success')
    return redirect(url_for('resources_page'))


@app.route('/resources/blood/add', methods=['POST'])
def blood_add():
    grp   = request.form.get('blood_group', '')
    comp  = request.form.get('component', '')
    total = request.form.get('units_total', type=int)
    avail = request.form.get('units_available', type=int)
    reser = request.form.get('units_reserved', type=int)
    exp   = request.form.get('expiry_date', '')
    if grp and comp:
        add_blood_inventory(grp, comp, total, avail, reser, exp)
        flash('Blood inventory added.', 'success')
    return redirect(url_for('resources_page'))


@app.route('/resources/blood/<int:bid>/update', methods=['POST'])
def blood_update(bid):
    total = request.form.get('units_total', type=int)
    avail = request.form.get('units_available', type=int)
    reser = request.form.get('units_reserved', type=int)
    exp   = request.form.get('expiry_date', '')
    update_blood_inventory(bid, total, avail, reser, exp)
    flash('Blood inventory updated.', 'success')
    return redirect(url_for('resources_page'))


@app.route('/resources/blood/<int:bid>/delete', methods=['POST'])
def blood_delete_route(bid):
    delete_blood_inventory(bid)
    flash('Blood inventory deleted.', 'success')
    return redirect(url_for('resources_page'))


@app.route('/resources/mobile/add', methods=['POST'])
def mobile_add():
    eq_type  = request.form.get('equipment_type', '')
    asset    = request.form.get('asset_code', '')
    dept_id  = request.form.get('department_id', type=int)
    loc      = request.form.get('current_location', '')
    cond     = request.form.get('condition', 'Good')
    notes    = request.form.get('notes', '')
    if eq_type and asset:
        add_mobile_equipment(eq_type, asset, dept_id, loc, cond, notes)
        flash('Mobile equipment added.', 'success')
    return redirect(url_for('resources_page'))


@app.route('/resources/mobile/<int:mid>/update', methods=['POST'])
def mobile_update(mid):
    status   = request.form.get('status', 'Available')
    loc      = request.form.get('current_location', '')
    dept_id  = request.form.get('department_id', type=int)
    cond     = request.form.get('condition', 'Good')
    pat_id   = request.form.get('assigned_to_patient') or None
    update_mobile_equipment(mid, status, loc, dept_id, cond, pat_id)
    flash('Mobile equipment updated.', 'success')
    return redirect(url_for('resources_page'))


@app.route('/resources/mobile/<int:mid>/delete', methods=['POST'])
def mobile_delete_route(mid):
    delete_mobile_equipment(mid)
    flash('Mobile equipment deleted.', 'success')
    return redirect(url_for('resources_page'))


@app.route('/resources/life_support/add', methods=['POST'])
def ls_add():
    eq_type  = request.form.get('equipment_type', '')
    asset    = request.form.get('asset_code', '')
    dept_id  = request.form.get('department_id', type=int)
    notes    = request.form.get('notes', '')
    if eq_type and asset:
        add_life_support(eq_type, asset, dept_id, notes)
        flash('Life support equipment added.', 'success')
    return redirect(url_for('resources_page'))


@app.route('/resources/life_support/<int:lid>/update', methods=['POST'])
def ls_update(lid):
    status   = request.form.get('status', 'Available')
    pat_id   = request.form.get('patient_id') or None
    dept_id  = request.form.get('department_id', type=int)
    flow     = request.form.get('flow_rate', '')
    press    = request.form.get('pressure_psi', type=int)
    batt     = request.form.get('battery_hours', type=int)
    notes    = request.form.get('notes', '')
    update_life_support(lid, status, pat_id, dept_id, flow, press, batt, notes)
    flash('Life support updated.', 'success')
    return redirect(url_for('resources_page'))


@app.route('/resources/life_support/<int:lid>/delete', methods=['POST'])
def ls_delete_route(lid):
    delete_life_support(lid)
    flash('Life support deleted.', 'success')
    return redirect(url_for('resources_page'))


@app.route('/resources/add', methods=['POST'])
def resources_add():
    name = request.form.get('name', '')
    category = request.form.get('category', '')
    department_id = request.form.get('department_id', type=int) or None
    total = request.form.get('total', type=int, default=0)
    available = request.form.get('available', type=int, default=0)
    in_use = request.form.get('in_use', type=int, default=0)
    maintenance = request.form.get('maintenance', type=int, default=0)
    location = request.form.get('location', '')
    if name and category:
        add_resource(name, category, department_id, total, available, in_use, maintenance, location)
        flash('Equipment added.', 'success')
    return redirect(url_for('resources_page'))


@app.route('/resources/<int:rid>/edit', methods=['POST'])
def resources_edit(rid):
    name = request.form.get('name', '')
    category = request.form.get('category', '')
    department_id = request.form.get('department_id', type=int) or None
    total = request.form.get('total', type=int, default=0)
    available = request.form.get('available', type=int, default=0)
    in_use = request.form.get('in_use', type=int, default=0)
    maintenance = request.form.get('maintenance', type=int, default=0)
    location = request.form.get('location', '')
    if name and category:
        edit_resource(rid, name, category, department_id, total, available, in_use, maintenance, location)
        flash('Equipment updated.', 'success')
    return redirect(url_for('resources_page'))


@app.route('/resources/<int:rid>/delete', methods=['POST'])
def resources_delete(rid):
    delete_resource(rid)
    flash('Equipment removed.', 'success')
    return redirect(url_for('resources_page'))


@app.route('/resources/update', methods=['POST'])
def resources_update():
    rid    = request.form.get('resource_id', type=int)
    avail  = request.form.get('available',   type=int, default=0)
    in_use = request.form.get('in_use',      type=int, default=0)
    maint  = request.form.get('maintenance', type=int, default=0)
    if rid:
        update_resource(rid, avail, in_use, maint)
        flash('Equipment updated.', 'success')
    return redirect(url_for('resources_page'))


@app.route('/resources/<int:rid>/toggle_maint', methods=['POST'])
def resources_toggle_maint(rid):
    action = request.form.get('action', 'to_maint')
    toggle_resource_maintenance(rid, action)
    flash('Maintenance status updated.', 'success')
    return redirect(url_for('resources_page'))


# ── Trauma Bay routes ──
@app.route('/resources/trauma/add', methods=['POST'])
def trauma_add():
    name = request.form.get('bay_name', '')
    level = request.form.get('level', 'Level II')
    notes = request.form.get('notes', '')
    if name:
        success = add_trauma_bay(name, level, notes)
        if success:
            flash('Trauma bay added.', 'success')
        else:
            flash(f"Trauma bay '{name}' already exists or failed to add.", 'error')
    return redirect(url_for('resources_page'))


@app.route('/resources/trauma/<int:tid>/update', methods=['POST'])
def trauma_update(tid):
    status = request.form.get('status', 'Available')
    case = request.form.get('current_case', '') or None
    nurse = request.form.get('nurse', '') or None
    doctor = request.form.get('doctor', '') or None
    notes = request.form.get('notes', '') or None
    triage = request.form.get('triage_class', 'Level II')
    blood = request.form.get('blood_ready', 'Pending Crossmatch')
    imaging = request.form.get('imaging_status', 'Pending')

    update_trauma_bay(tid, status, current_case=case, nurse=nurse, doctor=doctor, notes=notes, triage=triage, blood=blood, imaging=imaging)
    flash('Trauma bay updated.', 'success')
    return redirect(url_for('resources_page'))


@app.route('/resources/trauma/<int:tid>/delete', methods=['POST'])
def trauma_delete(tid):
    delete_trauma_bay(tid)
    flash('Trauma bay removed.', 'success')
    return redirect(url_for('resources_page'))


# API: bed detail JSON
@app.route('/api/bed/<int:bed_id>')
def api_bed(bed_id):
    bed = get_bed(bed_id)
    return jsonify(bed) if bed else ('Not found', 404)


# API: RFID device JSON
@app.route('/api/rfid/<asset_code>')
def api_rfid(asset_code):
    items = get_mobile_equipment()
    item  = next((i for i in items if i['asset_code'] == asset_code), None)
    return jsonify(item) if item else ('Not found', 404)


# ─────────────────────────────────────
#  Patients
# ─────────────────────────────────────
@app.route('/patients')
def patients_page():
    available_beds = get_beds(status='Available')
    available_vents = get_life_support(equipment_type='Ventilator', status='Available')
    available_ox = get_life_support(equipment_type='Oxygen Cylinder', status='Available')
    available_staff = [s for s in get_staff() if s['status'] == 'On Duty']

    return render_template('patients.html',
        page='patients', pa=_pa(),
        patients=get_patients(), cn=get_patient_counts(), depts=get_departments(),
        available_beds=available_beds,
        available_vents=available_vents,
        available_ox=available_ox,
        available_staff=available_staff,
    )


@app.route('/patients/add', methods=['POST'])
def patients_add():
    name      = request.form.get('name', '')
    age       = request.form.get('age', type=int)
    gender    = request.form.get('gender', 'M')
    condition = request.form.get('condition', '')
    severity  = request.form.get('severity', 'Stable')
    dept_id   = request.form.get('department_id', type=int)
    bed_id    = request.form.get('bed_id', type=int)
    notes     = request.form.get('notes', '')

    staff_id  = request.form.get('staff_id', type=int)
    ventilator_id  = request.form.get('ventilator_id', type=int)
    oxygen_id      = request.form.get('oxygen_id', type=int)

    blood_group   = request.form.get('blood_group')
    blood_component = request.form.get('blood_component')
    blood_units   = request.form.get('blood_units', type=int, default=0)

    bed_number = ''
    if bed_id:
        bed_record = get_bed(bed_id)
        if bed_record:
            bed_number = bed_record['bed_code']

    if name:
        pid = add_patient(name, age, gender, condition, severity, dept_id, bed_number, notes,
                          assigned_staff_id=staff_id,
                          assigned_ventilator_id=ventilator_id,
                          assigned_oxygen_id=oxygen_id,
                          blood_group=blood_group,
                          blood_component=blood_component,
                          blood_units=blood_units or 0)

        if bed_id and bed_record:
            update_bed_status(bed_id, 'Occupied', pid, notes=f'Assigned to {name}')

        if ventilator_id:
            update_life_support(ventilator_id, 'In Use', pid, dept_id, 'SIMV', None, None, f'Assigned to {name}')
        if oxygen_id:
            update_life_support(oxygen_id, 'In Use', pid, dept_id, f'{blood_units or 5}L/min', None, None, f'Assigned to {name}')

        if blood_group and blood_component and blood_units and blood_units > 0:
            reserve_blood_units(blood_group, blood_component, blood_units)

        flash(f'Patient {name} admitted with resources assigned.', 'success')
    return redirect(url_for('patients_page'))


@app.route('/patients/discharge/<int:pid>', methods=['POST'])
def patients_discharge(pid):
    if is_patient_on_ventilator(pid):
        flash('Cannot discharge — patient is on a ventilator. Wean off the ventilator first.', 'error')
        if request.headers.get('X-Requested-With'):
            return ('Cannot discharge — patient is on a ventilator', 400)
        return redirect(url_for('patients_page'))
    result = discharge_patient(pid)
    if result:
        flash('Patient discharged.', 'success')
    else:
        flash('Discharge failed — patient may still have active ventilator.', 'error')
    if request.headers.get('X-Requested-With'):
        return ('', 200 if result else 400)
    return redirect(url_for('patients_page'))


@app.route('/patients/wean/<int:pid>', methods=['POST'])
def patients_wean(pid):
    wean_off_ventilator(pid)
    flash('Ventilator weaned off successfully. Patient can now be discharged.', 'success')
    return redirect(url_for('patients_page'))


@app.route('/patients/update/<int:pid>', methods=['POST'])
def patients_update(pid):
    name      = request.form.get('name', '')
    age       = request.form.get('age', type=int)
    gender    = request.form.get('gender', 'M')
    condition = request.form.get('condition', '')
    severity  = request.form.get('severity', 'Stable')
    dept_id   = request.form.get('department_id', type=int)
    bed_id    = request.form.get('bed_id', type=int)
    bed       = request.form.get('bed_number', '')
    notes     = request.form.get('notes', '')
    status    = request.form.get('status', 'Admitted')

    assigned_staff_id = request.form.get('staff_id', type=int)
    assigned_ventilator_id = request.form.get('ventilator_id', type=int)
    assigned_oxygen_id = request.form.get('oxygen_id', type=int)
    blood_group = request.form.get('blood_group')
    blood_component = request.form.get('blood_component')
    blood_units = request.form.get('blood_units', type=int, default=0)

    if bed_id:
        b = get_bed(bed_id)
        if b:
            bed = b['bed_code']
            update_bed_status(bed_id, 'Occupied', pid, notes=f'Updated bed assignment for {name}')

    update_patient(pid, name, age, gender, condition, severity, dept_id, bed, notes, status,
                   assigned_staff_id, assigned_ventilator_id, assigned_oxygen_id,
                   blood_group, blood_component, blood_units)

    if assigned_ventilator_id:
        update_life_support(assigned_ventilator_id, 'In Use', pid, dept_id, 'SIMV', None, None, f'Assigned to {name}')
    if assigned_oxygen_id:
        update_life_support(assigned_oxygen_id, 'In Use', pid, dept_id, f'{blood_units or 5}L/min', None, None, f'Assigned to {name}')

    if blood_group and blood_component and blood_units and blood_units > 0:
        reserve_blood_units(blood_group, blood_component, blood_units)

    flash('Patient updated.', 'success')
    return redirect(url_for('patients_page'))


@app.route('/patients/delete/<int:pid>', methods=['POST'])
def patients_delete_route(pid):
    delete_patient(pid)
    flash('Patient record deleted.', 'success')
    return redirect(url_for('patients_page'))


# ─────────────────────────────────────
#  AI Predictions
# ─────────────────────────────────────
@app.route('/predictions')
def predictions_page():
    state    = _current_state()
    pred     = get_predictions(ML_BUNDLE, state)
    forecast = get_24h_forecast(ML_BUNDLE, state)

    beds_avail = state['beds_available']
    sod        = state['staff_count']
    alerts_list, _ = generate_alert(pred, beds_avail, sod)

    from database import get_icu_transfer_candidates
    icu_transfers = get_icu_transfer_candidates()

    return render_template('predictions.html',
        page='predictions', pa=_pa(),
        ba=beds_avail, sa=sod, current_hour=state['hour'],
        pred=pred, alerts=alerts_list, meta=pred['model_meta'],
        forecast_labels=[f['label'] for f in forecast],
        forecast_patients=[f['patients'] for f in forecast],
        forecast_beds=[f['beds_needed'] for f in forecast],
        forecast_staff=[f['staff_needed'] for f in forecast],
        icu_transfers=icu_transfers,
    )


# ─────────────────────────────────────
#  Alerts
# ─────────────────────────────────────
@app.route('/alerts')
def alerts_page():
    live_alerts = generate_real_alerts()
    total = len(live_alerts)
    pending = sum(1 for a in live_alerts if not a.get('acknowledged'))
    critical = sum(1 for a in live_alerts if a['severity'] == 'CRITICAL' and not a.get('acknowledged'))
    ac = {'total': total, 'pending': pending, 'critical': critical}
    return render_template('alerts.html',
        page='alerts', pa=pending,
        alerts=live_alerts, ac=ac,
    )


# ─────────────────────────────────────
#  Analytics
# ─────────────────────────────────────
@app.route('/analytics')
def analytics_page():
    state    = _current_state()
    forecast = get_24h_forecast(ML_BUNDLE, state)
    monthly  = get_monthly_trend(ML_BUNDLE, state)

    resources   = get_resources()
    staff_summ  = get_staff_summary()
    depts       = get_departments()
    bed_summ    = get_bed_summary()

    # Dept utilization using bed table
    dept_util = []
    all_beds = get_beds()
    for d in depts:
        d_beds = [b for b in all_beds if b['department_id'] == d['id']]
        total    = len(d_beds) or d['total_beds']
        occupied = sum(1 for b in d_beds if b['status'] == 'Occupied')
        pct      = round((occupied / max(total, 1)) * 100)
        dept_util.append({'name': d['name'], 'icon': d['icon'],
                          'total': total, 'occupied': occupied, 'pct': pct})

    # Resource health
    resource_health = []
    for r in resources:
        if r['total'] == 0:
            continue
        util = round((r['in_use'] / r['total']) * 100)
        resource_health.append({
            'name': r['name'], 'available': r['available'],
            'total': r['total'], 'util': util, 'status': r['status']
        })

    # KPIs
    avg_daily   = int(sum(m['patients'] for m in monthly) / max(len(monthly), 1))
    beds_available_now = sum(b['available'] for b in bed_summ)
    beds_total_now     = sum(b['total'] for b in bed_summ)
    avg_bed_util = round((1 - beds_available_now / max(beds_total_now, 1)) * 100, 1)
    peak         = max(forecast, key=lambda x: x['patients'], default={'hour': 10})
    staff_total  = len(get_staff())
    sod          = get_staff_on_duty()
    staff_eff    = round((sod / max(staff_total, 1)) * 100, 1)

    return render_template('analytics.html',
        page='analytics', pa=_pa(),
        avg_daily_admissions=avg_daily,
        avg_bed_util=avg_bed_util,
        peak_hour=peak['hour'],
        staff_efficiency=staff_eff,
        dept_util=dept_util,
        resource_health=resource_health,
        staff_summary=staff_summ,
        bed_summary=bed_summ,
        monthly_labels=[m['month'] for m in monthly],
        monthly_patients=[m['patients'] for m in monthly],
        hourly_labels=[f['label'] for f in forecast],
        hourly_beds=[f['beds_needed'] for f in forecast],
        hourly_staff=[f['staff_needed'] for f in forecast],
    )


# ─────────────────────────────────────
#  Settings
# ─────────────────────────────────────
@app.route('/settings', methods=['GET', 'POST'])
def settings_page():
    if request.method == 'POST':
        h = request.form.get('hour', type=int)
        p = request.form.get('patients', type=int)
        b = request.form.get('beds', type=int)
        s = request.form.get('staff', type=int)

        theme = request.form.get('theme', 'dark')
        set_setting('theme', theme)

        if all(v is not None for v in [h, p, b, s]):
            insert_hospital_data(h, p, b, s)
            flash('Snapshot saved!', 'success')

        flash(f'Theme set to {theme}.', 'success')
        return redirect(url_for('settings_page'))

    return render_template('settings.html',
        page='settings', pa=_pa(),
        depts=get_departments(),
    )


@app.route('/settings/staff/add', methods=['POST'])
def staff_add():
    add_staff(
        request.form['name'], request.form['role'],
        int(request.form['department_id']), request.form['shift'],
        request.form['status'], request.form.get('phone',''),
        request.form.get('email','')
    )
    flash('Staff member added.', 'success')
    return redirect(url_for('settings_page'))


@app.route('/settings/staff/<int:sid>/update', methods=['POST'])
def staff_update(sid):
    update_staff(sid,
        request.form['name'], request.form['role'],
        int(request.form['department_id']), request.form['shift'],
        request.form['status'], request.form.get('phone',''),
        request.form.get('email','')
    )
    flash('Staff member updated.', 'success')
    return redirect(url_for('settings_page'))


@app.route('/settings/staff/<int:sid>/delete', methods=['POST'])
def staff_delete(sid):
    delete_staff(sid)
    flash('Staff member removed.', 'success')
    return redirect(url_for('settings_page'))


@app.route('/resources/bed/<int:bed_id>/toggle_maintenance', methods=['POST'])
def bed_toggle_maintenance(bed_id):
    bed = get_bed(bed_id)
    if not bed:
        flash('Bed not found.', 'error')
        return redirect(url_for('resources_page'))
    if bed['status'] == 'Maintenance':
        update_bed_status(bed_id, 'Available')
        flash(f"{bed['bed_code']} restored to Available.", 'success')
    elif bed['status'] == 'Available':
        update_bed_status(bed_id, 'Maintenance')
        flash(f"{bed['bed_code']} set to Maintenance.", 'warning')
    else:
        flash(f"Cannot toggle: bed is currently {bed['status']}.", 'error')
    return redirect(url_for('resources_page'))


# ─────────────────────────────────────
#  REST API
# ─────────────────────────────────────
@app.route('/api/predict', methods=['POST'])
def api_predict():
    data  = request.get_json() or {}
    state = _current_state()
    state['hour']           = data.get('hour', state['hour'])
    state['beds_available'] = data.get('beds_available', state['beds_available'])
    state['staff_count']    = data.get('staff_count', state['staff_count'])
    state['er_arrivals']    = data.get('er_arrivals', state['er_arrivals'])
    return jsonify(get_predictions(ML_BUNDLE, state))


@app.route('/api/dashboard-data')
def api_dashboard():
    state = _current_state()
    pred  = get_predictions(ML_BUNDLE, state)
    return jsonify({
        'patient_counts': get_patient_counts(),
        'beds_available': state['beds_available'],
        'staff_on_duty':  state['staff_count'],
        'prediction':     pred,
    })


@app.route('/api/forecast')
def api_forecast():
    return jsonify(get_24h_forecast(ML_BUNDLE, _current_state()))


@app.route('/api/blood')
def api_blood():
    return jsonify(get_blood_inventory(
        blood_group=request.args.get('group'),
        component=request.args.get('component')
    ))


@app.route('/api/mobile-equipment')
def api_mobile():
    return jsonify(get_mobile_equipment(
        equipment_type=request.args.get('type'),
        status=request.args.get('status')
    ))


if __name__ == '__main__':
    print("=" * 55)
    print("  MedByte — AI Hospital Resource Optimization")
    print("  http://localhost:5000")
    print("=" * 55)
    app.run(debug=True, host='0.0.0.0', port=5000)