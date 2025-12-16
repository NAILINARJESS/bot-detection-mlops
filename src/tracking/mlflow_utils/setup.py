# src/tracking/mlflow_utils/setup.py
import os
import mlflow
import dagshub
from dotenv import load_dotenv

def setup_mlflow_dagshub():
    """Configure MLflow pour utiliser DagsHub comme serveur distant"""
    
    # 1. Charger les variables d'environnement
    load_dotenv()
    
    # 2. Vérifier les credentials
    dagshub_username = os.getenv('DAGSHUB_USERNAME')
    dagshub_token = os.getenv('DAGSHUB_TOKEN')
    mlflow_tracking_uri = os.getenv('MLFLOW_TRACKING_URI')
    
    if not all([dagshub_username, dagshub_token, mlflow_tracking_uri]):
        raise ValueError("❌ Variables DagsHub manquantes. Vérifiez votre fichier .env")
    
    # 3. Initialiser DagsHub (méthode recommandée)
    dagshub.init(
        repo_owner=dagshub_username,
        repo_name='bot-detection-mlops',
        mlflow=True
    )
    
    # OU méthode manuelle :
    # mlflow.set_tracking_uri(mlflow_tracking_uri)
    # os.environ['MLFLOW_TRACKING_USERNAME'] = dagshub_username
    # os.environ['MLFLOW_TRACKING_PASSWORD'] = dagshub_token
    
    # 4. Configurer l'expérience
    experiment_name = os.getenv('MLFLOW_EXPERIMENT_NAME', 'Bot_Detection')
    mlflow.set_experiment(experiment_name)
    
    print(f"✅ MLflow configuré pour DagsHub")
    print(f"   Tracking URI: {mlflow.get_tracking_uri()}")
    print(f"   Expérience: {experiment_name}")
    
    return mlflow_tracking_uri

if __name__ == "__main__":
    setup_mlflow_dagshub()
