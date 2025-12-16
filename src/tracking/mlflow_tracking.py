# ==================================================
# src/tracking/mlflow_tracking.py
# MLOps Training + Model Registry + Versioning
# ==================================================

import os
import sys
import hashlib
import joblib
import glob
import pandas as pd
import numpy as np
from datetime import datetime

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    classification_report
)

# Ajouter src au PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

# MLflow
import mlflow
import mlflow.sklearn
from mlflow.models.signature import infer_signature
from mlflow.tracking import MlflowClient

# DagsHub setup
from mlflow_utils.setup import setup_mlflow_dagshub

# ==================================================
# Utils
# ==================================================

def get_latest_csv(folder: str) -> str:
    """Retourne le dernier fichier CSV du dossier"""
    files = glob.glob(os.path.join(folder, "*.csv"))
    if not files:
        raise FileNotFoundError(f"Aucun fichier CSV trouvé dans {folder}")
    latest_file = max(files, key=os.path.getctime)
    return latest_file

def get_data_hash(path: str) -> str:
    """Calculer le hash du dataset pour le versioning"""
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

# ==================================================
# Data Loading
# ==================================================

def load_data(data_path):
    print(f"📊 Chargement des données : {data_path}")
    df = pd.read_csv(data_path)

    target = "is_bot"

    num_features = [
        "hour", "day_of_week", "action_code",
        "actions_per_session", "session_duration_sec",
        "time_diff_sec", "is_private_ip"
    ]

    cat_features = [
        "action", "ip_address", "user_agent",
        "device_type", "browser_family",
        "os_family", "bot_type"
    ]

    X = df[num_features + cat_features]
    y = df[target]

    print(f"✅ Dataset chargé : {X.shape[0]} lignes, {X.shape[1]} features")
    return X, y, num_features, cat_features

# ==================================================
# Preprocessing
# ==================================================

def create_preprocessor(num_features, cat_features):
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), num_features),
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat_features)
        ]
    )

# ==================================================
# Model Selection
# ==================================================

def select_best_model(X_train, y_train, X_test, y_test, preprocessor):
    candidates = {
        "LogisticRegression": LogisticRegression(max_iter=1000),
        "RandomForest": RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1),
        "GradientBoosting": GradientBoostingClassifier(n_estimators=200)
    }

    best_model = None
    best_auc = -1
    best_name = None

    for name, clf in candidates.items():
        pipeline = Pipeline([
            ("preprocessor", preprocessor),
            ("classifier", clf)
        ])

        pipeline.fit(X_train, y_train)
        y_prob = pipeline.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, y_prob)

        print(f"🔍 {name} ROC-AUC : {auc:.4f}")

        if auc > best_auc:
            best_auc = auc
            best_model = pipeline
            best_name = name

    print(f"\n🏆 Meilleur modèle : {best_name} (ROC-AUC={best_auc:.4f})")
    return best_model, best_name, best_auc

# ==================================================
# Model Promotion
# ==================================================

def promote_model(model_name, metric_value, threshold=0.98, stage="Staging"):
    client = MlflowClient()
    versions = client.get_latest_versions(model_name)

    if not versions:
        print("⚠️ Aucun modèle trouvé dans le registry")
        return

    version = versions[0].version

    if metric_value >= threshold:
        client.transition_model_version_stage(
            name=model_name,
            version=version,
            stage=stage,
            archive_existing_versions=True
        )
        print(f"🚀 Modèle v{version} promu en {stage}")
    else:
        print(f"❌ Modèle v{version} non promu (ROC-AUC insuffisant)")

# ==================================================
# Training + MLflow
# ==================================================

def train_model(X_train, y_train, X_test, y_test, num_features, cat_features, data_path):

    # Setup MLflow pour DagsHub
    setup_mlflow_dagshub()

    with mlflow.start_run(run_name="Bot_Detection_Training"):

        # Tags
        mlflow.set_tag("project", "bot-detection-mlops")
        mlflow.set_tag("problem", "binary_classification")
        mlflow.set_tag("team", "data_science")

        # Preprocessing
        preprocessor = create_preprocessor(num_features, cat_features)

        # Model selection
        model, model_name, best_auc = select_best_model(X_train, y_train, X_test, y_test, preprocessor)

        # Predictions
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]

        # Metrics
        metrics = {
            "accuracy": accuracy_score(y_test, y_pred),
            "precision": precision_score(y_test, y_pred, average="weighted"),
            "recall": recall_score(y_test, y_pred, average="weighted"),
            "f1": f1_score(y_test, y_pred, average="weighted"),
            "roc_auc": roc_auc_score(y_test, y_prob)
        }

        # Log params & metrics
        mlflow.log_param("selected_model", model_name)
        mlflow.log_params(model.named_steps["classifier"].get_params())
        for k, v in metrics.items():
            mlflow.log_metric(k, v)

        # Data versioning
        mlflow.log_param("data_hash", get_data_hash(data_path))

        # Model registry
        signature = infer_signature(X_train, model.predict(X_train))
        mlflow.sklearn.log_model(
            model,
            artifact_path="model",
            signature=signature,
            registered_model_name="bot_detection_model"
        )

        # Promotion
        promote_model("bot_detection_model", metrics["roc_auc"], threshold=0.98, stage="Staging")

        # Save classification report
        report = classification_report(y_test, y_pred, output_dict=True)
        pd.DataFrame(report).transpose().to_csv("classification_report.csv")
        mlflow.log_artifact("classification_report.csv")

        print("\n✅ Entraînement terminé")
        return model

# ==================================================
# Chargement du modèle pour prédiction
# ==================================================

def load_latest_model(model_path="bot_detection_latest.pkl"):
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Modèle non trouvé : {model_path}")
    model = joblib.load(model_path)
    print(f"📦 Modèle chargé : {model_path}")
    return model

def predict(model, X):
    return model.predict(X), model.predict_proba(X)[:, 1]

# ==================================================
# Main
# ==================================================

def main():
    np.random.seed(42)

    # 🔹 Charger automatiquement le dernier CSV nettoyé
    input_folder = "../../data/processed"
    data_path = get_latest_csv(input_folder)
    X, y, num_features, cat_features = load_data(data_path)

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Entraînement + MLflow
    model = train_model(X_train, y_train, X_test, y_test, num_features, cat_features, data_path)

    # Sauvegarde locale
    save_path = "bot_detection_latest.pkl"
    joblib.dump(model, save_path)
    print(f"💾 Modèle sauvegardé localement : {save_path}")

    # Chargement automatique pour prédiction
    loaded_model = load_latest_model(save_path)
    y_pred, y_prob = predict(loaded_model, X_test)
    print(f"\n📊 Exemple de prédiction : {y_pred[:5]}")
    print(f"📊 Probabilités : {y_prob[:5]}")

if __name__ == "__main__":
    main()

