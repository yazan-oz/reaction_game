from flask import Flask, render_template, jsonify, request
import json
import os
print("FILES IN ROOT:", os.listdir("."))
import time
import random
import threading
import atexit
from datetime import datetime

# Import hardware controller with detailed diagnostics
HARDWARE_ENABLED = False
hardware = None

def log_app(message):
    """Simple logging for app events"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] APP: {message}")

# Only try to import hardware on Raspberry Pi (not on Render/cloud)
if os.path.exists('/dev/gpiochip0'):  # This only exists on Pi
    try:
        log_app("GPIO detected - attempting to import hardware_controller...")
        from hardware_controller import hardware
        
        if hardware and hardware.is_available():
            HARDWARE_ENABLED = True
            log_app("Hardware controller loaded and available!")
        else:
            HARDWARE_ENABLED = False
            log_app("Hardware controller loaded but not available")
    except Exception as e:
        HARDWARE_ENABLED = False
        log_app(f"Hardware controller failed: {e}")
else:
    log_app("No GPIO detected - running in cloud/web-only mode")

if not HARDWARE_ENABLED:
    log_app("Running in software mode - web interface only")

app = Flask(__name__, static_folder='static')

# Game state
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

# ====DATABASE SETUP: Try PostgreSQL, fallback to JSON file====

USE_DATABASE = False
db_connection = None
LEADERBOARD_FILE = 'leaderboard_data.json' # JSON file fallback

def init_database():
    """Initialize PostgreSQL connection if DATABASE_URL is available"""
    global USE_DATABASE, db_connection
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        try:
            # Handle the 'postgres://' vs 'postgresql://' fix for SQLAlchemy/Psycopg2 compatibility
            if database_url.startswith("postgres://"):
                database_url = database_url.replace("postgres://", "postgresql://", 1)
            
            import psycopg2
            from psycopg2.extras import RealDictCursor

            log_app("Attempting to connect to PostgreSQL database...") 
            
            # FIXED: Added sslmode='require' and shorter connect_timeout for Render
            db_connection = psycopg2.connect(
                database_url,
                connect_timeout=5,  
                sslmode='require'   
            )

            with db_connection.cursor() as cursor:
                # Create leaderboard table if it does not exist
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
                
                # Update columns logic
                cursor.execute("""
                    DO $$ 
                    BEGIN
                        BEGIN
                            ALTER TABLE leaderboard ADD COLUMN difficulty VARCHAR(20) DEFAULT 'unknown';
                        EXCEPTION
                            WHEN duplicate_column THEN NULL;
                        END;
                        BEGIN
                            ALTER TABLE leaderboard ADD COLUMN max_combo INTEGER DEFAULT 0;
                        EXCEPTION
                            WHEN duplicate_column THEN NULL;
                        END;
                    END $$;
                """)

                cursor.execute("CREATE INDEX IF NOT EXISTS idx_game_mode ON leaderboard(game_mode)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_score ON leaderboard(score DESC)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_avg_time ON leaderboard(avg_time)")
                
                db_connection.commit()
            
            USE_DATABASE = True
            log_app("✅ PostgreSQL database connected successfully!")

        except Exception as e:
            log_app(f"⚠️ Database connection failed: {e}")
            log_app("Falling back to JSON file storage.")
            USE_DATABASE = False
            db_connection = None
    else:
         log_app("ℹ️ DATABASE_URL not found. Using JSON storage.")
         USE_DATABASE = False

# RE-ENABLED: This will now run on startup safely
try:
    init_database()
except Exception as e:
    log_app(f"⚠️ Database initialization logic failed: {e}")
    USE_DATABASE = False

def load_leaderboard():
    """Load leaderboard from database or JSON file"""
    if USE_DATABASE and db_connection:
        try:
            with db_connection.cursor() as cursor:
                cursor.execute("""
                    SELECT name, score, game_mode, difficulty, max_combo, avg_time, accuracy, date, timestamp
                    FROM leaderboard
                    ORDER BY timestamp DESC
                """)
                rows = cursor.fetchall()
                return [
                    {
                        'name': row[0],
                        'score': row[1],
                        'gameMode': row[2],
                        'difficulty': row[3],
                        'maxCombo': row[4],
                        'avgTime': row[5],
                        'accuracy': row[6],
                        'date': row[7].isoformat() if hasattr(row[7], 'isoformat') else str(row[7]),
                        'timestamp': row[8]
                    }
                    for row in rows
                ]
        except Exception as e:
            log_app(f"Error loading from database: {e}")
            return load_leaderboard_json()
    else:
        return load_leaderboard_json()

def save_score_to_database(entry):
    """Save a single score entry to database"""
    if USE_DATABASE and db_connection:
        try:
            with db_connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO leaderboard 
                    (name, score, game_mode, difficulty, max_combo, avg_time, accuracy, date, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    entry['name'],
                    entry['score'],
                    entry['gameMode'],
                    entry.get('difficulty', 'unknown'),
                    entry.get('maxCombo', 0),
                    entry['avgTime'],
                    entry['accuracy'],
                    datetime.fromisoformat(entry['date']),
                    entry['timestamp']
                ))
                db_connection.commit()
            return True
        except Exception as e:
            log_app(f"Error saving score to database: {e}")
            return False
    return False

def load_leaderboard_json():
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_leaderboard_json(data):
    try:
        with open(LEADERBOARD_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        log_app(f"Error saving to JSON: {e}")

# Hardware/Logic Handlers
def hardware_button_pressed(button_id):
    if game_state["waiting_for_press"] and not game_state["tension_building"]:
        handle_button_press(button_id)

def handle_button_press(button_id):
    if not game_state["waiting_for_press"]:
        return {"error": "Not waiting for button press"}
    
    reaction_time = int((time.time() - game_state["start_time"]) * 1000)
    
    if button_id == game_state["current_button"]:
        game_state["last_message"] = f"✅ Correct! Reaction time: {reaction_time} ms"
        if game_state["best_time"] is None or reaction_time < game_state["best_time"]:
            game_state["best_time"] = reaction_time
        
        if HARDWARE_ENABLED and hardware:
            hardware.performance_meter_update(reaction_time)
        
        game_state["round"] += 1
        game_state["waiting_for_press"] = False
        game_state["tension_building"] = False
    else:
        game_state["last_message"] = f"❌ Wrong button! Expected {game_state['current_button']}"
        game_state["waiting_for_press"] = False
        if HARDWARE_ENABLED and hardware:
            hardware.snap_back()
    
    return game_state

# Setup hardware callbacks
if HARDWARE_ENABLED and hardware:
    try:
        hardware.set_button_callback(1, lambda: hardware_button_pressed(1))
        hardware.set_button_callback(2, lambda: hardware_button_pressed(2))
        atexit.register(hardware.cleanup)
    except Exception as e:
        log_app(f"Error setting up hardware callbacks: {e}")

# ===== ROUTES =====

@app.route("/")
def index():
    return render_template("template.html", hardware_enabled=HARDWARE_ENABLED)

@app.route("/mobile")
def mobile_index():
    return render_template("mobile.html", hardware_enabled=HARDWARE_ENABLED)

@app.route("/api/buttons", methods=["GET"])
def get_buttons():
    return jsonify(buttons)

@app.route("/api/buttons/<int:button_id>/press", methods=["POST"])
def press_button(button_id):
    if HARDWARE_ENABLED and hardware:
        hardware_button_pressed(button_id)
    else:
        handle_button_press(button_id)
    return jsonify(game_state)

@app.route("/api/start_round", methods=["POST"])
def start_round():
    global game_state
    data = request.get_json() if request.is_json else {}
    target_button = data.get('target_button')
    
    if target_button is None:
        target_button = random.choice([1, 2])
    
    game_state["current_button"] = target_button
    game_state["waiting_for_press"] = True
    game_state["start_time"] = time.time()
    game_state["tension_building"] = False
    return jsonify(game_state)

@app.route("/api/status", methods=["GET"])
def get_status():
    status = game_state.copy()
    status["hardware_enabled"] = HARDWARE_ENABLED
    status["hardware_available"] = hardware.is_available() if (HARDWARE_ENABLED and hardware) else False
    return jsonify(status)

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    game_mode = request.args.get('mode', 'time_attack')
    limit = int(request.args.get('limit', 10))
    all_scores = load_leaderboard()
    mode_scores = [s for s in all_scores if s.get('gameMode') == game_mode]
    
    if game_mode == 'time_attack':
        mode_scores.sort(key=lambda x: x.get('score', 0), reverse=True)
    else:
        mode_scores.sort(key=lambda x: x.get('avgTime', float('inf')))
    
    return jsonify({
        'success': True,
        'scores': mode_scores[:limit],
        'total': len(mode_scores),
        'storage_type': 'database' if USE_DATABASE else 'json'
    })

@app.route('/api/leaderboard', methods=['POST'])
def save_score():
    data = request.json
    required_fields = ['name', 'gameMode', 'score', 'avgTime', 'accuracy']
    if not all(field in data for field in required_fields):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    player_name = data['name'].strip()[:50]
    new_entry = {
        'name': player_name,
        'score': int(data['score']),
        'gameMode': data['gameMode'],
        'difficulty': data.get('difficulty', 'unknown'),
        'maxCombo': int(data.get('maxCombo', 0)),
        'avgTime': float(data['avgTime']) if data['avgTime'] != '-' else 0,
        'accuracy': float(data['accuracy']),
        'date': datetime.utcnow().isoformat(),
        'timestamp': datetime.utcnow().timestamp()
    }
    
    if USE_DATABASE:
        success = save_score_to_database(new_entry)
        if not success:
            all_scores = load_leaderboard_json()
            all_scores.append(new_entry)
            save_leaderboard_json(all_scores)
    else:
        all_scores = load_leaderboard_json()
        all_scores.append(new_entry)
        save_leaderboard_json(all_scores)
    
    return jsonify({'success': True, 'entry': new_entry, 'storage_type': 'database' if USE_DATABASE else 'json'})

@app.route("/api/hardware_diagnostics", methods=["GET"])
def hardware_diagnostics():
    return jsonify({
        "hardware_enabled": HARDWARE_ENABLED,
        "database_enabled": USE_DATABASE,
        "database_type": "PostgreSQL" if USE_DATABASE else "JSON file",
        "system_info": {"platform": os.name, "python": datetime.now().isoformat()}
    })

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)