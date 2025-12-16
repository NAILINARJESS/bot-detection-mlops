import joblib
import pandas as pd

MODEL_PATH = "src/tracking/bot_detection_latest.pkl"

def test_model_load():
    model = joblib.load(MODEL_PATH)
    assert model is not None

def test_model_prediction():
    model = joblib.load(MODEL_PATH)

    sample = pd.DataFrame([{
        "hour": 10,
        "day_of_week": 1,
        "action_code": 2,
        "actions_per_session": 3,
        "session_duration_sec": 90,
        "time_diff_sec": 20,
        "is_private_ip": 0,
        "action": "view",
        "ip_address": "10.0.0.1",
        "user_agent": "Mozilla",
        "device_type": "mobile",
        "browser_family": "Chrome",
        "os_family": "Android",
        "bot_type": "unknown"
    }])

    pred = model.predict(sample)[0]
    prob = model.predict_proba(sample)[0][1]

    assert pred in [0, 1]
    assert 0.0 <= prob <= 1.0
