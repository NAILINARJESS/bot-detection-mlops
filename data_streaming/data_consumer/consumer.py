from kafka import KafkaConsumer
import json
import os
import csv
import time
from datetime import datetime
import signal
import sys

# ------------------ CONFIGURATION ------------------

BROKER = os.environ.get("KAFKA_BROKER", "broker:9092")
TOPIC = "bot_events"
CSV_DIR = "data"
DEBUG = True  # True pour afficher logs, False pour silencieux
GROUP_ID = "bot_detection_consumer_v2"

# ===== NOUVEAU : Tracker de sessions =====
# Dictionnaire pour suivre les sessions: {session_id: {"first_seen": timestamp, "event_count": count}}
session_tracker = {}

# ===== FIELDNAMES MIS À JOUR (11 colonnes) =====
fieldnames = [
    "event_id",        # UUID unique
    "session_id",      # Session réutilisable (format: sess_abc123def456)
    "is_bot",          # Label ML: 1=bot, 0=humain
    "bot_type",        # Type de bot (googlebot, scraper_bot, etc.) ou "none"
    "action",          # page_view, click, scroll, search, login
    "timestamp",       # Format ISO 8601: "2025-12-11T10:30:25.123456"
    "ip_address",      # Adresse IP pour analyse
    "user_agent",      # User agent original (pour debug)
    # ===== NOUVELLES COLONNES POUR ML =====
    "device_type",     # mobile / desktop / tablet
    "browser_family",  # chrome, firefox, safari, bot_client, etc.
    "os_family"        # windows, macos, linux, android, ios, etc.
]

# ------------------ INITIALISATION ------------------

os.makedirs(CSV_DIR, exist_ok=True)

# Fichier CSV unique avec timestamp
CSV_FILE = os.path.join(CSV_DIR, f"bot_events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    if DEBUG:
        print(f"📁 CSV créé: {CSV_FILE}")
        print(f"📋 Colonnes: {len(fieldnames)} ({', '.join(fieldnames)})")

# Kafka consumer
consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=BROKER,
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset="latest",
    enable_auto_commit=True,
    group_id=GROUP_ID
)

# ------------------ STATISTIQUES ------------------

stats = {
    "total_events": 0,
    "bot_events": 0,
    "human_events": 0,
    "events_by_action": {},
    "events_by_bot_type": {},  # Renommé de events_by_bot à events_by_bot_type
    "unique_sessions": 0,
    "events_per_session": {},
    "device_types": {},        # NOUVEAU: stats par device_type
    "browsers": {},           # NOUVEAU: stats par browser_family
    "os_families": {},        # NOUVEAU: stats par os_family
    "last_print": time.time()
}

# Set pour gérer les doublons par event_id
seen_event_ids = set()

def print_stats():
    """Affiche les statistiques détaillées"""
    print("\n" + "="*60)
    print("📊 STATISTIQUES DE CONSOMMATION")
    print("="*60)
    total = stats['total_events']
    print(f"📈 Événements totaux: {total}")
    print(f"🤖 Bots: {stats['bot_events']} ({stats['bot_events']/max(total,1)*100:.1f}%)")
    print(f"👤 Humains: {stats['human_events']} ({stats['human_events']/max(total,1)*100:.1f}%)")
    
    if stats['unique_sessions'] > 0:
        avg_events = total / stats['unique_sessions']
        print(f"🎪 Sessions uniques: {stats['unique_sessions']}")
        print(f"📊 Moyenne événements/session: {avg_events:.1f}")
    
    # Stats par device_type (NOUVEAU)
    if stats['device_types']:
        print(f"\n📱 Devices: {', '.join([f'{k}:{v}' for k, v in stats['device_types'].items()])}")
    
    if stats['events_by_action']:
        print("\n🎯 Actions top 5:")
        for action, count in sorted(stats['events_by_action'].items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {action}: {count}")
    
    if stats['events_by_bot_type']:
        print("\n🤖 Top bot types:")
        for bot_type, count in sorted(stats['events_by_bot_type'].items(), key=lambda x: x[1], reverse=True)[:5]:
            if bot_type != "none":
                print(f"  {bot_type}: {count}")
    
    print("="*60 + "\n")

# ------------------ HANDLER CTRL+C ------------------

def signal_handler(sig, frame):
    """Gère l'arrêt propre avec Ctrl+C"""
    print("\n🛑 Arrêt du consumer...")
    print_stats()
    consumer.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# ------------------ BOUCLE PRINCIPALE ------------------

print(f"🚀 Consumer démarré. En attente d'événements Kafka sur le topic '{TOPIC}'...")

try:
    for message in consumer:
        event = message.value
        event_id = event.get("event_id")

        # 1. Vérifier doublon
        if event_id in seen_event_ids:
            continue
        seen_event_ids.add(event_id)

        # 2. Tracking des sessions (NOUVEAU)
        session_id = event.get("session_id", "unknown")
        
        if session_id not in session_tracker:
            # Nouvelle session détectée
            session_tracker[session_id] = {
                "first_seen": event.get("timestamp"),
                "event_count": 1
            }
            stats["unique_sessions"] += 1
        else:
            # Session existante, incrémenter le compteur
            session_tracker[session_id]["event_count"] += 1
        
        stats["events_per_session"][session_id] = session_tracker[session_id]["event_count"]

        # 3. Enregistrement CSV avec TOUTES les colonnes
        with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            # S'assurer que toutes les clés existent
            row_data = {k: event.get(k, "") for k in fieldnames}
            writer.writerow(row_data)

        # 4. Mise à jour complète des statistiques
        stats["total_events"] += 1
        
        # Type d'utilisateur
        if event.get("is_bot") == 1:
            stats["bot_events"] += 1
            bot_type = event.get("bot_type", "unknown")
            stats["events_by_bot_type"][bot_type] = stats["events_by_bot_type"].get(bot_type, 0) + 1
        else:
            stats["human_events"] += 1
            # Pour les humains, bot_type = "none"
            bot_type = event.get("bot_type", "none")
            stats["events_by_bot_type"][bot_type] = stats["events_by_bot_type"].get(bot_type, 0) + 1

        # Action
        action = event.get("action", "unknown")
        stats["events_by_action"][action] = stats["events_by_action"].get(action, 0) + 1
        
        # NOUVEAU: Statistiques des nouvelles colonnes
        device_type = event.get("device_type", "unknown")
        stats["device_types"][device_type] = stats["device_types"].get(device_type, 0) + 1
        
        browser_family = event.get("browser_family", "unknown")
        stats["browsers"][browser_family] = stats["browsers"].get(browser_family, 0) + 1
        
        os_family = event.get("os_family", "unknown")
        stats["os_families"][os_family] = stats["os_families"].get(os_family, 0) + 1

        # 5. Affichage minimal
        if DEBUG and stats["total_events"] % 10 == 0:
            current_time = datetime.now().strftime('%H:%M:%S')
            print(f"[{current_time}] Traité: {stats['total_events']} événements | "
                  f"Sessions: {stats['unique_sessions']} | "
                  f"Bots: {stats['bot_events']}")

        # 6. Affichage stats détaillées toutes les 30s
        if time.time() - stats["last_print"] > 30:
            print_stats()
            stats["last_print"] = time.time()

except KeyboardInterrupt:
    print("\n⚠️  Interruption utilisateur (Ctrl+C)")
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
finally:
    print("\n" + "="*60)
    print("🏁 FIN DU CONSUMER - STATISTIQUES FINALES")
    print("="*60)
    print_stats()
    consumer.close()
    print(f"💾 Données sauvegardées dans: {CSV_FILE}")
