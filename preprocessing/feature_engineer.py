# src/feature_engineer.py
from __future__ import annotations
import pandas as pd
import numpy as np
import ipaddress

class FeatureEngineer:
    """
    Classe pour générer les features à partir des données nettoyées.
    Retourne TOUTES les colonnes originales + les nouvelles features.
    """
    
    def __init__(self):
        self.features_created = False
    
    def _validate_input(self, df: pd.DataFrame) -> bool:
        """Valide que les colonnes nécessaires sont présentes."""
        required_columns = ['session_id', 'timestamp', 'action', 'ip_address', 'is_bot']
        missing = [col for col in required_columns if col not in df.columns]
        
        if missing:
            print(f"❌ Colonnes manquantes: {missing}")
            print("   Exécutez d'abord le data_cleaner.py")
            return False
        return True
    
    def _calculate_session_stats(self, df: pd.DataFrame) -> dict:
        """Calcule et affiche les statistiques des sessions."""
        session_counts = df.groupby('session_id').size()
        
        stats = {
            'total_sessions': len(session_counts),
            'single_action': (session_counts == 1).sum(),
            'multi_action': (session_counts > 1).sum(),
            'max_actions': session_counts.max(),
            'min_actions': session_counts.min(),
            'mean_actions': session_counts.mean()
        }
        
        # Afficher les stats
        print(f"📊 Sessions totales: {stats['total_sessions']}")
        print(f"   - À 1 action: {stats['single_action']} ({stats['single_action']/stats['total_sessions']*100:.1f}%)")
        print(f"   - >1 action: {stats['multi_action']} ({stats['multi_action']/stats['total_sessions']*100:.1f}%)")
        print(f"   - Max actions/session: {stats['max_actions']}")
        print(f"   - Moyenne actions/session: {stats['mean_actions']:.2f}")
        
        return stats
    
    # ----------------------------
    # 1) Features temporelles
    # ----------------------------
    @staticmethod
    def temporal_features(df: pd.DataFrame, ts_col: str = 'timestamp') -> pd.DataFrame:
        """Extrait les features temporelles."""
        df['event_time'] = pd.to_datetime(df[ts_col], errors='coerce')
        df['hour'] = df['event_time'].dt.hour.fillna(-1).astype(int)
        df['day_of_week'] = df['event_time'].dt.dayofweek.fillna(-1).astype(int)
        return df

    # ----------------------------
    # 2) Features de session
    # ----------------------------
    @staticmethod
    def session_features(df: pd.DataFrame, session_col: str = 'session_id', ts_col: str = 'event_time') -> pd.DataFrame:
        """Calcule les features de session."""
        # Trier par session et temps
        df = df.sort_values([session_col, ts_col])
        
        # Stats par session
        sess_stats = df.groupby(session_col).agg(
            actions_per_session=('event_id', 'count'),
            session_start=(ts_col, 'min'),
            session_end=(ts_col, 'max')
        ).reset_index()
        
        # Durée de session
        sess_stats['session_duration_sec'] = (
            sess_stats['session_end'] - sess_stats['session_start']
        ).dt.total_seconds().fillna(0)
        
        # Fusionner avec dataframe principal
        df = df.merge(
            sess_stats[[session_col, 'actions_per_session', 'session_duration_sec']], 
            on=session_col, 
            how='left'
        )
        
        # Temps entre actions
        df['time_diff_sec'] = df.groupby(session_col)[ts_col].diff().dt.total_seconds().fillna(0)
        
        return df

    # ----------------------------
    # 3) Encodage des actions
    # ----------------------------
    @staticmethod
    def encode_actions(df: pd.DataFrame, action_col: str = 'action') -> pd.DataFrame:
        """Encode les actions en codes numériques."""
        df['action_code'] = df[action_col].astype('category').cat.codes
        return df

    # ----------------------------
    # 4) Feature IP privée
    # ----------------------------
    @staticmethod
    def ip_features(df: pd.DataFrame, ip_col: str = 'ip_address') -> pd.DataFrame:
        """Détecte si l'IP est privée."""
        def is_private(ip):
            try:
                return ipaddress.ip_address(str(ip)).is_private
            except:
                return False
        
        df['is_private_ip'] = df[ip_col].apply(is_private).astype(int)
        return df
    
    # ----------------------------
    # PIPELINE COMPLET
    # ----------------------------
    def fit_transform(self, df: pd.DataFrame, output_path: str = None) -> pd.DataFrame:
        """
        Applique tout le feature engineering.
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame nettoyé (sortie du data_cleaner.py)
        output_path : str, optional
            Chemin pour sauvegarder les features
            
        Returns:
        --------
        pd.DataFrame avec TOUTES les colonnes originales + nouvelles features
        """
        print("="*60)
        print("🎯 DÉBUT DU FEATURE ENGINEERING")
        print("="*60)
        
        # 1. Validation
        if not self._validate_input(df):
            return None
        
        # 2. Analyse des données d'entrée
        print("\n📥 DONNÉES D'ENTRÉE :")
        print(f"   - Lignes: {len(df):,}")
        print(f"   - Colonnes: {len(df.columns)}")
        print(f"   - Bots: {df['is_bot'].sum()} ({df['is_bot'].sum()/len(df)*100:.1f}%)")
        
        session_stats = self._calculate_session_stats(df)
        
        # 3. Application des transformations
        print("\n🔧 APPLICATION DES TRANSFORMATIONS...")
        
        # Features temporelles
        df = self.temporal_features(df)
        print("   ✅ Features temporelles")
        
        # Features de session
        df = self.session_features(df)
        print("   ✅ Features de session")
        
        # Encodage actions
        df = self.encode_actions(df)
        print("   ✅ Encodage des actions")
        
        # Features IP
        df = self.ip_features(df)
        print("   ✅ Features IP")
        
        # 4. Créer le DataFrame final avec TOUTES les colonnes
        # Garder toutes les colonnes originales + nouvelles features
        self.features_created = True
        
        # 5. Analyse des features générées
        print("\n📈 FEATURES GÉNÉRÉES :")
        print(f"   - Colonnes totales: {len(df.columns)}")
        print(f"   - Lignes: {len(df):,}")
        
        # Afficher toutes les colonnes
        print("\n📋 LISTE DES COLONNES :")
        original_cols = ['event_id', 'session_id', 'is_bot', 'bot_type', 'action', 
                        'timestamp', 'ip_address', 'user_agent', 'device_type',
                        'browser_family', 'os_family']
        
        new_features = ['hour', 'day_of_week', 'time_diff_sec', 
                       'session_duration_sec', 'actions_per_session',
                       'is_private_ip', 'action_code', 'event_time']
        
        print("   📌 Colonnes originales (11):")
        for i, col in enumerate(original_cols, 1):
            exists = "✓" if col in df.columns else "✗"
            print(f"     {i:2d}. {exists} {col}")
        
        print("\n   🆕 Nouvelles features (8):")
        for i, col in enumerate(new_features, 1):
            exists = "✓" if col in df.columns else "✗"
            print(f"     {i:2d}. {exists} {col}")
        
        print("\n📊 STATISTIQUES DES NOUVELLES FEATURES :")
        print(f"   session_duration_sec : min={df['session_duration_sec'].min():.2f}, "
              f"max={df['session_duration_sec'].max():.2f}, "
              f"mean={df['session_duration_sec'].mean():.2f}")
        
        print(f"   actions_per_session  : min={df['actions_per_session'].min()}, "
              f"max={df['actions_per_session'].max()}, "
              f"mean={df['actions_per_session'].mean():.2f}")
        
        print(f"   time_diff_sec        : min={df['time_diff_sec'].min():.2f}, "
              f"max={df['time_diff_sec'].max():.2f}, "
              f"mean={df['time_diff_sec'].mean():.2f}")
        
        print(f"   is_private_ip        : {df['is_private_ip'].sum()} True "
              f"({df['is_private_ip'].sum()/len(df)*100:.1f}%)")
        
        print(f"   action_code          : {df['action_code'].nunique()} valeurs uniques")
        
        # 6. Vérification du succès
        print("\n✅ VÉRIFICATION FINALE :")
        if session_stats['multi_action'] > 0:
            print(f"   ✓ Sessions multi-actions détectées: {session_stats['multi_action']}")
            print(f"   ✓ Durée max session: {df['session_duration_sec'].max():.2f}s")
            print(f"   ✓ Temps max entre actions: {df['time_diff_sec'].max():.2f}s")
            print("   ✅ PROBLÈME DES SESSIONS RÉSOLU !")
        else:
            print("   ⚠️  ATTENTION: Toutes les sessions n'ont qu'une action")
            print("      Les features de session seront à 0")
        
        # 7. Optionnel: Réorganiser les colonnes pour une meilleure lisibilité
        # Définir l'ordre souhaité des colonnes
        column_order = [
            # Identifiants et métadonnées
            'event_id', 'session_id',
            
            # Informations de base
            'timestamp', 'event_time', 'hour', 'day_of_week',
            
            # Actions
            'action', 'action_code',
            
            # Session features
            'actions_per_session', 'session_duration_sec', 'time_diff_sec',
            
            # Informations réseau
            'ip_address', 'is_private_ip',
            
            # User agent info
            'user_agent', 'device_type', 'browser_family', 'os_family',
            
            # Classification
            'is_bot', 'bot_type'
        ]
        
        # Garder seulement les colonnes qui existent
        existing_columns = [col for col in column_order if col in df.columns]
        # Ajouter les colonnes manquantes à la fin
        remaining_columns = [col for col in df.columns if col not in existing_columns]
        final_column_order = existing_columns + remaining_columns
        
        df = df[final_column_order]
        
        # 8. Sauvegarde
        if output_path:
            df.to_csv(output_path, index=False)
            print(f"\n💾 Données complètes sauvegardées: {output_path}")
            print(f"   - Colonnes: {len(df.columns)}")
            print(f"   - Lignes: {len(df):,}")
        
        print("\n" + "="*60)
        print("🎯 FEATURE ENGINEERING TERMINÉ")
        print("="*60)
        
        return df


# ==================== UTILISATION SIMPLE ====================
if __name__ == "__main__":
    """
    Usage: python src/feature_engineer.py [chemin_vers_dataset_clean.csv]
    
    Exemple:
        python src/feature_engineer.py data/dataset_clean.csv
    """
    import sys
    import os
    
    # Déterminer le fichier d'entrée
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        # Chercher le fichier dataset_clean_step1.csv
        input_file = "../data/processed/dataset_clean_step1.csv"
        if not os.path.exists(input_file):
            # Chercher d'autres fichiers clean
            clean_files = []
            for dir_path in [".", "data", "data_consumer/data"]:
                if os.path.exists(dir_path):
                    files = [f for f in os.listdir(dir_path) if f.startswith("dataset_clean") and f.endswith(".csv")]
                    clean_files.extend([os.path.join(dir_path, f) for f in files])
            
            if not clean_files:
                print("❌ Aucun fichier dataset_clean_*.csv trouvé")
                print("   Exécutez d'abord: python src/data_cleaner.py")
                sys.exit(1)
            
            # Prendre le plus récent
            input_file = max(clean_files, key=os.path.getctime)
    
    print(f"📁 Chargement: {input_file}")
    
    try:
        df_clean = pd.read_csv(input_file)
    except Exception as e:
        print(f"❌ Erreur de chargement: {e}")
        sys.exit(1)
    
    # Initialiser et exécuter
    fe = FeatureEngineer()
    df_features = fe.fit_transform(
        df=df_clean,
        output_path="../data/processed/dataset_features_complete.csv"  # Nom différent pour éviter confusion
    )
    
    if df_features is not None:
        print(f"\n🔍 Aperçu des données (3 premières lignes):")
        print(df_features.head(3).to_string())
        
        print(f"\n📋 Shape final: {df_features.shape}")
        print(f"📊 Distribution des bots: {df_features['is_bot'].sum()}/{len(df_features)} "
              f"({df_features['is_bot'].sum()/len(df_features)*100:.1f}%)")
        
        # Vérification rapide des nouvelles features
        print("\n✅ VÉRIFICATION DES FEATURES :")
        print(f"   - session_duration_sec > 0 : {(df_features['session_duration_sec'] > 0).sum()} lignes")
        print(f"   - actions_per_session > 1  : {(df_features['actions_per_session'] > 1).sum()} lignes")
        print(f"   - time_diff_sec > 0        : {(df_features['time_diff_sec'] > 0).sum()} lignes")
        
        if (df_features['session_duration_sec'] > 0).any():
            print("\n🎉 SUCCÈS : Les données sont complètes et prêtes pour le ML !")
            print("   → Anciennes colonnes: 11")
            print("   → Nouvelles features: 7")
            print("   → Total colonnes: 18")
        else:
            print("\n⚠️  ATTENTION : Toutes les sessions ont durée 0")
            print("   Vérifiez que vous utilisez /generate_session et non /bot_event")
