import mlflow
import os

MODEL_NAME = "bot_detection_model"
MODEL_STAGE = os.getenv("MODEL_STAGE", "Staging")

def load_model():
    """
    Charge le modèle depuis MLflow Model Registry
    """
    model_uri = f"models:/{MODEL_NAME}/{MODEL_STAGE}"
    print(f"📦 Chargement du modèle depuis {model_uri}")
    model = mlflow.pyfunc.load_model(model_uri)
    return model
