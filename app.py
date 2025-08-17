from flask import Flask, render_template, jsonify, request
import time
import random

app = Flask(__name__)

# Buttons and game state
buttons = [
    {"id": 1, "name": "Button 1", "state": False},
    {"id": 2, "name": "Button 2", "state": False},
    {"id": 3, "name": "Button 3", "state": False},
]

game_state = {
    "round": 0,
    "waiting_for_press": False,
    "current_button": None,
    "last_message": "Game not started",
    "best_time": None,
    "start_time": None
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/buttons", methods=["GET"])
def get_buttons():
    return jsonify(buttons)

@app.route("/api/buttons/<int:button_id>/press", methods=["POST"])
def press_button(button_id):
    global game_state
    button = next((b for b in buttons if b["id"] == button_id), None)
    if not button:
        return jsonify({"error": "Button not found"}), 404

    # Game logic: check if waiting for this button
    if game_state["waiting_for_press"] and button_id == game_state["current_button"]:
        reaction_time = int((time.time() - game_state["start_time"]) * 1000)
        game_state["last_message"] = f"✅ Correct! Reaction time: {reaction_time} ms"
        if game_state["best_time"] is None or reaction_time < game_state["best_time"]:
            game_state["best_time"] = reaction_time
        game_state["round"] += 1
        game_state["waiting_for_press"] = False
    else:
        # Wrong or too early
        game_state["last_message"] = "❌ Wrong button or too early!"
        game_state["waiting_for_press"] = False

    return jsonify(game_state)

@app.route("/api/start_round", methods=["POST"])
def start_round():
    global game_state
    game_state["round"] += 1
    game_state["current_button"] = random.choice([b["id"] for b in buttons])
    game_state["waiting_for_press"] = True
    game_state["last_message"] = f"Round {game_state['round']}: Press Button {game_state['current_button']}"
    game_state["start_time"] = time.time()
    return jsonify(game_state)

@app.route("/api/status", methods=["GET"])
def get_status():
    return jsonify(game_state)

if __name__ == "__main__":
    app.run(debug=True)
