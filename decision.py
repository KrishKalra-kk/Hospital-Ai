"""
Decision engine: generate alerts and recommendations from ML predictions.
"""


def generate_alert(pred: dict, beds_avail: int, staff_on_duty: int) -> tuple:
    """
    Generate predictive alerts from ML output dict.
    Returns (alerts_list, recommendations_list)
    """
    alerts = []
    recs   = []

    patients_next  = pred.get('patients_next_hour', 0)
    beds_needed    = pred.get('beds_needed_24h', 0)
    staff_needed   = pred.get('staff_needed_24h', 0)
    risk_beds      = pred.get('risk_beds', 'Low')
    risk_staff     = pred.get('risk_staff', 'Low')
    risk_patients  = pred.get('risk_patients', 'Low')
    bed_util       = pred.get('bed_utilization', 0)

    # ── Bed alerts ──
    if risk_beds in ('Critical',):
        alerts.append({'severity': 'CRITICAL', 'type': 'Resource',
                       'message': f'Bed demand critical — {beds_needed} beds needed, only {beds_avail} available!'})
        recs.append({'priority': 'High',
                     'action': 'Activate overflow protocol. Consider patient transfers or temporary bed installation.'})
    elif risk_beds == 'High':
        alerts.append({'severity': 'WARNING', 'type': 'Resource',
                       'message': f'High bed demand predicted — {beds_needed} beds needed (util: {bed_util}%)'})
        recs.append({'priority': 'Medium',
                     'action': 'Prepare additional beds. Notify overflow departments.'})
    elif risk_beds == 'Medium':
        alerts.append({'severity': 'INFO', 'type': 'Resource',
                       'message': f'Moderate bed demand — {bed_util}% utilization projected.'})
        recs.append({'priority': 'Low', 'action': 'Monitor bed availability. No immediate action needed.'})

    # ── Staff alerts ──
    if risk_staff in ('Critical',):
        alerts.append({'severity': 'CRITICAL', 'type': 'Staff',
                       'message': f'Critical staff shortage — need {staff_needed}, only {staff_on_duty} on duty!'})
        recs.append({'priority': 'High',
                     'action': 'Call in on-call staff immediately. Consider shift extensions.'})
    elif risk_staff == 'High':
        alerts.append({'severity': 'WARNING', 'type': 'Staff',
                       'message': f'Staff strain predicted — {staff_needed} staff needed, {staff_on_duty} available.'})
        recs.append({'priority': 'Medium', 'action': 'Place on-call staff on standby for next shift.'})

    # ── Patient surge ──
    if risk_patients in ('Critical', 'High'):
        alerts.append({'severity': 'WARNING', 'type': 'Patient',
                       'message': f'Patient surge expected — {patients_next} admissions predicted next hour.'})
        recs.append({'priority': 'Medium',
                     'action': 'Activate surge protocols. Ensure pharmacy/lab/radiology readiness.'})

    # ── All clear ──
    if not alerts:
        alerts.append({'severity': 'NORMAL', 'type': 'System',
                       'message': 'All resources sufficient for predicted patient load.'})
        recs.append({'priority': 'Low',
                     'action': 'Continue monitoring. System operating within normal parameters.'})

    return alerts, recs


def generate_recommendations(pred: dict, resources: list, staff_on_duty: int) -> list:
    """Generate actionable recommendations for dashboard."""
    _, recs = generate_alert(pred, 0, staff_on_duty)

    # Add resource-specific recommendations
    critical, warnings = assess_resource_status(resources)
    for msg in critical:
        recs.append({'priority': 'High', 'action': f'Critical resource: {msg}'})
    for msg in warnings[:2]:
        recs.append({'priority': 'Medium', 'action': f'Resource warning: {msg}'})

    return recs[:6]  # limit to top 6


def assess_resource_status(resources: list) -> tuple:
    """Return (critical_list, warning_list) based on current resource state."""
    critical = []
    warnings = []
    for r in resources:
        if r['total'] == 0:
            continue
        util = (r['in_use'] / r['total']) * 100
        avail = r['available']
        if avail == 0 or util > 90:
            critical.append(f"{r['name']}: {avail}/{r['total']} available ({util:.0f}% utilized)")
        elif util > 75:
            warnings.append(f"{r['name']}: {avail}/{r['total']} available ({util:.0f}% utilized)")
    return critical, warnings