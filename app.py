from flask import Flask, render_template, jsonify, request
import json
import os
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

try:
    log_app("Attempting to import hardware_controller...")
    from hardware_controller import hardware
    
    if hardware and hardware.is_available():
        HARDWARE_ENABLED = True
        log_app("Hardware controller loaded and available!")
    else:
        HARDWARE_ENABLED = False
        if hardware is None:
            log_app("Hardware controller not available - hardware object is None")
        else:
            log_app("Hardware controller loaded but not available - check GPIO initialization")
        
except ImportError as e:
    HARDWARE_ENABLED = False
    log_app(f"Hardware controller import failed: {e}")
    log_app("Make sure hardware_controller.py exists in the same directory")
except Exception as e:
    HARDWARE_ENABLED = False
    log_app(f"Unexpected error loading hardware controller: {e}")

if not HARDWARE_ENABLED:
    log_app("Running in software mode - web interface only")

app = Flask(__name__)

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
    """"Initialize PostgreSQL connection if DATABASE_URL is available"""
    
    global USE_DATABASE, db_connection
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        try:
            if database_url.startswith("postgres://"):
                database_url = database_url.replace("postgres://", "postgresql://", 1)
            import psycopg2
            from psycopg2.extras import RealDictCursor

            log_app("Attempting to connect to PostgreSQL database...") 
            db_connection = psycopg2.connect(database_url)

            with db_connection.cursor() as cursor: #Create leaderboard table if it does not exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS leaderboard (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(50) NOT NULL,
                        score INTEGER NOT NULL,
                        game_mode VARCHAR(20) NOT NULL,
                        avg_time FLOAT NOT NULL,
                        accuracy FLOAT NOT NULL,
                        date TIMESTAMP NOT NULL,
                        timestamp FLOAT NOT NULL 
                    );
                """)

                cursor.execute( """ CREATE INDEX IF NOT EXISTS idx_game_mode ON leaderboard(game_mode)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_score ON leaderboard(score DESC)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_avg_time ON leaderboard(avg_time)
                """)
                
                db_connection.commit()
            
            USE_DATABASE = True
            log_app("✅ PostgreSQL database connected successfully!")
            log_app("Leaderboard data will persist across server restarts.")

        except ImportError:
             log_app("⚠️ psycopg2 not installed. Install with: pip install psycopg2-binary")
             log_app("Falling back to JSON file storage (will reset on server restart)")
             USE_DATABASE = False
        
        except Exception as e:
            log_app(f"⚠️ Could not connect to database: {e}")
            log_app("Falling back to JSON file storage (will reset on server restart)")
            USE_DATABASE = False
    else:
         log_app("ℹ️ DATABASE_URL not found in environment variables")
         log_app("Using JSON file storage (will reset on server restart)")
         log_app("To enable persistent storage, add a PostgreSQL database in Render")
         USE_DATABASE = False
init_database()

def load_leaderboard():
    """Load leaderboard from database or JSON file"""
    if USE_DATABASE and db_connection:
        try:
            with db_connection.cursor() as cursor:
                cursor.execute("""
                    SELECT name, score, game_mode, avg_time, accuracy, date, timestamp
                    FROM Leaderboard
                    ORDER BY timestamp DESC
                    """)
                rows = cursor.fetchall()

                #COnvert to list of dicts
                return [
                    {
                        'name': row[0],
                        'score': row[1],
                        'gameMode': row[2],
                        'avgTime': row[3],
                        'accuracy': row[4],
                        'date': row[5].isoformat(),
                        'timestamp': row[6]
                    }
                    for row in rows
                ]
        except Exception as e:
            log_app(f"Error loading from database: {e}")
            log_app("Falling back to JSON file storage")
            return load_leaderboard_json()
    else:
        return load_leaderboard_json()
    
def save_leaderboard(data):
    """Save leaderboard to database or JSON file"""
    if USE_DATABASE and db_connection:
        try:
            # For database, we only need to save new entries
            # (This function is called with full list, but we handle it differently)
            # We'll actually modify how save_score works instead
            pass
        except Exception as e:
            log_app(f"Error saving to database: {e}")
            log_app("Falling back to JSON file")
            save_leaderboard_json(data)
    else:
        save_leaderboard_json(data)

           
def save_score_to_database(entry):
    """Save a single score entry to database"""
    if USE_DATABASE and db_connection:
        try:
            with db_connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO leaderboard 
                    (name, score, game_mode, avg_time, accuracy, date, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    entry['name'],
                    entry['score'],
                    entry['gameMode'],
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
    """Load leaderboard from JSON file (fallback)"""
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_leaderboard_json(data):
    """Save leaderboard to JSON file (fallback)"""
    try:
        with open(LEADERBOARD_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        log_app(f"Error saving to JSON: {e}")

def hardware_button_pressed(button_id):
    """Callback for hardware button press"""
    log_app(f"Hardware button {button_id} pressed")

    # Accept press only if round started and tension animation done
    if game_state["waiting_for_press"] and not game_state["tension_building"]:
        handle_button_press(button_id)
    else:
        if game_state["tension_building"]:
            log_app(f"Button {button_id} ignored - tension still building")
        elif not game_state["waiting_for_press"]:
            log_app(f"Button {button_id} ignored - game not waiting for input")
        else:
            log_app(f"Button {button_id} ignored - unknown state")

def handle_button_press(button_id):
    """Handle button press logic"""
    if not game_state["waiting_for_press"]:
        log_app("Button press rejected - not waiting")
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
        log_app(f"✅ CORRECT button press - reaction time: {reaction_time}ms")
    else:
        game_state["last_message"] = f"❌ Wrong button! Expected {game_state['current_button']}"
        game_state["waiting_for_press"] = False
        game_state["tension_building"] = False
        if HARDWARE_ENABLED and hardware:
            hardware.snap_back()
        log_app(f"❌ WRONG button press - expected {game_state['current_button']}, got {button_id}")
    
    return game_state

# Setup hardware callbacks
if HARDWARE_ENABLED and hardware:
    log_app("Setting up hardware button callbacks...")
    try:
        hardware.set_button_callback(1, lambda: hardware_button_pressed(1))
        hardware.set_button_callback(2, lambda: hardware_button_pressed(2))
        log_app("Hardware callbacks set successfully")
        
        # Cleanup on exit
        atexit.register(hardware.cleanup)
        log_app("Hardware cleanup registered for exit")
    except Exception as e:
        log_app(f"Error setting up hardware callbacks: {e}")
        HARDWARE_ENABLED = False

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
    """Web button presses (software simulation)"""
    log_app(f"Web button {button_id} pressed")
    if HARDWARE_ENABLED and hardware:
        # In hardware mode, treat web presses as hardware presses
        hardware_button_pressed(button_id)
    else:
        # In software mode, handle directly
        handle_button_press(button_id)
    return jsonify(game_state)

@app.route("/api/start_round", methods=["POST"])
def start_round():
    """Start a new round - accepts target_button from JavaScript to sync game states"""
    global game_state
    
    # Get target button from request, or choose randomly if not provided
    data = request.get_json() if request.is_json else {}
    target_button = data.get('target_button') if data else None
    
    if target_button is None:
        target_button = random.choice([1, 2])
    
    game_state["current_button"] = target_button
    game_state["waiting_for_press"] = True
    game_state["last_message"] = f"Ready for Button {game_state['current_button']}!"
    game_state["start_time"] = time.time()
    game_state["tension_building"] = False  # No tension - ready immediately
    
    sync_source = "JavaScript" if target_button == data.get('target_button') else "Flask random"
    log_app(f"🎯 Round started - target button: {game_state['current_button']} (from {sync_source}) - READY IMMEDIATELY")

    return jsonify(game_state)

@app.route("/api/status", methods=["GET"])
def get_status():
    """Get current game state with hardware status"""
    status = game_state.copy()
    status["hardware_enabled"] = HARDWARE_ENABLED
    if HARDWARE_ENABLED and hardware:
        status["hardware_available"] = hardware.is_available()
    else:
        status["hardware_available"] = False
    return jsonify(status)

# ===== LEADERBOARD ROUTES =====

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get top scores for a game mode"""
    game_mode = request.args.get('mode', 'time_attack')
    limit = int(request.args.get('limit', 10))
    
    all_scores = load_leaderboard()
    
    # Filter by game mode
    mode_scores = [s for s in all_scores if s.get('gameMode') == game_mode]
    
    # Sort based on game mode
    if game_mode == 'time_attack':
        mode_scores.sort(key=lambda x: x.get('score', 0), reverse=True)
    else:
        mode_scores.sort(key=lambda x: x.get('avgTime', float('inf')))
    
    return jsonify({
        'success': True,
        'scores': mode_scores[:limit],
        'total': len(mode_scores),
        'storage_type': 'database' if USE_DATABASE else 'json'  # NEW LINE
    })
@app.route('/api/leaderboard', methods=['POST'])
def save_score():
    """Save a new score to leaderboard"""
    data = request.json
    
    # Validate required fields
    required_fields = ['name', 'gameMode', 'score', 'avgTime', 'accuracy']
    if not all(field in data for field in required_fields):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    # Sanitize player name (prevent XSS)
    player_name = data['name'].strip()[:50]  # Max 50 characters
    if not player_name:
        return jsonify({'success': False, 'error': 'Invalid player name'}), 400
    
    # Create new entry
    new_entry = {
        'name': player_name,
        'score': int(data['score']),
        'gameMode': data['gameMode'],
        'difficulty': data.get('difficulty', 'unknown'),  # NEW - save difficulty
        'maxCombo': int(data.get('maxCombo', 0)),
        'avgTime': float(data['avgTime']) if data['avgTime'] != '-' else 0,
        'accuracy': float(data['accuracy']),
        'date': datetime.utcnow().isoformat(),
        'timestamp': datetime.utcnow().timestamp()
    }
    
    # Save to database or JSON
    if USE_DATABASE:
        success = save_score_to_database(new_entry)
        if not success:
            log_app("Database save failed, falling back to JSON")
            # Fallback to JSON
            all_scores = load_leaderboard_json()
            all_scores.append(new_entry)
            save_leaderboard_json(all_scores)
    else:
        # Save to JSON file
        all_scores = load_leaderboard_json()
        all_scores.append(new_entry)
        
        # Keep only top 100 scores per mode to prevent file from getting too large
        mode_scores = [s for s in all_scores if s.get('gameMode') == data['gameMode']]
        other_scores = [s for s in all_scores if s.get('gameMode') != data['gameMode']]
        
        # Sort and limit
        if data['gameMode'] == 'time_attack':
            mode_scores.sort(key=lambda x: x.get('score', 0), reverse=True)
        else:
            mode_scores.sort(key=lambda x: x.get('avgTime', float('inf')))
        
        mode_scores = mode_scores[:100]
        
        # Combine and save
        final_scores = other_scores + mode_scores
        save_leaderboard_json(final_scores)
    
    # Calculate rank
    all_scores = load_leaderboard()
    mode_scores = [s for s in all_scores if s.get('gameMode') == data['gameMode']]
    
    if data['gameMode'] == 'time_attack':
        mode_scores.sort(key=lambda x: x.get('score', 0), reverse=True)
    else:
        mode_scores.sort(key=lambda x: x.get('avgTime', float('inf')))
    
    rank = next((i + 1 for i, s in enumerate(mode_scores) if 
                 s['name'] == player_name and 
                 abs(s['timestamp'] - new_entry['timestamp']) < 1), len(mode_scores))
    
    return jsonify({
        'success': True,
        'rank': rank,
        'total': len(mode_scores),
        'entry': new_entry,
        'storage_type': 'database' if USE_DATABASE else 'json'  # NEW LINE
    })

@app.route('/api/leaderboard/clear', methods=['POST'])
def clear_leaderboard():
    """Clear the entire leaderboard (admin only - add authentication in production!)"""
    # In production, add authentication here!
    
    if USE_DATABASE and db_connection:
        try:
            with db_connection.cursor() as cursor:
                cursor.execute("DELETE FROM leaderboard")
                db_connection.commit()
            log_app("Database leaderboard cleared")
        except Exception as e:
            log_app(f"Error clearing database: {e}")
            return jsonify({'success': False, 'error': str(e)})
    else:
        save_leaderboard_json([])
        log_app("JSON leaderboard cleared")
    
    return jsonify({'success': True, 'message': 'Leaderboard cleared'})

# ===== HARDWARE CONTROL ROUTES =====

@app.route("/api/reset_motor", methods=["POST"])
def reset_motor():
    if HARDWARE_ENABLED and hardware:
        try:
            hardware.set_motor_position(0)
            log_app("Motor reset to zero")
            return jsonify({"status": "Motor reset to zero"})
        except Exception as e:
            log_app(f"Error resetting motor: {e}")
            return jsonify({"status": f"Motor reset failed: {e}"})
    return jsonify({"status": "Hardware not available"})

@app.route("/api/test_motor/<int:position>", methods=["POST"])
def test_motor(position):
    if HARDWARE_ENABLED and hardware:
        try:
            hardware.set_motor_position(position)
            log_app(f"Motor moved to position {position}")
            return jsonify({"status": f"Motor moved to position {position}"})
        except Exception as e:
            log_app(f"Error moving motor: {e}")
            return jsonify({"status": f"Motor move failed: {e}"})
    return jsonify({"status": "Hardware not available"})

@app.route("/api/test_buttons", methods=["GET"])
def test_buttons():
    """Test button states - useful for debugging"""
    if HARDWARE_ENABLED and hardware:
        try:
            import lgpio
            button1_state = lgpio.gpio_read(hardware.pi, hardware.BUTTON_1_PIN)
            button2_state = lgpio.gpio_read(hardware.pi, hardware.BUTTON_2_PIN)
            return jsonify({
                "hardware_available": True,
                "button_1_pin": hardware.BUTTON_1_PIN,
                "button_2_pin": hardware.BUTTON_2_PIN,
                "button_1_state": button1_state,
                "button_2_state": button2_state,
                "note": "State 1 = not pressed (pull-up), State 0 = pressed"
            })
        except Exception as e:
            return jsonify({
                "error": f"Failed to read buttons: {e}",
                "hardware_available": True
            })
    else:
        return jsonify({
            "error": "Hardware not available",
            "hardware_available": False
        })

@app.route("/api/hardware_diagnostics", methods=["GET"])
def hardware_diagnostics():
    """Get hardware diagnostic information"""
    diagnostics = {
        "hardware_enabled": HARDWARE_ENABLED,
        "hardware_object_exists": hardware is not None,
        "database_enabled": USE_DATABASE,  # NEW LINE
        "database_type": "PostgreSQL" if USE_DATABASE else "JSON file",  # NEW LINE
        "system_info": {
            "platform": __import__('sys').platform,
            "python_version": __import__('sys').version
        }
    }
    
    if hardware:
        diagnostics["hardware_available"] = hardware.is_available()
    
    # Check lgpio availability
    try:
        import lgpio
        diagnostics["lgpio_available"] = True
        diagnostics["lgpio_info"] = str(lgpio)
    except ImportError:
        diagnostics["lgpio_available"] = False
    
    # Check GPIO device files
    gpio_devices = ['/dev/gpiochip0', '/dev/gpiomem']
    diagnostics["gpio_devices"] = {}
    for device in gpio_devices:
        diagnostics["gpio_devices"][device] = {
            "exists": os.path.exists(device),
            "readable": False
        }
        if os.path.exists(device):
            try:
                with open(device, 'rb') as f:
                    f.read(1)
                diagnostics["gpio_devices"][device]["readable"] = True
            except:
                pass
    
    return jsonify(diagnostics)

# ===== MAIN =====

if __name__ == "__main__":
    import sys
    
    # Check for debug mode flag
    debug_mode = True
    if "--no-debug" in sys.argv:
        debug_mode = False
        log_app("Debug mode disabled via --no-debug flag")
    
    log_app("=" * 50)
    log_app("Starting Reaction Time Game Server...")
    log_app(f"Hardware enabled: {HARDWARE_ENABLED}")
    log_app(f"Database enabled: {USE_DATABASE}")  # NEW LINE
    log_app(f"Storage type: {'PostgreSQL' if USE_DATABASE else 'JSON file (ephemeral)'}")  # NEW LINE
    log_app(f"Debug mode: {debug_mode}")
    
    if not USE_DATABASE:  # NEW SECTION
        log_app("⚠️ WARNING: Using JSON file storage - data will be lost on server restart!")
        log_app("To enable persistent storage:")
        log_app("  1. Add a PostgreSQL database in Render Dashboard")
        log_app("  2. Install psycopg2-binary: pip install psycopg2-binary")
        log_app("  3. Database will be auto-detected from DATABASE_URL environment variable")
    
    if HARDWARE_ENABLED and hardware:
        log_app("Hardware mode: Physical buttons and stepper motor enabled")
        try:
            hardware.set_motor_position(0)
            log_app("Motor initialized to position 0")
        except Exception as e:
            log_app(f"Error initializing motor: {e}")
    else:
        log_app("Software mode: Web interface only")
        if hardware is None:
            log_app("Reason: Hardware object is None")
        elif not HARDWARE_ENABLED:
            log_app("Reason: Hardware not enabled due to initialization failure")
    
    log_app("=" * 50)
    log_app("Visit /api/hardware_diagnostics for detailed hardware & database status")  # UPDATED LINE
    if not HARDWARE_ENABLED:
        log_app("For hardware mode, try: python3 app.py --no-debug")
    log_app("=" * 50)
    
    # Run the app - bind to 0.0.0.0 and use PORT from environment (for Render)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=debug_mode)