from flask import Flask, jsonify
from kafka import KafkaProducer
import json, time, os, uuid, random
from datetime import datetime, timedelta

app = Flask(__name__)

producer = KafkaProducer(
    bootstrap_servers=os.environ.get("KAFKA_BROKER", "broker:9092"),
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# ==================== SYSTÈME DE SESSIONS CORRIGÉ ====================
# Nouvelle structure: {ip_address: {"session_id": "...", "last_time": ts, "action_count": n}}
active_sessions = {}
SESSION_TIMEOUT_SEC = 1800  # 30 minutes en secondes
SESSION_MAX_ACTIONS = 15    # Maximum d'actions par session avant nouvelle session

def get_or_create_session_id(ip_address):
    """
    Gère les sessions de manière réaliste :
    1. Réutilise la session si pas expirée ET pas trop d'actions
    2. Sinon, crée une nouvelle session
    """
    current_time = time.time()
    
    # Vérifier si cette IP a déjà une session active
    if ip_address in active_sessions:
        session_data = active_sessions[ip_address]
        
        # Vérifier DEUX conditions pour réutiliser :
        # 1. Session pas expirée (moins de 30 min)
        # 2. Pas trop d'actions dans cette session
        session_not_expired = (current_time - session_data["last_time"]) < SESSION_TIMEOUT_SEC
        not_too_many_actions = session_data["action_count"] < SESSION_MAX_ACTIONS
        
        if session_not_expired and not_too_many_actions:
            # ✅ Session valide : on l'utilise à nouveau
            session_data["last_time"] = current_time
            session_data["action_count"] += 1
            active_sessions[ip_address] = session_data
            
            # Log occasionnel
            if random.random() < 0.05:  # 5% du temps
                print(f"🔄 Session réutilisée: {session_data['session_id'][:15]}... "
                      f"(action #{session_data['action_count']})")
            
            return session_data["session_id"]
        else:
            # ❌ Session expirée ou trop d'actions : nouvelle session
            reason = "expirée" if not session_not_expired else f"trop d'actions ({session_data['action_count']})"
            if random.random() < 0.1:
                print(f"🆕 Nouvelle session (ancienne {reason}) pour {ip_address}")
    
    # Créer une NOUVELLE session
    new_session_id = f"sess_{uuid.uuid4().hex[:12]}"
    active_sessions[ip_address] = {
        "session_id": new_session_id,
        "last_time": current_time,
        "action_count": 1,  # Première action
        "created_at": current_time,
        "ip_address": ip_address
    }
    
    # Log occasionnel
    if random.random() < 0.05:
        print(f"🆕 Nouvelle session créée: {new_session_id}")
    
    return new_session_id

# ==================== EXTRACTION USER-AGENT ====================
def extract_device_info(user_agent_string):
    """
    Extrait device_type, browser_family, os_family du user_agent
    SANS dépendance externe - logique simple pour le streaming
    """
    ua = user_agent_string.lower()
    
    # 1. Détection device_type (pour feature ML)
    if 'mobile' in ua or 'iphone' in ua or 'android' in ua:
        device_type = 'mobile'
    elif 'tablet' in ua or 'ipad' in ua:
        device_type = 'tablet'
    else:
        device_type = 'desktop'  # Par défaut
    
    # 2. Détection browser_family (pour feature ML)
    if 'chrome' in ua and 'chromium' not in ua:
        browser_family = 'chrome'
    elif 'firefox' in ua:
        browser_family = 'firefox'
    elif 'safari' in ua and 'chrome' not in ua:
        browser_family = 'safari'
    elif 'edge' in ua:
        browser_family = 'edge'
    elif 'opera' in ua:
        browser_family = 'opera'
    elif 'bot' in ua or 'crawler' in ua or 'spider' in ua or 'googlebot' in ua or 'bingbot' in ua:
        browser_family = 'bot_client'
    else:
        browser_family = 'other'
    
    # 3. Détection os_family (pour feature ML)
    if 'windows' in ua:
        os_family = 'windows'
    elif 'mac os' in ua or 'macintosh' in ua:
        os_family = 'macos'
    elif 'linux' in ua and 'android' not in ua:
        os_family = 'linux'
    elif 'android' in ua:
        os_family = 'android'
    elif 'iphone' in ua or 'ipad' in ua:
        os_family = 'ios'
    else:
        os_family = 'other'
    
    return {
        'device_type': device_type,
        'browser_family': browser_family,
        'os_family': os_family
    }

# ==================== DONNÉES DE SIMULATION ====================
bot_list = [
    "scraper_bot", "selenium_bot", "curl_bot", "python_requests_bot",
    "googlebot", "bingbot", "yandex_bot", "facebook_externalhit", "twitterbot"
]

human_user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 11; SM-A505F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.163 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
]

bot_user_agents = [
    "python-requests/2.31.0",
    "curl/7.88.1",
    "Selenium/Chrome/120.0.6099.109",
    "Go-http-client/2.0",
    "Googlebot/2.1 (+http://www.google.com/bot.html)",
    "Mozilla/5.0 (compatible; Bingbot/2.0; +http://www.bing.com/bingbot.htm)",
    "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Googlebot/2.1; +http://www.google.com/bot.html) Chrome/120.0.6099.108 Safari/537.36",
    "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)"
]

bot_ip_ranges = [
    ("10.0.0.0", "10.255.255.255"),
    ("172.16.0.0", "172.31.255.255"),
    ("192.168.0.0", "192.168.255.255"),
    ("66.249.64.0", "66.249.95.255"),
    ("157.55.39.0", "157.55.39.255")
]

human_ip_ranges = [
    ("192.168.0.0", "192.168.255.255"),
    ("10.0.0.0", "10.0.255.255"),
    ("172.16.0.0", "172.16.255.255")
]

def generate_ip_from_range(ip_range):
    start, end = ip_range
    start_parts = list(map(int, start.split('.')))
    end_parts = list(map(int, end.split('.')))
    ip_parts = [str(random.randint(s, e)) if s != e else str(s) for s, e in zip(start_parts, end_parts)]
    return ".".join(ip_parts)

def weighted_random_action(is_bot):
    if is_bot:
        return random.choices(
            ["page_view", "click", "scroll", "search", "login"],
            weights=[40, 25, 20, 10, 5],
            k=1
        )[0]
    else:
        actions = {"page_view": 40, "click": 25, "scroll": 20, "search": 10, "login": 5}
        population = list(actions.keys())
        weights = list(actions.values())
        return random.choices(population, weights=weights, k=1)[0]

# ==================== ENDPOINT PRINCIPAL AMÉLIORÉ ====================
@app.route("/bot_event", methods=["GET"])
def bot_event():
    # 1. Décision bot/humain
    is_bot = random.choices([0, 1], weights=[0.7, 0.3], k=1)[0]
    
    # 2. Génération des données de base
    if is_bot:
        bot_type = random.choice(bot_list)
        user_agent = random.choice(bot_user_agents)
        ip_address = generate_ip_from_range(random.choice(bot_ip_ranges))
    else:
        bot_type = "none"
        user_agent = random.choice(human_user_agents)
        ip_address = generate_ip_from_range(random.choice(human_ip_ranges))
    
    # 3. CORRECTION: Session avec logique améliorée
    # Pour les bots, plus de chance de garder la même session
    # Pour les humains, plus de variations
    if is_bot and random.random() < 0.8:  # 80% des bots gardent leur session
        # Utiliser l'IP normale
        session_id = get_or_create_session_id(ip_address)
    else:
        # Humains ou 20% des bots: parfois forcer nouvelle session
        if random.random() < 0.4:  # 40% de nouvelle session
            # Ajouter un suffixe à l'IP pour forcer nouvelle session
            unique_ip = f"{ip_address}_{uuid.uuid4().hex[:6]}"
            session_id = get_or_create_session_id(unique_ip)
        else:
            session_id = get_or_create_session_id(ip_address)
    
    # 4. Action aléatoire
    action = weighted_random_action(is_bot)
    
    # 5. Timestamp ISO 8601 avec décalage réaliste
    current_datetime = datetime.now()
    hour = current_datetime.hour
    time_adjustment = random.uniform(-10, 10) if 9 <= hour <= 17 else random.uniform(-30, 30)
    adjusted_datetime = current_datetime + timedelta(seconds=time_adjustment)
    timestamp_iso = adjusted_datetime.isoformat()
    
    # 6. Extraction des features pour ML
    device_info = extract_device_info(user_agent)
    
    # 7. Construction de l'événement FINAL
    event = {
        "event_id": str(uuid.uuid4()),
        "session_id": session_id,
        "is_bot": is_bot,
        "bot_type": bot_type,
        "action": action,
        "timestamp": timestamp_iso,
        "ip_address": ip_address,  # On garde l'IP originale pour l'analyse
        "user_agent": user_agent,
        "device_type": device_info['device_type'],
        "browser_family": device_info['browser_family'],
        "os_family": device_info['os_family']
    }

    # 8. 5% d'humains avec patterns suspects
    if is_bot == 0 and random.random() < 0.05:
        event["user_agent"] = random.choice(bot_user_agents)
        event["ip_address"] = generate_ip_from_range(random.choice(bot_ip_ranges[3:]))
        new_device_info = extract_device_info(event["user_agent"])
        event["device_type"] = new_device_info['device_type']
        event["browser_family"] = new_device_info['browser_family']
        event["os_family"] = new_device_info['os_family']

    # 9. Envoi à Kafka
    producer.send("bot_events", event)
    producer.flush()
    
    # Log minimal
    if random.random() < 0.1:
        print(f"📤 Envoyé: session={session_id[:10]}..., bot={is_bot}, action={action}")
    
    return jsonify(event)

# ==================== NOUVEL ENDPOINT POUR GÉNÉRER DES SESSIONS MULTI-ACTIONS ====================
@app.route("/generate_session", methods=["GET"])
def generate_session():
    """
    Génère plusieurs actions pour une même session (plus réaliste)
    """
    # Décision bot/humain
    is_bot = random.choices([0, 1], weights=[0.7, 0.3], k=1)[0]
    
    # Données de base
    if is_bot:
        bot_type = random.choice(bot_list)
        user_agent = random.choice(bot_user_agents)
        ip_address = generate_ip_from_range(random.choice(bot_ip_ranges))
        # Bots: 3-8 actions par session
        num_actions = random.randint(3, 8)
    else:
        bot_type = "none"
        user_agent = random.choice(human_user_agents)
        ip_address = generate_ip_from_range(random.choice(human_ip_ranges))
        # Humains: 1-4 actions par session
        num_actions = random.randint(1, 4)
    
    # Créer une session
    session_id = get_or_create_session_id(ip_address)
    events = []
    
    # Générer plusieurs actions avec délais réalistes
    for i in range(num_actions):
        # Action
        action = weighted_random_action(is_bot)
        
        # Timestamp avec progression
        base_time = datetime.now()
        # Délai entre actions: 0-2s pour première, puis 1-10s
        delay = random.uniform(0, 2) if i == 0 else random.uniform(1, min(10, i*2))
        action_time = base_time + timedelta(seconds=delay)
        timestamp_iso = action_time.isoformat()
        
        # Device info (même pour toute la session)
        device_info = extract_device_info(user_agent)
        
        # Construction événement
        event = {
            "event_id": str(uuid.uuid4()),
            "session_id": session_id,
            "is_bot": is_bot,
            "bot_type": bot_type,
            "action": action,
            "timestamp": timestamp_iso,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "device_type": device_info['device_type'],
            "browser_family": device_info['browser_family'],
            "os_family": device_info['os_family']
        }
        
        # Envoyer à Kafka
        producer.send("bot_events", event)
        events.append(event)
        
        # Petit délai simulé
        time.sleep(random.uniform(0.01, 0.05))
    
    producer.flush()
    
    print(f"✅ Session générée: {session_id} ({num_actions} actions, {'🤖' if is_bot else '👤'})")
    
    return jsonify({
        "status": "success",
        "session_id": session_id,
        "is_bot": is_bot,
        "num_actions": num_actions,
        "ip_address": ip_address
    })

# ==================== ENDPOINT POUR VÉRIFIER LES SESSIONS ====================
@app.route("/sessions_info", methods=["GET"])
def sessions_info():
    """
    Affiche l'état actuel des sessions (pour debug)
    """
    current_time = time.time()
    total_sessions = len(active_sessions)
    
    if total_sessions == 0:
        return jsonify({"message": "Aucune session active"})
    
    # Calculer les statistiques
    total_actions = sum(s["action_count"] for s in active_sessions.values())
    avg_actions = total_actions / total_sessions if total_sessions > 0 else 0
    
    # Prendre un échantillon de 10 sessions
    sample = []
    for ip, data in list(active_sessions.items())[:10]:
        age_seconds = current_time - data.get("created_at", current_time)
        sample.append({
            "ip": ip[:20] + "..." if len(ip) > 20 else ip,
            "session_id": data["session_id"][:15] + "...",
            "actions": data["action_count"],
            "age_sec": round(age_seconds, 1),
            "last_active_sec": round(current_time - data["last_time"], 1)
        })
    
    return jsonify({
        "total_active_sessions": total_sessions,
        "total_actions": total_actions,
        "avg_actions_per_session": round(avg_actions, 2),
        "session_sample": sample
    })

if __name__ == "__main__":
    print("="*60)
    print("🚀 Serveur de génération d'événements BOT/HUMAIN")
    print("="*60)
    print("Endpoints disponibles:")
    print("  GET /bot_event      - Génère un événement unique")
    print("  GET /generate_session - Génère une session complète (multi-actions)")
    print("  GET /sessions_info  - Affiche l'état des sessions")
    print("="*60)
    app.run(host="0.0.0.0", port=5000)
