# ==== FILE: src/data_loader.py ====
# DataLoader: load CSV, streaming placeholder, sampling
# from __future__ import annotations
import pandas as pd
from pathlib import Path
from typing import Optional


class DataLoader:
    def __init__(self, path: Optional[str] = None):
        self.path = Path(path) if path else None

    def read_csv(self, path: Optional[str] = None, nrows: Optional[int] = None) -> pd.DataFrame:
        p = Path(path) if path else self.path
        if p is None:
            raise ValueError('No path provided to DataLoader')
        df = pd.read_csv(p, nrows=nrows)
        return df

    def preview(self, df: pd.DataFrame, n: int = 5):
        return df.head(n)
    
if __name__ == "__main__":
    loader = DataLoader(path="data/dataset_clean_2025-12-14_10-46-34.csv")  # adapte le nom du fichier
    df = loader.read_csv()
    print("Aperçu du dataset :")
    print(loader.preview(df))
