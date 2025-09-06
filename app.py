from flask import Flask, render_template, jsonify, request
import time
import random
import threading
import atexit

# Import hardware controller
try:
    from hardware_controller import hardware
    HARDWARE_ENABLED = True
    print("Hardware controller loaded successfully!")
except ImportError:
    HARDWARE_ENABLED = False
    print("Hardware controller not available - running in software mode")

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

def hardware_button_pressed(button_id):
    """Callback for hardware button press"""
    print(f"DEBUG: Button {button_id} pressed")  # Debug to see physical input

    # Accept press only if round started and tension animation done
    if game_state["waiting_for_press"] and not game_state["tension_building"]:
        handle_button_press(button_id)
    else:
        print(f"DEBUG: Button {button_id} pressed but game not waiting for input or still tension building")

def handle_button_press(button_id):
    """Handle button press logic"""
    if not game_state["waiting_for_press"]:
        return {"error": "Not waiting for button press"}
    
    reaction_time = int((time.time() - game_state["start_time"]) * 1000)
    
    if button_id == game_state["current_button"]:
        game_state["last_message"] = f"✅ Correct! Reaction time: {reaction_time} ms"
        if game_state["best_time"] is None or reaction_time < game_state["best_time"]:
            game_state["best_time"] = reaction_time
        
        if HARDWARE_ENABLED:
            hardware.performance_meter_update(reaction_time)
        
        game_state["round"] += 1
        game_state["waiting_for_press"] = False
        game_state["tension_building"] = False
    else:
        game_state["last_message"] = f"❌ Wrong button! Expected {game_state['current_button']}"
        game_state["waiting_for_press"] = False
        game_state["tension_building"] = False
        if HARDWARE_ENABLED:
            hardware.snap_back()
    
    return game_state

# Setup hardware callbacks
if HARDWARE_ENABLED:
    hardware.set_button_callback(1, lambda: hardware_button_pressed(1))
    hardware.set_button_callback(2, lambda: hardware_button_pressed(2))
    # Cleanup on exit
    atexit.register(hardware.cleanup)

@app.route("/")
def index():
    return render_template("template.html", hardware_enabled=HARDWARE_ENABLED)

@app.route("/api/buttons", methods=["GET"])
def get_buttons():
    return jsonify(buttons)

@app.route("/api/buttons/<int:button_id>/press", methods=["POST"])
def press_button(button_id):
    """Web button presses (software simulation)"""
    if HARDWARE_ENABLED:
        hardware_button_pressed(button_id)
        return jsonify(game_state)
    return jsonify(handle_button_press(button_id))

@app.route("/api/start_round", methods=["POST"])
def start_round():
    global game_state
    game_state["current_button"] = random.choice([1, 2])
    game_state["waiting_for_press"] = True
    game_state["last_message"] = f"Get ready... Press Button {game_state['current_button']} when it glows!"
    game_state["start_time"] = time.time()
    game_state["tension_building"] = True

    if HARDWARE_ENABLED:
        # Run tension animation in a background thread
        def run_tension():
            tension_duration = random.uniform(2.0, 4.0)
            hardware.tension_build_animation(tension_duration)
            game_state["tension_building"] = False

        threading.Thread(target=run_tension, daemon=True).start()
    else:
        # In software mode, simulate short delay
        def run_tension_software():
            time.sleep(random.uniform(2.0, 4.0))
            game_state["tension_building"] = False

        threading.Thread(target=run_tension_software, daemon=True).start()

    return jsonify(game_state)

@app.route("/api/status", methods=["GET"])
def get_status():
    return jsonify(game_state)

@app.route("/api/reset_motor", methods=["POST"])
def reset_motor():
    if HARDWARE_ENABLED:
        hardware.set_motor_position(0)
        return jsonify({"status": "Motor reset to zero"})
    return jsonify({"status": "Hardware not available"})

@app.route("/api/test_motor/<int:position>", methods=["POST"])
def test_motor(position):
    if HARDWARE_ENABLED:
        hardware.set_motor_position(position)
        return jsonify({"status": f"Motor moved to position {position}"})
    return jsonify({"status": "Hardware not available"})

if __name__ == "__main__":
    print("Starting Reaction Time Game Server...")
    if HARDWARE_ENABLED:
        print("Hardware mode: Physical buttons and stepper motor enabled")
        hardware.set_motor_position(0)
    else:
        print("Software mode: Web interface only")
    
    app.run(host="0.0.0.0", port=5000, debug=True)
