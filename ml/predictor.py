"""
Prediction API — clean interface for the Flask routes.
All model calls go through this module.
"""

import numpy as np


def _build_feature_vector(hour, day_of_week, month, is_weekend,
                           beds_available, icu_occupied, icu_available,
                           staff_count, shift, er_arrivals,
                           equipment_in_use, seasonal_factor):
    return [[
        hour, day_of_week, month, int(is_weekend),
        beds_available, icu_occupied, icu_available,
        staff_count, shift, er_arrivals,
        equipment_in_use, seasonal_factor,
    ]]


def _shift_for_hour(hour: int) -> int:
    if 7 <= hour <= 14:
        return 0
    elif 15 <= hour <= 22:
        return 1
    return 2


def _seasonal_factor(month: int) -> float:
    import math
    return round(1.0 + 0.15 * math.cos((month - 1) * 2 * math.pi / 12), 3)


def _risk_level(predicted: float, capacity: float) -> str:
    ratio = predicted / max(capacity, 1)
    if ratio >= 0.95:
        return "Critical"
    elif ratio >= 0.80:
        return "High"
    elif ratio >= 0.60:
        return "Medium"
    return "Low"


def _confidence(r2: float) -> int:
    """Convert R² to a human-readable confidence percentage."""
    return max(50, min(99, int(r2 * 100)))


def get_predictions(bundle: dict, current_state: dict) -> dict:
    """
    Main prediction entry point.
    current_state keys:
      hour, day_of_week, month, beds_available, icu_occupied, icu_available,
      staff_count, er_arrivals, equipment_in_use
    Returns a rich dict with all three forecasts.
    """
    hour = current_state.get("hour", 12)
    day_of_week = current_state.get("day_of_week", 0)
    month = current_state.get("month", 6)
    is_weekend = day_of_week >= 5
    beds_available = current_state.get("beds_available", 30)
    icu_occupied = current_state.get("icu_occupied", 8)
    icu_available = current_state.get("icu_available", 12)
    staff_count = current_state.get("staff_count", 25)
    er_arrivals = current_state.get("er_arrivals", 5)
    equipment_in_use = current_state.get("equipment_in_use", 12)
    shift = _shift_for_hour(hour)
    seasonal = _seasonal_factor(month)
    beds_total = beds_available + current_state.get("beds_occupied", 80)

    X = _build_feature_vector(
        hour, day_of_week, month, is_weekend,
        beds_available, icu_occupied, icu_available,
        staff_count, shift, er_arrivals,
        equipment_in_use, seasonal
    )

    patients_pred = max(0, int(bundle["patients"]["model"].predict(X)[0]))
    beds_pred = max(0, int(bundle["beds"]["model"].predict(X)[0]))
    staff_pred = max(0, int(bundle["staff"]["model"].predict(X)[0]))

    return {
        "patients_next_hour": patients_pred,
        "beds_needed_24h":    beds_pred,
        "staff_needed_24h":   staff_pred,
        "bed_utilization":    round((beds_pred / max(beds_total, 1)) * 100, 1),
        "staff_utilization":  round((staff_pred / max(staff_count, 1)) * 100, 1),
        "risk_beds":   _risk_level(beds_pred, beds_total),
        "risk_staff":  _risk_level(staff_pred, staff_count * 1.2),
        "risk_patients": _risk_level(patients_pred, 20),
        "confidence_patients": _confidence(bundle["patients"].get("r2", 0.85)),
        "confidence_beds":     _confidence(bundle["beds"].get("r2", 0.90)),
        "confidence_staff":    _confidence(bundle["staff"].get("r2", 0.88)),
        "model_meta": {
            "patients_r2":  round(bundle["patients"].get("r2", 0), 3),
            "beds_r2":      round(bundle["beds"].get("r2", 0), 3),
            "staff_r2":     round(bundle["staff"].get("r2", 0), 3),
        }
    }


def get_24h_forecast(bundle: dict, current_state: dict) -> list:
    """
    Returns hourly forecast list for the next 24 hours.
    Each item: {hour, patients, beds_needed, staff_needed}
    """
    from datetime import datetime
    base_hour = current_state.get("hour", datetime.now().hour)
    day_of_week = current_state.get("day_of_week", 0)
    month = current_state.get("month", datetime.now().month)
    is_weekend = day_of_week >= 5
    beds_available = current_state.get("beds_available", 30)
    icu_occupied = current_state.get("icu_occupied", 8)
    icu_available = current_state.get("icu_available", 12)
    staff_count = current_state.get("staff_count", 25)
    er_arrivals = current_state.get("er_arrivals", 5)
    equipment_in_use = current_state.get("equipment_in_use", 12)
    seasonal = _seasonal_factor(month)

    forecast = []
    for i in range(24):
        h = (base_hour + i) % 24
        shift = _shift_for_hour(h)
        X = _build_feature_vector(
            h, day_of_week, month, is_weekend,
            beds_available, icu_occupied, icu_available,
            staff_count, shift, er_arrivals,
            equipment_in_use, seasonal
        )
        forecast.append({
            "hour": h,
            "label": f"{h:02d}:00",
            "patients": max(0, int(bundle["patients"]["model"].predict(X)[0])),
            "beds_needed": max(0, int(bundle["beds"]["model"].predict(X)[0])),
            "staff_needed": max(0, int(bundle["staff"]["model"].predict(X)[0])),
        })
    return forecast


def get_weekly_trend(bundle: dict, current_state: dict) -> list:
    """Returns 7-day daily aggregate forecast."""
    from datetime import datetime
    month = current_state.get("month", datetime.now().month)
    seasonal = _seasonal_factor(month)
    beds_available = current_state.get("beds_available", 30)
    icu_occupied = current_state.get("icu_occupied", 8)
    icu_available = current_state.get("icu_available", 12)
    staff_count = current_state.get("staff_count", 25)
    equipment_in_use = current_state.get("equipment_in_use", 12)
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    result = []
    for dow in range(7):
        is_weekend = dow >= 5
        daily_patients = 0
        for h in [8, 12, 16, 20]:
            X = _build_feature_vector(
                h, dow, month, is_weekend,
                beds_available, icu_occupied, icu_available,
                staff_count, _shift_for_hour(h), 5,
                equipment_in_use, seasonal
            )
            daily_patients += max(0, int(bundle["patients"]["model"].predict(X)[0]))
        result.append({"day": days[dow], "patients": daily_patients})
    return result
