import pandas as pd

def test_preprocessing_basic():
    data = {
        "hour": 12,
        "day_of_week": 2,
        "action_code": 1,
        "actions_per_session": 5,
        "session_duration_sec": 120,
        "time_diff_sec": 30,
        "is_private_ip": 0,
        "action": "click",
        "ip_address": "192.168.1.1",
        "user_agent": "Mozilla",
        "device_type": "desktop",
        "browser_family": "Firefox",
        "os_family": "Linux",
        "bot_type": "unknown"
    }

    df = pd.DataFrame([data])

    # Vérifications basiques
    assert df.isnull().sum().sum() == 0
    assert df.shape == (1, 14)
