"""
Hospital Resource Optimization — ML Models
Trains three Random Forest models on synthetic hospital operations data.
Targets:
  1. patients_next_hour  — admissions forecast
  2. beds_needed_24h     — bed demand forecast
  3. staff_needed_24h    — staffing demand forecast
"""

import os
import sys
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from typing import Optional

# Support both `python ml/model.py` and `from ml.model import ...`
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from ml.dataset import load_or_generate

MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "models")

FEATURE_COLS = [
    "hour", "day_of_week", "month", "is_weekend",
    "beds_available", "icu_occupied", "icu_available",
    "staff_count", "shift", "er_arrivals",
    "equipment_in_use", "seasonal_factor",
]

TARGETS = {
    "patients": "patients_next_hour",
    "beds": "beds_needed_24h",
    "staff": "staff_needed_24h",
}


def _build_model(target_key: str):
    """Choose model architecture per target."""
    if target_key == "patients":
        return GradientBoostingRegressor(
            n_estimators=200, max_depth=5, learning_rate=0.08,
            subsample=0.85, random_state=42
        )
    else:
        return RandomForestRegressor(
            n_estimators=200, max_depth=8, min_samples_leaf=4,
            n_jobs=-1, random_state=42
        )


def train_all_models(verbose: bool = True) -> dict:
    """Train all three models and return a bundle dict."""
    df = load_or_generate()
    os.makedirs(MODEL_DIR, exist_ok=True)

    bundle = {}

    for key, target_col in TARGETS.items():
        X = df[FEATURE_COLS].values
        y = df[target_col].values

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        model = _build_model(key)
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
        r2 = float(r2_score(y_test, y_pred))

        if verbose:
            print(f"[ML] {key:8s} | R²={r2:.3f} | RMSE={rmse:.2f}")

        # Feature importances
        if hasattr(model, "feature_importances_"):
            importances = dict(zip(FEATURE_COLS, model.feature_importances_.round(4).tolist()))
        else:
            importances = {}

        bundle[key] = {
            "model": model,
            "rmse": rmse,
            "r2": r2,
            "importances": importances,
        }

        # Persist
        joblib.dump(model, os.path.join(MODEL_DIR, f"{key}_model.joblib"))

    # Save metadata
    meta = {k: {"r2": v["r2"], "rmse": v["rmse"]} for k, v in bundle.items()}
    import json
    with open(os.path.join(MODEL_DIR, "meta.json"), "w") as f:
        json.dump(meta, f, indent=2)

    return bundle


def load_models() -> Optional[dict]:
    """Load persisted models if they exist."""
    files = {k: os.path.join(MODEL_DIR, f"{k}_model.joblib") for k in TARGETS}
    if not all(os.path.exists(p) for p in files.values()):
        return None
    bundle = {}
    for key, path in files.items():
        bundle[key] = {"model": joblib.load(path)}
    # Load meta
    meta_path = os.path.join(MODEL_DIR, "meta.json")
    if os.path.exists(meta_path):
        import json
        with open(meta_path) as f:
            meta = json.load(f)
        for key in bundle:
            bundle[key]["r2"] = meta.get(key, {}).get("r2", 0.0)
            bundle[key]["rmse"] = meta.get(key, {}).get("rmse", 0.0)
    return bundle


def load_or_train(force_retrain: bool = False) -> dict:
    """Load existing models or train fresh."""
    if not force_retrain:
        bundle = load_models()
        if bundle:
            print("[ML] Loaded pre-trained models from disk.")
            return bundle
    print("[ML] Training models on hospital operations dataset...")
    return train_all_models()


if __name__ == "__main__":
    bundle = train_all_models(verbose=True)
    print("[OK] All models trained and saved.")
    for k, v in bundle.items():
        print(f"  {k}: R2={v['r2']:.3f}, RMSE={v['rmse']:.2f}")
