# ==== FILE: src/data_cleaner.py ====
from __future__ import annotations
import pandas as pd
import numpy as np
from typing import List
import os
from glob import glob

# ============================
# CLASSE DataCleaner
# ============================

class DataCleaner:
    def __init__(self):
        pass

    @staticmethod
    def to_datetime(df: pd.DataFrame, col: str = 'timestamp') -> pd.DataFrame:
        df[col] = pd.to_datetime(df[col], errors='coerce')
        return df

    @staticmethod
    def normalize_strings(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
        for c in cols:
            if c in df.columns:
                df[c] = df[c].astype('string').str.strip().str.lower()
            else:
                print(f"⚠️ Colonne introuvable (ignorée) : {c}")
        return df

    @staticmethod
    def fill_missing_categorical(df: pd.DataFrame, cols: List[str], value: str = 'unknown') -> pd.DataFrame:
        for c in cols:
            if c in df.columns:
                df[c] = df[c].fillna(value)
            else:
                print(f"⚠️ Colonne introuvable (ignorée) : {c}")
        return df

    @staticmethod
    def drop_duplicate_events(df: pd.DataFrame) -> pd.DataFrame:
        if "event_id" in df.columns:
            return df.drop_duplicates(subset=['event_id'])
        else:
            print("⚠️ 'event_id' manquant, pas de suppression de doublons.")
            return df

    @staticmethod
    def detect_private_ip(ip: str) -> bool:
        try:
            if pd.isna(ip):
                return False
            if ip.startswith(('10.', '192.168.', '172.')):
                return True
        except:
            return False
        return False

# ============================
# UTIL: Récupérer dernier CSV
# ============================

def get_latest_csv(folder: str, pattern: str = "dataset_clean_*.csv") -> str:
    """Retourne le chemin du dernier fichier CSV créé dans le dossier."""
    files = glob(os.path.join(folder, pattern))
    if not files:
        raise FileNotFoundError(f"Aucun fichier correspondant trouvé dans {folder}")
    # Retourner le plus récent selon la date de modification
    latest_file = max(files, key=os.path.getctime)
    return latest_file

# ============================
# SECTION : TEST DIRECT (CLI)
# ============================

if __name__ == "__main__":
    # Lire automatiquement le dernier fichier du streaming
    input_folder = "../data/raw"
    latest_file = get_latest_csv(input_folder)
    
    print(f"📁 Chargement du dernier fichier : {latest_file}")
    df = pd.read_csv(latest_file)
    
    cleaner = DataCleaner()
    print("➡️ Nettoyage en cours...")

    df = cleaner.to_datetime(df, "timestamp")

    df = cleaner.normalize_strings(df, [
        "bot_type",
        "action",
        "device_type",
        "browser_family",
        "os_family"
    ])

    df = cleaner.fill_missing_categorical(df, [
        "bot_type",
        "action",
        "device_type",
        "browser_family",
        "os_family"
    ])

    df = cleaner.drop_duplicate_events(df)

    # Sauvegarde
    output_path = "../data/processed/dataset_clean_step1.csv"
    df.to_csv(output_path, index=False)
    print(f"\n✔️ Dataset nettoyé sauvegardé : {output_path}")

