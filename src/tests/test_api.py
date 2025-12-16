def test_health(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "API Bot Detection" in response.json()["message"]

def test_predict_endpoint(client):
    payload = {
        "features": {
            "hour": 14,
            "day_of_week": 3,
            "action_code": 1,
            "actions_per_session": 6,
            "session_duration_sec": 180,
            "time_diff_sec": 40,
            "is_private_ip": 0,
            "action": "scroll",
            "ip_address": "8.8.8.8",
            "user_agent": "Mozilla",
            "device_type": "desktop",
            "browser_family": "Chrome",
            "os_family": "Windows",
            "bot_type": "unknown"
        }
    }

    response = client.post("/predict", json=payload)

    assert response.status_code == 200

    data = response.json()
    assert "prediction" in data
    assert "probability" in data
    assert data["prediction"] in [0, 1]
    assert 0.0 <= data["probability"] <= 1.0
