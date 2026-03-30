import pandas as pd
import os
from sklearn.linear_model import LinearRegression

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.csv")


def train_model():
    data = pd.read_csv(DATA_PATH)
    X = data[['hour', 'beds_available', 'staff_available']]
    y = data['patients']
    model = LinearRegression()
    model.fit(X, y)
    return model


def predict_next(model, hour, beds, staff):
    prediction = model.predict([[hour, beds, staff]])
    return max(0, int(prediction[0]))


def get_prediction_details(model, hour, beds, staff):
    """Return prediction with additional context."""
    pred = predict_next(model, hour, beds, staff)
    # Simple confidence based on how far we are from training range
    confidence = max(50, min(95, 95 - abs(hour - 12) * 2))

    # Risk level
    if pred > beds:
        risk = 'High'
    elif pred > beds * 0.8:
        risk = 'Medium'
    else:
        risk = 'Low'

    return {
        'predicted_patients': pred,
        'confidence': confidence,
        'risk_level': risk,
        'hour': hour,
        'beds': beds,
        'staff': staff,
        'utilization': round((pred / max(beds, 1)) * 100, 1)
    }


def get_hourly_predictions(model, beds, staff):
    """Get predictions for all 24 hours."""
    predictions = []
    for h in range(1, 25):
        p = predict_next(model, h, beds, staff)
        predictions.append({'hour': h, 'predicted': p})
    return predictions