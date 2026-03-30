"""
MedByte — Hospital Resource Acknowledgement & Management System
Pure Python Flask application — all HTML/CSS/JS embedded in Python files.
Run: python app.py
"""

from flask import Flask, render_template_string, request, redirect, url_for, flash, jsonify, get_flashed_messages
import pandas as pd
import os

from database import create_db, seed_data, get_hospital_data, insert_hospital_data
from database import get_resources, update_resource, get_resource_summary
from database import get_patients, add_patient, discharge_patient, get_patient_counts
from database import get_alerts, add_alert, acknowledge_alert, get_alert_counts
from database import get_departments, get_staff, get_staff_on_duty, get_staff_summary
from model import train_model, predict_next, get_prediction_details, get_hourly_predictions
from decision import generate_alert, assess_resource_status
from styles import CSS
from templates_py import JS, BASE, DASHBOARD, DASHBOARD_JS, RESOURCES, PATIENTS
from templates_py import PREDICTIONS, PREDICTIONS_JS, ALERTS, SETTINGS

app = Flask(__name__)
app.secret_key = 'medcore-ai-secret-key-2026'

# Initialize database and seed sample data
create_db()
seed_data()

# Train the ML model
DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.csv")
ml_model = train_model()


def render_page(title, header, page, content_template, extra_js="", **kwargs):
    """Render a full page by combining base layout with page content."""
    pa = get_alert_counts().get('pending', 0) or 0
    flash_msgs = get_flashed_messages(with_categories=True)
    content = render_template_string(content_template, **kwargs)
    if extra_js:
        extra_js = render_template_string(extra_js, **kwargs)
    return render_template_string(
        BASE, css=CSS, js=JS, title=title, header=header, page=page,
        pa=pa, flash_msgs=flash_msgs, content=content, extra_js=extra_js
    )


# ─── Dashboard ───
@app.route('/')
def dashboard():
    data = pd.read_csv(DATA_PATH)
    pc = get_patient_counts()
    resources = get_resources()
    res_summary = get_resource_summary()

    beds_total = sum(r['total'] for r in resources if r['category'] == 'Beds')
    beds_avail = sum(r['available'] for r in resources if r['category'] == 'Beds')
    bed_util = round((1 - beds_avail / max(beds_total, 1)) * 100, 1)

    sod = get_staff_on_duty()
    ts = len(get_staff())

    next_hour = int(data['hour'].max()) + 1
    beds_last = int(data['beds_available'].iloc[-1])
    staff_last = int(data['staff_available'].iloc[-1])
    pred = predict_next(ml_model, next_hour, beds_last, staff_last)

    alerts_list, recs = generate_alert(pred, beds_avail, sod)
    recent_alerts = get_alerts()[:5]

    trend_labels = data['hour'].tolist()
    trend_data = data['patients'].tolist()

    res_labels = [s['category'] for s in res_summary]
    res_data = [s['in_use'] for s in res_summary]

    return render_page('Dashboard', 'Dashboard', 'dashboard', DASHBOARD, DASHBOARD_JS,
                       pc=pc, ba=beds_avail, bu=bed_util, sod=sod, ts=ts,
                       pred=pred, alerts=recent_alerts, recs=recs,
                       tl=trend_labels, td=trend_data, rl=res_labels, rd=res_data)


# ─── Resources ───
@app.route('/resources')
def resources_page():
    resources = get_resources()
    rs = get_resource_summary()
    return render_page('Resources', 'Resource Management', 'resources', RESOURCES,
                       resources=resources, rs=rs)


@app.route('/resources/update', methods=['POST'])
def resources_update():
    rid = request.form.get('resource_id', type=int)
    avail = request.form.get('available', type=int, default=0)
    in_use = request.form.get('in_use', type=int, default=0)
    maint = request.form.get('maintenance', type=int, default=0)
    if rid:
        update_resource(rid, avail, in_use, maint)
        flash('Resource updated successfully!', 'success')
    return redirect(url_for('resources_page'))


# ─── Patients ───
@app.route('/patients')
def patients_page():
    patients = get_patients()
    cn = get_patient_counts()
    depts = get_departments()
    return render_page('Patients', 'Patient Management', 'patients', PATIENTS,
                       patients=patients, cn=cn, depts=depts)


@app.route('/patients/add', methods=['POST'])
def patients_add():
    name = request.form.get('name', '')
    age = request.form.get('age', type=int)
    gender = request.form.get('gender', 'M')
    condition = request.form.get('condition', '')
    severity = request.form.get('severity', 'Stable')
    dept_id = request.form.get('department_id', type=int)
    bed = request.form.get('bed_number', '')
    notes = request.form.get('notes', '')
    if name:
        add_patient(name, age, gender, condition, severity, dept_id, bed, notes)
        flash(f'Patient {name} admitted successfully!', 'success')
    return redirect(url_for('patients_page'))


@app.route('/patients/discharge/<int:pid>', methods=['POST'])
def patients_discharge(pid):
    discharge_patient(pid)
    flash('Patient discharged successfully!', 'success')
    return redirect(url_for('patients_page'))


# ─── Predictions ───
@app.route('/predictions')
def predictions_page():
    data = pd.read_csv(DATA_PATH)
    beds_last = int(data['beds_available'].iloc[-1])
    staff_last = int(data['staff_available'].iloc[-1])

    hourly_preds = get_hourly_predictions(ml_model, beds_last, staff_last)

    trend_labels = data['hour'].tolist()
    trend_data = data['patients'].tolist()
    pred_data = [p['predicted'] for p in hourly_preds][:len(trend_labels)]

    next_hour = int(data['hour'].max()) + 1
    pred = predict_next(ml_model, next_hour, beds_last, staff_last)
    alerts_list, _ = generate_alert(pred, beds_last, staff_last)

    return render_page('Predictions', 'AI Predictions', 'predictions', PREDICTIONS, PREDICTIONS_JS,
                       ba=beds_last, sa=staff_last, alerts=alerts_list,
                       tl=trend_labels, td=trend_data, pd=pred_data)


# ─── Alerts ───
@app.route('/alerts')
def alerts_page():
    alerts_list = get_alerts()
    ac = get_alert_counts()
    return render_page('Alerts', 'Alert Center', 'alerts', ALERTS,
                       alerts=alerts_list, ac=ac)


@app.route('/alerts/acknowledge/<int:aid>', methods=['POST'])
def alert_ack(aid):
    acknowledge_alert(aid)
    flash('Alert acknowledged!', 'success')
    return ('', 200) if request.headers.get('X-Requested-With') else redirect(url_for('alerts_page'))


# ─── Settings ───
@app.route('/settings', methods=['GET', 'POST'])
def settings_page():
    if request.method == 'POST':
        hour = request.form.get('hour', type=int)
        patients = request.form.get('patients', type=int)
        beds = request.form.get('beds', type=int)
        staff = request.form.get('staff', type=int)
        if all(v is not None for v in [hour, patients, beds, staff]):
            insert_hospital_data(hour, patients, beds, staff)
            flash('Data added successfully!', 'success')
        return redirect(url_for('settings_page'))

    depts = get_departments()
    staff_list = get_staff()
    return render_page('Settings', 'Settings & Data', 'settings', SETTINGS,
                       depts=depts, staff=staff_list)


# ─── API Endpoints ───
@app.route('/api/predict', methods=['POST'])
def api_predict():
    data = request.get_json()
    hour = data.get('hour', 12)
    beds = data.get('beds', 20)
    staff = data.get('staff', 5)
    result = get_prediction_details(ml_model, hour, beds, staff)
    return jsonify(result)


@app.route('/api/dashboard-data')
def api_dashboard():
    pc = get_patient_counts()
    resources = get_resources()
    beds_avail = sum(r['available'] for r in resources if r['category'] == 'Beds')
    sod = get_staff_on_duty()

    csv_data = pd.read_csv(DATA_PATH)
    next_hour = int(csv_data['hour'].max()) + 1
    pred = predict_next(ml_model, next_hour,
                        int(csv_data['beds_available'].iloc[-1]),
                        int(csv_data['staff_available'].iloc[-1]))

    return jsonify({
        'patient_counts': pc,
        'beds_available': beds_avail,
        'staff_on_duty': sod,
        'prediction': pred
    })


if __name__ == '__main__':
    print("=" * 50)
    print("  MedByte - Hospital Resource Management")
    print("  http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)