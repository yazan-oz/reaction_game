from flask import Flask, render_template, jsonify, request
import json
import os
import time
import random
import atexit
from datetime import datetime

# ==============================
# HARDWARE SETUP
# ==============================

HARDWARE_ENABLED = False
hardware = None

def log_app(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] APP: {message}")

# Only try to import hardware on Raspberry Pi
if os.path.exists('/dev/gpiochip0'):
    try:
        log_app("GPIO detected - attempting to import hardware_controller...")
        from hardware_controller import hardware
        
        if hardware and hardware.is_available():
            HARDWARE_ENABLED = True
            log_app("Hardware controller loaded and available!")
        else:
            log_app("Hardware controller not available")
    except Exception as e:
        log_app(f"Hardware controller failed: {e}")
else:
    log_app("No GPIO detected - running in cloud/web-only mode")

if not HARDWARE_ENABLED:
    log_app("Running in software mode")

app = Flask(__name__, static_folder='static')

# ==============================
# GAME STATE
# ==============================

buttons = [
    {"id": 1, "name": "Button 1", "state": False},
    {"id": 2, "name": "Button 2", "state": False},
]

game_state = {
    "round": 0,
    "waiting_for_press": False,
    "current_button": None,
    "last_message": "Game not started",
    "best_time": None,
    "start_time": None,
    "game_mode": "time_attack",
    "tension_building": False
}

# ==============================
# DATABASE (LAZY CONNECTION)
# ==============================

USE_DATABASE = False
db_connection = None
LEADERBOARD_FILE = "leaderboard_data.json"

def get_db_connection():
    global db_connection, USE_DATABASE

    if db_connection:
        return db_connection

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        USE_DATABASE = False
        return None

    try:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)

        import psycopg2

        log_app("🔌 Attempting lazy PostgreSQL connection...")

        db_connection = psycopg2.connect(
            database_url,
            connect_timeout=5,
            sslmode="require"
        )

        USE_DATABASE = True
        log_app("✅ Database connection successful")
        return db_connection

    except Exception as e:
        log_app(f"⚠️ Database connection failed: {e}")
        USE_DATABASE = False
        db_connection = None
        return None

# ==============================
# LEADERBOARD STORAGE
# ==============================

def load_leaderboard():
    conn = get_db_connection()

    if conn:
        try:
            with conn.cursor() as cursor:

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS leaderboard (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(50) NOT NULL,
                        score INTEGER NOT NULL,
                        game_mode VARCHAR(20) NOT NULL,
                        difficulty VARCHAR(20) DEFAULT 'unknown',
                        max_combo INTEGER DEFAULT 0,
                        avg_time FLOAT NOT NULL,
                        accuracy FLOAT NOT NULL,
                        date TIMESTAMP NOT NULL,
                        timestamp FLOAT NOT NULL
                    );
                """)

                cursor.execute("""
                    SELECT name, score, game_mode, difficulty,
                           max_combo, avg_time, accuracy,
                           date, timestamp
                    FROM leaderboard
                    ORDER BY timestamp DESC
                """)

                rows = cursor.fetchall()

                return [
                    {
                        "name": r[0],
                        "score": r[1],
                        "gameMode": r[2],
                        "difficulty": r[3],
                        "maxCombo": r[4],
                        "avgTime": r[5],
                        "accuracy": r[6],
                        "date": r[7].isoformat(),
                        "timestamp": r[8]
                    }
                    for r in rows
                ]

        except Exception as e:
            log_app(f"Database load failed: {e}")

    return load_leaderboard_json()


def save_score_to_database(entry):
    conn = get_db_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO leaderboard
                (name, score, game_mode, difficulty,
                 max_combo, avg_time, accuracy,
                 date, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                entry["name"],
                entry["score"],
                entry["gameMode"],
                entry.get("difficulty", "unknown"),
                entry.get("maxCombo", 0),
                entry["avgTime"],
                entry["accuracy"],
                datetime.fromisoformat(entry["date"]),
                entry["timestamp"]
            ))
            conn.commit()

        return True

    except Exception as e:
        log_app(f"Database save failed: {e}")
        return False


def load_leaderboard_json():
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []


def save_leaderboard_json(data):
    try:
        with open(LEADERBOARD_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        log_app(f"JSON save failed: {e}")

# ==============================
# GAME LOGIC
# ==============================

def handle_button_press(button_id):
    if not game_state["waiting_for_press"]:
        return {"error": "Not waiting"}

    reaction_time = int((time.time() - game_state["start_time"]) * 1000)

    if button_id == game_state["current_button"]:
        game_state["last_message"] = f"✅ Correct! {reaction_time} ms"
        if game_state["best_time"] is None or reaction_time < game_state["best_time"]:
            game_state["best_time"] = reaction_time

        game_state["round"] += 1
    else:
        game_state["last_message"] = f"❌ Wrong button!"

    game_state["waiting_for_press"] = False
    return game_state

# ==============================
# ROUTES
# ==============================

@app.route("/")
def index():
    return render_template("template.html", hardware_enabled=HARDWARE_ENABLED)

@app.route("/api/start_round", methods=["POST"])
def start_round():
    target_button = random.choice([1, 2])
    game_state["current_button"] = target_button
    game_state["waiting_for_press"] = True
    game_state["start_time"] = time.time()
    return jsonify(game_state)

@app.route("/api/buttons/<int:button_id>/press", methods=["POST"])
def press_button(button_id):
    handle_button_press(button_id)
    return jsonify(game_state)

@app.route("/api/leaderboard", methods=["GET"])
def get_leaderboard_route():
    scores = load_leaderboard()
    return jsonify({
        "success": True,
        "scores": scores,
        "storage_type": "database" if USE_DATABASE else "json"
    })

@app.route("/api/leaderboard", methods=["POST"])
def save_score():
    data = request.json

    new_entry = {
        "name": data["name"][:50],
        "score": int(data["score"]),
        "gameMode": data["gameMode"],
        "difficulty": data.get("difficulty", "unknown"),
        "maxCombo": int(data.get("maxCombo", 0)),
        "avgTime": float(data["avgTime"]),
        "accuracy": float(data["accuracy"]),
        "date": datetime.utcnow().isoformat(),
        "timestamp": datetime.utcnow().timestamp()
    }

    if not save_score_to_database(new_entry):
        all_scores = load_leaderboard_json()
        all_scores.append(new_entry)
        save_leaderboard_json(all_scores)

    return jsonify({
        "success": True,
        "storage_type": "database" if USE_DATABASE else "json"
    })

# ==============================
# MAIN
# ==============================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)