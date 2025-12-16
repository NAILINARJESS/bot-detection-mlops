import pandas as pd
import os
from datetime import datetime

# ---------------- CONFIGURATION ----------------

DATA_DIR = "./data_consumer/data"
DEBUG = True

# ===== NOS 11 COLONNES OPTIMISÉES =====
COLUMNS = [
    "event_id",        # UUID unique
    "session_id",      # sess_abc123def456 (réutilisable)
    "is_bot",          # Label ML: 1=bot, 0=humain
    "bot_type",        # Type de bot ou "none"
    "action",          # page_view, click, scroll, search, login
    "timestamp",       # ISO 8601 format
    "ip_address",      # Pour analyse
    "user_agent",      # Original (pour debug)
    "device_type",     # mobile/desktop/tablet
    "browser_family",  # chrome/firefox/safari/bot_client/other
    "os_family"        # windows/macos/linux/android/ios/other
]

# ===== VÉRIFICATION DU PROBLÈME DES SESSIONS =====
def check_session_problem(df):
    """
    Vérifie si le problème des sessions à 1 action est résolu
    """
    print("\n" + "="*60)
    print("🔍 VÉRIFICATION DU PROBLÈME DES SESSIONS")
    print("="*60)
    
    if "session_id" not in df.columns:
        print("❌ Colonne 'session_id' manquante")
        return False
    
    # Calculer le nombre d'actions par session
    session_stats = df.groupby('session_id').agg(
        action_count=('event_id', 'count'),
        is_bot=('is_bot', 'first'),
        unique_ips=('ip_address', 'nunique')
    ).reset_index()
    
    total_sessions = len(session_stats)
    single_action_sessions = (session_stats['action_count'] == 1).sum()
    multi_action_sessions = (session_stats['action_count'] > 1).sum()
    
    print(f"📊 Analyse des sessions:")
    print(f"  - Sessions totales: {total_sessions}")
    print(f"  - Sessions à 1 action: {single_action_sessions} ({single_action_sessions/total_sessions*100:.1f}%)")
    print(f"  - Sessions >1 action: {multi_action_sessions} ({multi_action_sessions/total_sessions*100:.1f}%)")
    
    # Distribution du nombre d'actions
    print(f"\n📈 Distribution des actions par session:")
    action_distribution = session_stats['action_count'].value_counts().sort_index()
    for count, freq in action_distribution.items():
        print(f"  - {count} action(s): {freq} sessions ({freq/total_sessions*100:.1f}%)")
    
    # Vérification pour les bots vs humains
    if "is_bot" in session_stats.columns:
        print(f"\n🤖 Analyse Bots vs Humains:")
        
        bots = session_stats[session_stats['is_bot'] == 1]
        humans = session_stats[session_stats['is_bot'] == 0]
        
        if len(bots) > 0:
            avg_bot_actions = bots['action_count'].mean()
            bot_multi = (bots['action_count'] > 1).sum()
            print(f"  - Bots: {len(bots)} sessions")
            print(f"    → Moyenne actions: {avg_bot_actions:.2f}")
            print(f"    → Sessions multi-actions: {bot_multi} ({bot_multi/len(bots)*100:.1f}%)")
        
        if len(humans) > 0:
            avg_human_actions = humans['action_count'].mean()
            human_multi = (humans['action_count'] > 1).sum()
            print(f"  - Humains: {len(humans)} sessions")
            print(f"    → Moyenne actions: {avg_human_actions:.2f}")
            print(f"    → Sessions multi-actions: {human_multi} ({human_multi/len(humans)*100:.1f}%)")
    
    # Vérifier les problèmes de cohérence IP/session
    ip_problems = session_stats[session_stats['unique_ips'] > 1]
    if len(ip_problems) > 0:
        print(f"\n⚠️  Problèmes détectés:")
        print(f"  - Sessions avec plusieurs IPs: {len(ip_problems)}")
        for _, row in ip_problems.head(3).iterrows():
            print(f"    Session {row['session_id'][:15]}... : {row['unique_ips']} IPs différentes")
    
    # ÉVALUATION FINALE
    print("\n" + "="*60)
    print("✅ ÉVALUATION DU PROBLÈME")
    print("="*60)
    
    if multi_action_sessions == 0:
        print("❌ PROBLÈME NON RÉSOLU")
        print("   → Toutes les sessions n'ont qu'une seule action")
        print("   → Vérifiez que vous utilisez /generate_session et non /bot_event")
        return False
    elif multi_action_sessions / total_sessions < 0.3:
        print("⚠️  PROBLÈME PARTIELLEMENT RÉSOLU")
        print(f"   → Seulement {multi_action_sessions/total_sessions*100:.1f}% des sessions ont >1 action")
        print("   → Générer plus de sessions avec /generate_session")
        return True
    else:
        print("✅ PROBLÈME RÉSOLU !")
        print(f"   → {multi_action_sessions/total_sessions*100:.1f}% des sessions ont >1 action")
        print("   → Les données sont réalistes pour le ML")
        
        # Exemples de sessions multi-actions
        multi_sessions = session_stats[session_stats['action_count'] > 1]
        if len(multi_sessions) > 0:
            print(f"\n🎯 Exemples de sessions multi-actions:")
            for _, row in multi_sessions.head(3).iterrows():
                session_events = df[df['session_id'] == row['session_id']].sort_values('timestamp')
                actions = session_events['action'].tolist()
                print(f"  Session {row['session_id'][:15]}... : {row['action_count']} actions")
                print(f"    Actions: {', '.join(actions)}")
        
        return True

# ---------------- CHARGEMENT DES CSV ----------------

print("🔍 Recherche des fichiers CSV...")
csv_files = [os.path.join(DATA_DIR, f) for f in os.listdir(DATA_DIR) if f.endswith(".csv")]

if not csv_files:
    print("❌ Aucun fichier CSV trouvé dans", DATA_DIR)
    exit()

print(f"📂 Fichiers trouvés: {len(csv_files)}")
for f in csv_files:
    print(f"  - {os.path.basename(f)}")

# ---------------- CONCATÉNATION SIMPLE ----------------

df_list = []
for file in csv_files:
    try:
        df = pd.read_csv(file)
        print(f"✅ Lecture: {os.path.basename(file)} ({len(df)} lignes)")
        
        # Vérification rapide des colonnes
        missing_cols = [col for col in COLUMNS if col not in df.columns]
        if missing_cols:
            print(f"   ⚠️ Colonnes manquantes: {missing_cols}")
        
        # Garder seulement nos colonnes standard (si présentes)
        available_cols = [col for col in COLUMNS if col in df.columns]
        df = df[available_cols]
        
        df_list.append(df)
        
    except Exception as e:
        print(f"❌ Erreur avec {file}: {e}")

if not df_list:
    print("❌ Aucune donnée à concaténer")
    exit()

# Concaténation
print("\n🔗 Concaténation des données...")
data = pd.concat(df_list, ignore_index=True)

print(f"📊 Total après concaténation: {len(data)} lignes")

# ---------------- NETTOYAGE MINIMAL ----------------

print("\n🧹 Nettoyage minimal...")

# Suppression des doublons event_id
initial_count = len(data)
data = data.drop_duplicates(subset="event_id", keep='first')
removed = initial_count - len(data)
if removed > 0:
    print(f"   Doublons supprimés: {removed}")

# Conversion timestamp
if "timestamp" in data.columns:
    data["timestamp"] = pd.to_datetime(data["timestamp"], errors='coerce')
    invalid_timestamps = data["timestamp"].isna().sum()
    if invalid_timestamps > 0:
        print(f"   ⚠️ Timestamps invalides: {invalid_timestamps}")

# ---------------- VÉRIFICATION DU PROBLÈME ----------------

problem_solved = check_session_problem(data)

# ---------------- SAUVEGARDE ----------------

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
final_filename = f"dataset_clean_{timestamp}.csv"
final_path = f"../data/raw/{final_filename}"

print(f"\n💾 Sauvegarde du dataset...")
data.to_csv(final_path, index=False)

# ---------------- RECOMMANDATIONS ----------------

print("\n" + "="*60)
print("🎯 RECOMMANDATIONS")
print("="*60)



print(f"📁 Fichier final: {final_filename}")
print(f"📈 Dimensions: {len(data)} lignes, {len(data.columns)} colonnes")

if DEBUG:
    print("\n📋 Aperçu des sessions multi-actions:")
    session_counts = data.groupby('session_id').size()
    multi_sessions = session_counts[session_counts > 1]
    
    if len(multi_sessions) > 0:
        for session_id, count in multi_sessions.head(3).items():
            session_data = data[data['session_id'] == session_id]
            print(f"\n  Session: {session_id[:15]}... ({count} actions)")
            print(f"  Actions: {', '.join(session_data['action'].tolist())}")
            if 'timestamp' in session_data.columns:
                times = session_data['timestamp'].dt.strftime('%H:%M:%S').tolist()
                print(f"  Horaires: {', '.join(times)}")
    else:
        print("  Aucune session multi-action trouvée")

print("\n" + "="*60)
