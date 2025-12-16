# src/data_analysis.py
from __future__ import annotations
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json

class DataAnalysis:
    def __init__(self, outdir: str = 'reports'):
        self.outdir = Path(outdir)
        self.outdir.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------
    # 1) Analyse qualité des données
    # --------------------------------------------------------
    def data_quality(self, df: pd.DataFrame) -> dict:
        quality = {
            "shape": df.shape,
            "missing_values": df.isna().sum().to_dict(),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "duplicates": int(df.duplicated().sum())
        }
        path = self.outdir / "01_data_quality.json"
        with open(path, "w") as f:
            json.dump(quality, f, indent=4)
        return quality


    # --------------------------------------------------------
    # 2) Analyse descriptive générale
    # --------------------------------------------------------
    def basic_stats(self, df: pd.DataFrame) -> dict:
        stats = {
            "describe_num": df.describe().to_dict(),
            "describe_all": df.describe(include='all').to_dict()
        }
        path = self.outdir / "02_basic_stats.json"
        with open(path, "w") as f:
            json.dump(stats, f, indent=4)
        return stats


    # --------------------------------------------------------
    # 3) Analyse bots vs humains
    # --------------------------------------------------------
    def bot_stats(self, df: pd.DataFrame) -> dict:
        if 'is_bot' not in df.columns:
            return {}

        bot_count = df['is_bot'].value_counts().to_dict()

        stats = {
            "bot_counts": bot_count,
            "bot_ratio": float(df['is_bot'].mean()),
            "avg_time_diff_bots": float(df[df.is_bot == 1]['time_diff_sec'].mean()),
            "avg_time_diff_humans": float(df[df.is_bot == 0]['time_diff_sec'].mean()),
            "avg_session_duration_bots": float(df[df.is_bot == 1]['session_duration_sec'].mean()),
            "avg_session_duration_humans": float(df[df.is_bot == 0]['session_duration_sec'].mean())
        }

        path = self.outdir / "03_bot_stats.json"
        with open(path, "w") as f:
            json.dump(stats, f, indent=4)
        return stats


    # --------------------------------------------------------
    # 4) Heatmap des corrélations
    # --------------------------------------------------------
    def correlation_matrix(self, df: pd.DataFrame):
        num_df = df.select_dtypes(include=[np.number])

        plt.figure(figsize=(10, 8))
        sns.heatmap(num_df.corr(), annot=True, fmt='.2f', cmap='coolwarm')
        plt.title("Correlation Matrix")
        plt.tight_layout()
        plt.savefig(self.outdir / "04_correlation_heatmap.png")
        plt.close()

        num_df.corr().to_csv(self.outdir / "04_correlation_matrix.csv")


    # --------------------------------------------------------
    # 5) Histogrammes + Boxplots
    # --------------------------------------------------------
    def distributions(self, df: pd.DataFrame):
        cols = ['hour', 'day_of_week', 'time_diff_sec',
                'session_duration_sec', 'actions_per_session', 'action_code']

        for col in cols:
            if col not in df.columns:
                continue

            # Histogramme
            plt.figure(figsize=(6, 4))
            sns.histplot(df[col], bins=20)
            plt.title(f"Distribution of {col}")
            plt.tight_layout()
            plt.savefig(self.outdir / f"{col}_hist.png")
            plt.close()

            # Boxplot (détection outliers)
            plt.figure(figsize=(6, 4))
            sns.boxplot(x=df[col])
            plt.title(f"Boxplot of {col}")
            plt.tight_layout()
            plt.savefig(self.outdir / f"{col}_boxplot.png")
            plt.close()


    # --------------------------------------------------------
    # 6) Analyse IP
    # --------------------------------------------------------
    def ip_analysis(self, df: pd.DataFrame):
        if 'is_private_ip' not in df.columns:
            return

        ip_stats = {
            "private_ip_ratio": float(df['is_private_ip'].mean())
        }

        with open(self.outdir / "05_ip_stats.json", "w") as f:
            json.dump(ip_stats, f, indent=4)

        # Graphique
        plt.figure(figsize=(6, 4))
        sns.countplot(x=df['is_private_ip'])
        plt.title("Private vs Public IP")
        plt.tight_layout()
        plt.savefig(self.outdir / "05_ip_distribution.png")
        plt.close()


    # --------------------------------------------------------
    # 7) Analyse User-Agent
    # --------------------------------------------------------
    def user_agent_analysis(self, df: pd.DataFrame):
        if 'user_agent' not in df.columns:
            return

        top_ua = df['user_agent'].value_counts().head(20)
        top_ua.to_csv(self.outdir / "06_user_agent_top20.csv")

        plt.figure(figsize=(10, 6))
        sns.barplot(y=top_ua.index, x=top_ua.values)
        plt.title("Top 20 User Agents")
        plt.tight_layout()
        plt.savefig(self.outdir / "06_user_agents_top20.png")
        plt.close()


    # --------------------------------------------------------
    # PIPELINE COMPLET EDA
    # --------------------------------------------------------
    def generate_full_report(self, df: pd.DataFrame):
        print("➡ Generating full EDA report...")

        reports = {
            "data_quality": self.data_quality(df),
            "basic_stats": self.basic_stats(df),
            "bot_stats": self.bot_stats(df)
        }

        self.correlation_matrix(df)
        self.distributions(df)
        self.ip_analysis(df)
        self.user_agent_analysis(df)

        print("✔ Rapports EDA générés dans /reports/")
        return reports


# --------------------------------------------------------
# MAIN
# --------------------------------------------------------
if __name__ == "__main__":
    df = pd.read_csv("../data/processed/dataset_features_complete.csv")

    analysis = DataAnalysis(outdir="reports")
    reports = analysis.generate_full_report(df)

    print("\nRésumé EDA :")
    print(json.dumps(reports, indent=4))
