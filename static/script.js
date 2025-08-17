document.addEventListener("DOMContentLoaded", () => {
    const buttonContainer = document.getElementById("buttonContainer");
    const startRoundBtn = document.getElementById("startRoundBtn");
    const statusBox = document.getElementById("status");
    const reactionTimeBox = document.getElementById("reactionTime");
    const bestTimeDisplay = document.getElementById("bestTime");

    let buttons = [];
    let gameState = {};

    async function loadButtons() {
        const res = await fetch("/api/buttons");
        buttons = await res.json();
        buttonContainer.innerHTML = "";
        buttons.forEach(button => {
            const btn = document.createElement("button");
            btn.textContent = button.name;
            btn.dataset.id = button.id;
            btn.classList.add("game-btn");
            buttonContainer.appendChild(btn);
        });
    }

    async function updateStatus() {
        const res = await fetch("/api/status");
        gameState = await res.json();

        // Countdown / messages
        statusBox.textContent = gameState.last_message;

        // Reaction time display
        if (gameState.last_reaction !== undefined) {
            reactionTimeBox.textContent = `Reaction time: ${gameState.last_reaction} ms`;
        }

        // Best reaction time
        if (gameState.best_time) {
            bestTimeDisplay.textContent = `Best reaction time: ${gameState.best_time} ms`;
        }

        // Highlight target button
        Array.from(buttonContainer.children).forEach(btn => {
            btn.classList.remove("active-button");
            if (gameState.waiting_for_press && parseInt(btn.dataset.id) === gameState.current_button) {
                btn.classList.add("active-button");
            }
        });
    }

    buttonContainer.addEventListener("click", async (e) => {
        if (!e.target.classList.contains("game-btn")) return;
        const btnId = e.target.dataset.id;
        await fetch(`/api/buttons/${btnId}/press`, { method: "POST" });
        updateStatus();
    });

    startRoundBtn.addEventListener("click", async () => {
        // Small countdown before the round starts
        let countdown = 3;
        startRoundBtn.disabled = true;
        const countdownInterval = setInterval(() => {
            if (countdown > 0) {
                statusBox.textContent = `Starting in ${countdown}...`;
                countdown--;
            } else {
                clearInterval(countdownInterval);
                startRoundBtn.disabled = false;
                // Trigger round start on backend
                fetch("/api/start_round", { method: "POST" }).then(updateStatus);
            }
        }, 1000);
    });

    // Periodic status update
    setInterval(updateStatus, 1000);
    loadButtons();
});
