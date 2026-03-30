def generate_alert(predicted_patients, beds, staff):
    alerts = []
    recommendations = []

    # Bed capacity alerts
    if predicted_patients > beds:
        alerts.append({
            'severity': 'CRITICAL',
            'message': f'Predicted patients ({predicted_patients}) exceed bed capacity ({beds})!',
            'type': 'Resource'
        })
        recommendations.append({
            'priority': 'High',
            'action': 'Increase bed capacity immediately — consider temporary beds or patient transfers'
        })
    elif predicted_patients > beds * 0.85:
        alerts.append({
            'severity': 'WARNING',
            'message': f'Bed utilization will reach {int(predicted_patients/beds*100)}% — approaching capacity',
            'type': 'Resource'
        })
        recommendations.append({
            'priority': 'Medium',
            'action': 'Prepare additional beds and notify overflow departments'
        })

    # Staff shortage alerts
    if predicted_patients > staff * 10:
        alerts.append({
            'severity': 'CRITICAL',
            'message': f'Staff shortage! Need {predicted_patients // 10} staff but only {staff} available',
            'type': 'Staff'
        })
        recommendations.append({
            'priority': 'High',
            'action': 'Call in additional staff. Consider shift extensions or on-call personnel.'
        })
    elif predicted_patients > staff * 8:
        alerts.append({
            'severity': 'WARNING',
            'message': f'Staff may be strained — patient-to-staff ratio rising to {predicted_patients/staff:.1f}:1',
            'type': 'Staff'
        })
        recommendations.append({
            'priority': 'Medium',
            'action': 'Place on-call staff on standby'
        })

    # Patient surge alert
    if predicted_patients > 70:
        alerts.append({
            'severity': 'WARNING',
            'message': f'Patient surge expected — {predicted_patients} patients predicted',
            'type': 'Patient'
        })
        recommendations.append({
            'priority': 'Medium',
            'action': 'Activate surge protocols and ensure pharmacy/lab readiness'
        })

    # Normal status
    if predicted_patients < beds and predicted_patients <= staff * 10:
        alerts.append({
            'severity': 'NORMAL',
            'message': 'All resources sufficient for predicted patient load',
            'type': 'System'
        })
        recommendations.append({
            'priority': 'Low',
            'action': 'Continue monitoring. System operating within normal parameters.'
        })

    return alerts, recommendations


def assess_resource_status(resources):
    """Assess overall resource health."""
    critical = []
    warnings = []

    for r in resources:
        if r['total'] == 0:
            continue
        utilization = (r['in_use'] / r['total']) * 100
        if utilization > 90 or r['available'] == 0:
            critical.append(f"{r['name']}: {r['available']}/{r['total']} available ({utilization:.0f}% utilized)")
        elif utilization > 75:
            warnings.append(f"{r['name']}: {r['available']}/{r['total']} available ({utilization:.0f}% utilized)")

    return critical, warnings