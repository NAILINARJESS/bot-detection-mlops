# ==================================================
# src/api/main.py
# FastAPI pour Bot Detection - Production
# ==================================================

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import joblib
from datetime import datetime

# ==================================================
# Initialisation FastAPI
# ==================================================
app = FastAPI(title="Bot Detection API", version="1.0")

# ==================================================
# CORS (OBLIGATOIRE pour frontend navigateur)
# ==================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # OK pour PFE
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================================================
# Chargement du modèle
# ==================================================
MODEL_PATH = "src/tracking/bot_detection_latest.pkl"

try:
    model = joblib.load(MODEL_PATH)
    print(f"💾 Modèle chargé localement : {MODEL_PATH}")
except Exception as e:
    raise RuntimeError(f"Impossible de charger le modèle : {e}")

# ==================================================
# Colonnes catégoriques
# ==================================================
CAT_FEATURES = [
    "action",
    "ip_address",
    "user_agent",
    "device_type",
    "browser_family",
    "os_family",
    "bot_type"
]

# ==================================================
# Schéma requête
# ==================================================
class PredictRequest(BaseModel):
    features: dict

# ==================================================
# Endpoint racine
# ==================================================
@app.get("/")
def root():
    return {"message": "API Bot Detection opérationnelle"}

# ==================================================
# Endpoint prédiction
# ==================================================
@app.post("/predict")
def predict(request: PredictRequest):
    try:
        # DataFrame
        X = pd.DataFrame([request.features])

        # Sécurisation colonnes catégoriques
        for col in CAT_FEATURES:
            if col in X.columns:
                X[col] = X[col].astype(str).fillna("unknown")

        # Prédiction
        prediction = int(model.predict(X)[0])
        probability = float(model.predict_proba(X)[0][1])

        return {
            "prediction": prediction,
            "probability": probability
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================================================
# Endpoint metrics
# ==================================================
@app.get("/metrics")
def metrics():
    return {
        "model_path": MODEL_PATH,
        "loaded_at": datetime.now().isoformat()
    }

