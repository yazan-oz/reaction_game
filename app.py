from flask import Flask, render_template, jsonify, request
import time
import random
import threading
import atexit

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

def hardware_button_pressed(button_id):
    """Callback for hardware button press"""
    log_app(f"Hardware button {button_id} pressed")

    # Accept press only if round started and tension animation done
    if game_state["waiting_for_press"] and not game_state["tension_building"]:
        handle_button_press(button_id)
    else:
        log_app(f"Button {button_id} ignored - game not waiting or tension building")

def handle_button_press(button_id):
    """Handle button press logic"""
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
        log_app(f"Correct button press - reaction time: {reaction_time}ms")
    else:
        game_state["last_message"] = f"❌ Wrong button! Expected {game_state['current_button']}"
        game_state["waiting_for_press"] = False
        game_state["tension_building"] = False
        if HARDWARE_ENABLED and hardware:
            hardware.snap_back()
        log_app(f"Wrong button press - expected {game_state['current_button']}, got {button_id}")
    
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

@app.route("/test")
def test_page():
    """Test page for physical buttons"""
    return '''<!DOCTYPE html>
<html>
<head>
    <title>Physical Button Test</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            max-width: 800px; 
            margin: 0 auto; 
            padding: 20px;
            background: #1a1a1a;
            color: #ffffff;
        }
        .status {
            background: #333;
            padding: 20px;
            border-radius: 8px;
            margin: 10px 0;
        }
        .button {
            background: #4CAF50;
            border: none;
            color: white;
            padding: 15px 32px;
            text-align: center;
            font-size: 16px;
            margin: 10px;
            cursor: pointer;
            border-radius: 8px;
        }
        .button:hover { background: #45a049; }
        .button:disabled { 
            background: #666; 
            cursor: not-allowed; 
        }
        .logs {
            background: #222;
            border: 1px solid #444;
            padding: 10px;
            height: 300px;
            overflow-y: scroll;
            font-family: monospace;
            font-size: 12px;
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }
    </style>
</head>
<body>
    <h1>Physical Button Test</h1>
    
    <div class="status">
        <h3>Game Status</h3>
        <div id="gameStatus">Waiting to start...</div>
        <div id="gameMessage"></div>
        <div id="gameRound">Round: 0</div>
        <div id="bestTime">Best time: None</div>
    </div>
    
    <div class="status">
        <h3>Hardware Status</h3>
        <div id="hardwareStatus">Checking...</div>
        <div id="buttonStates">Button states: Checking...</div>
    </div>
    
    <div>
        <button class="button" onclick="startRound()">Start Round</button>
        <button class="button" onclick="testButton(1)">Test Virtual Button 1</button>
        <button class="button" onclick="testButton(2)">Test Virtual Button 2</button>
        <button class="button" onclick="resetGame()">Reset Game</button>
    </div>
    
    <div class="status">
        <h3>Instructions</h3>
        <ol>
            <li>Click "Start Round"</li>
            <li>Wait for the countdown/tension period (2-4 seconds)</li>
            <li>When a button is announced, press your PHYSICAL button</li>
            <li>The logs below will show if your physical button is detected</li>
        </ol>
        
        <p><strong>Physical Button Test:</strong> Press your physical buttons anytime to see if they're detected (will show in logs even if game isn't running)</p>
    </div>
    
    <div class="status">
        <h3>Real-time Logs</h3>
        <div class="logs" id="logs"></div>
    </div>

    <script>
        let gameState = {};
        
        function log(message) {
            const timestamp = new Date().toLocaleTimeString();
            const logs = document.getElementById('logs');
            logs.innerHTML += `[${timestamp}] ${message}\\n`;
            logs.scrollTop = logs.scrollHeight;
        }
        
        function updateDisplay() {
            document.getElementById('gameStatus').textContent = 
                gameState.waiting_for_press ? 
                (gameState.tension_building ? 'Building tension...' : `Waiting for Button ${gameState.current_button}`) : 
                'Ready to start';
                
            document.getElementById('gameMessage').textContent = gameState.last_message || '';
            document.getElementById('gameRound').textContent = `Round: ${gameState.round || 0}`;
            document.getElementById('bestTime').textContent = `Best time: ${gameState.best_time ? gameState.best_time + 'ms' : 'None'}`;
        }
        
        async function fetchGameState() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                // Check if game state changed
                const stateChanged = JSON.stringify(gameState) !== JSON.stringify(data);
                if (stateChanged) {
                    const oldWaiting = gameState.waiting_for_press;
                    const oldTension = gameState.tension_building;
                    const oldMessage = gameState.last_message;
                    
                    gameState = data;
                    updateDisplay();
                    
                    // Log important state changes
                    if (data.waiting_for_press && !data.tension_building && (oldTension || !oldWaiting)) {
                        log(`🎯 Ready for Button ${data.current_button}! Press your physical button now!`);
                    }
                    if (data.last_message && data.last_message !== oldMessage) {
                        if (data.last_message.includes('Correct!')) {
                            log(`✅ ${data.last_message}`);
                        } else if (data.last_message.includes('Wrong')) {
                            log(`❌ ${data.last_message}`);
                        } else {
                            log(`📝 ${data.last_message}`);
                        }
                    }
                }
            } catch (error) {
                log(`Error fetching game state: ${error.message}`);
            }
        }
        
        async function fetchHardwareStatus() {
            try {
                const response = await fetch('/api/test_buttons');
                const data = await response.json();
                
                if (data.hardware_available) {
                    document.getElementById('hardwareStatus').textContent = '✅ Hardware Available';
                    document.getElementById('buttonStates').textContent = 
                        `Pin ${data.button_1_pin}: ${data.button_1_state}, Pin ${data.button_2_pin}: ${data.button_2_state}`;
                } else {
                    document.getElementById('hardwareStatus').textContent = '❌ Hardware Not Available';
                    document.getElementById('buttonStates').textContent = data.error || 'No hardware detected';
                }
            } catch (error) {
                document.getElementById('hardwareStatus').textContent = '❌ Hardware Check Failed';
                document.getElementById('buttonStates').textContent = error.message;
            }
        }
        
        async function startRound() {
            try {
                log('🚀 Starting new round...');
                const response = await fetch('/api/start_round', { method: 'POST' });
                const data = await response.json();
                gameState = data;
                updateDisplay();
                log(`Round started - target button: ${data.current_button}`);
                log('⏳ Tension building... wait for the signal!');
            } catch (error) {
                log(`Error starting round: ${error.message}`);
            }
        }
        
        async function testButton(buttonId) {
            try {
                log(`🖱️ Testing virtual button ${buttonId}...`);
                const response = await fetch(`/api/buttons/${buttonId}/press`, { method: 'POST' });
                const data = await response.json();
                gameState = data;
                updateDisplay();
            } catch (error) {
                log(`Error testing button: ${error.message}`);
            }
        }
        
        function resetGame() {
            log('🔄 Game reset');
            gameState = {
                round: 0,
                waiting_for_press: false,
                current_button: null,
                last_message: "Game reset",
                best_time: null,
                tension_building: false
            };
            updateDisplay();
        }
        
        // Update every 200ms for real-time feel
        setInterval(fetchGameState, 200);
        
        // Update hardware status every 2 seconds
        setInterval(fetchHardwareStatus, 2000);
        
        // Initial load
        fetchGameState();
        fetchHardwareStatus();
        
        log('🎮 Physical Button Test loaded');
        log('📝 Press physical buttons anytime to test detection');
        log('🎯 Start a round and press physical buttons when prompted');
    </script>
</body>
</html>'''

@app.route("/")
def index():
    return render_template("template.html", hardware_enabled=HARDWARE_ENABLED)

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
    global game_state
    game_state["current_button"] = random.choice([1, 2])
    game_state["waiting_for_press"] = True
    game_state["last_message"] = f"Get ready... Press Button {game_state['current_button']} when it glows!"
    game_state["start_time"] = time.time()
    game_state["tension_building"] = True
    
    log_app(f"Round started - target button: {game_state['current_button']}")

    if HARDWARE_ENABLED and hardware:
        # Run tension animation in a background thread
        def run_tension():
            try:
                tension_duration = random.uniform(2.0, 4.0)
                hardware.tension_build_animation(tension_duration)
                game_state["tension_building"] = False
                log_app("Hardware tension animation complete")
            except Exception as e:
                log_app(f"Error in tension animation: {e}")
                game_state["tension_building"] = False

        threading.Thread(target=run_tension, daemon=True).start()
    else:
        # In software mode, simulate short delay
        def run_tension_software():
            try:
                duration = random.uniform(2.0, 4.0)
                time.sleep(duration)
                game_state["tension_building"] = False
                log_app("Software tension delay complete")
            except Exception as e:
                log_app(f"Error in software tension: {e}")
                game_state["tension_building"] = False

        threading.Thread(target=run_tension_software, daemon=True).start()

    return jsonify(game_state)

@app.route("/api/status", methods=["GET"])
def get_status():
    # Add hardware status to game state
    status = game_state.copy()
    status["hardware_enabled"] = HARDWARE_ENABLED
    if HARDWARE_ENABLED and hardware:
        status["hardware_available"] = hardware.is_available()
    else:
        status["hardware_available"] = False
    return jsonify(status)

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
def hardware_diagnostics():
    """Get hardware diagnostic information"""
    diagnostics = {
        "hardware_enabled": HARDWARE_ENABLED,
        "hardware_object_exists": hardware is not None,
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
    import os
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
    log_app(f"Debug mode: {debug_mode}")
    
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
    log_app("Visit http://localhost:5000/api/hardware_diagnostics for detailed hardware status")
    if not HARDWARE_ENABLED:
        log_app("For hardware mode, try: python3 app.py --no-debug")
    log_app("=" * 50)
    
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)