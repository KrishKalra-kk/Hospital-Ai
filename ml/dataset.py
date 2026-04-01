"""
Generates a realistic synthetic hospital operations dataset.
Patterns derived from published hospital operational research literature
and UCI Diabetes 130-US Hospitals dataset characteristics.
"""

import numpy as np
import pandas as pd
import os

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "hospital_ops.csv")


def generate_dataset(n_days: int = 90, seed: int = 42) -> pd.DataFrame:
    """
    Generate n_days * 24 hourly records of hospital operations data.
    Returns DataFrame with features and prediction targets.
    """
    rng = np.random.default_rng(seed)
    records = []

    # Hospital baseline config
    BEDS_TOTAL = 110
    ICU_BEDS_TOTAL = 20
    BASE_STAFF_DAY = 35
    BASE_STAFF_NIGHT = 18
    BASE_STAFF_EVENING = 25

    for day in range(n_days):
        day_of_week = day % 7           # 0=Mon, 6=Sun
        month = (day // 30) % 12 + 1   # 1-12
        is_weekend = day_of_week >= 5

        # Seasonal factor: higher in winter months (Dec-Feb)
        seasonal = 1.0 + 0.15 * np.cos((month - 1) * 2 * np.pi / 12)

        # Day-of-week factor
        dow_factor = 1.12 if is_weekend else 1.0

        for hour in range(24):
            # ── Hour of day patient arrival pattern ──
            # Peak: 9-11am emergency arrivals + 5-8pm evening surge
            hour_factor = (
                0.45 + 0.55 * np.exp(-((hour - 10) ** 2) / 8) +
                0.35 * np.exp(-((hour - 18) ** 2) / 6) +
                0.10 * np.exp(-((hour - 3) ** 2) / 4)   # small night cluster
            )

            base_er_arrivals = int(rng.poisson(8 * hour_factor * seasonal * dow_factor))

            # Beds occupied depends on accumulated admissions + length of stay
            beds_occupied = int(np.clip(
                55 + 30 * hour_factor * seasonal * dow_factor + rng.normal(0, 5),
                10, BEDS_TOTAL - 2
            ))
            icu_occupied = int(np.clip(
                8 + 5 * seasonal + rng.normal(0, 1.5),
                1, ICU_BEDS_TOTAL - 1
            ))

            beds_available = BEDS_TOTAL - beds_occupied
            icu_available = ICU_BEDS_TOTAL - icu_occupied

            # Staff on duty depends on shift
            if 7 <= hour <= 14:
                shift = 0  # Day
                staff_count = int(BASE_STAFF_DAY + rng.normal(0, 2))
            elif 15 <= hour <= 22:
                shift = 1  # Evening
                staff_count = int(BASE_STAFF_EVENING + rng.normal(0, 2))
            else:
                shift = 2  # Night
                staff_count = int(BASE_STAFF_NIGHT + rng.normal(0, 1.5))

            staff_count = max(5, staff_count)

            # Equipment in use (ventilators, scanners, monitors)
            equipment_in_use = int(np.clip(
                12 + 10 * hour_factor * seasonal + rng.normal(0, 2),
                3, 28
            ))

            # ── Prediction Targets ──
            # 1) Patients admitted next hour
            patients_next_hour = int(np.clip(
                base_er_arrivals + rng.poisson(2),
                0, 35
            ))

            # 2) Beds needed in next 24h (based on current occupancy + forecast)
            beds_needed_24h = int(np.clip(
                beds_occupied + int(rng.normal(5 * hour_factor * seasonal, 3)),
                10, BEDS_TOTAL
            ))

            # 3) Staff needed next shift
            peak_load = hour_factor * seasonal * dow_factor
            staff_needed_24h = int(np.clip(
                BASE_STAFF_DAY * peak_load + rng.normal(0, 3),
                BASE_STAFF_NIGHT, BASE_STAFF_DAY + 10
            ))

            records.append({
                "hour": hour,
                "day_of_week": day_of_week,
                "month": month,
                "is_weekend": int(is_weekend),
                "beds_total": BEDS_TOTAL,
                "beds_occupied": beds_occupied,
                "beds_available": beds_available,
                "icu_total": ICU_BEDS_TOTAL,
                "icu_occupied": icu_occupied,
                "icu_available": icu_available,
                "staff_count": staff_count,
                "shift": shift,
                "er_arrivals": base_er_arrivals,
                "equipment_in_use": equipment_in_use,
                "seasonal_factor": round(float(seasonal), 3),
                # Targets
                "patients_next_hour": patients_next_hour,
                "beds_needed_24h": beds_needed_24h,
                "staff_needed_24h": staff_needed_24h,
            })

    df = pd.DataFrame(records)
    return df


def save_dataset(df: pd.DataFrame) -> str:
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    df.to_csv(DATA_PATH, index=False)
    print(f"[OK] Dataset saved: {len(df)} rows → {DATA_PATH}")
    return DATA_PATH


def load_or_generate() -> pd.DataFrame:
    if os.path.exists(DATA_PATH):
        return pd.read_csv(DATA_PATH)
    df = generate_dataset(n_days=90)
    save_dataset(df)
    return df


if __name__ == "__main__":
    df = generate_dataset(n_days=90)
    save_dataset(df)
    print(df.describe())
