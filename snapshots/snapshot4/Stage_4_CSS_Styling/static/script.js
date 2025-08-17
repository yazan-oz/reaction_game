document.addEventListener("DOMContentLoaded", () => {
    const startBtn = document.getElementById("startBtn");
    const message = document.getElementById("message");
    const bestTimeDisplay = document.getElementById("bestTime");
    const modeSelect = document.getElementById("modeSelect");
    const historyTableBody = document.querySelector("#historyTable tbody");

    let waiting = false;
    let startTime;
    let bestTime = null;
    let gameStarted = false;
    let round = 0;

    startBtn.addEventListener("click", () => {
        if (waiting) return;

        startBtn.style.display = "none"; // hide button
        waiting = true;
        gameStarted = false;
        round++;
        let countdown = 3;
        message.textContent = `Starting in ${countdown}...`;
        document.body.style.backgroundColor = "#f0f0f0";

        const countdownInterval = setInterval(() => {
            countdown--;
            if (countdown > 0) {
                message.textContent = `Starting in ${countdown}...`;
            } else {
                clearInterval(countdownInterval);

                const delay = Math.random() * 1500 + 500;
                message.textContent = "Get ready...";
                setTimeout(() => {
                    message.textContent = "GO!";
                    document.body.style.backgroundColor = "#ffeb3b"; // yellow
                    startTime = new Date().getTime();
                    gameStarted = true;

                    // Optional: confetti for GO!
                    confetti({
                        particleCount: 50,
                        spread: 70,
                        origin: { y: 0.6 }
                    });
                }, delay);
            }
        }, 1000);
    });

    document.body.addEventListener("click", (e) => {
        if (!waiting) return;
        if (e.target.id === "startBtn") return;

        if (!gameStarted) {
            message.textContent = "Too early! Wait for GO!";
            document.body.style.backgroundColor = "#f44336"; // red
            waiting = false;
            startTime = null;
            startBtn.style.display = "inline-block";
            return;
        }

        const reactionTime = new Date().getTime() - startTime;
        message.textContent = `Reaction time: ${reactionTime} ms`;

        // Update best time
        if (bestTime === null || reactionTime < bestTime) {
            bestTime = reactionTime;
            bestTimeDisplay.style.animation = "pop 0.3s ease-in-out";
            setTimeout(() => { bestTimeDisplay.style.animation = ""; }, 300);
        }
        bestTimeDisplay.textContent = `Best time: ${bestTime} ms`;

        // Dynamic background based on speed
        if (reactionTime < 250) {
            document.body.style.backgroundColor = "#4CAF50";
        } else if (reactionTime < 400) {
            document.body.style.backgroundColor = "#ffeb3b";
        } else {
            document.body.style.backgroundColor = "#f44336";
        }

        // Add to history table
        if (historyTableBody) {
            const row = document.createElement("tr");
            row.innerHTML = `<td>${round}</td><td>${modeSelect.value}</td><td>${reactionTime} ms</td>`;
            historyTableBody.prepend(row); // newest on top
        }

        setTimeout(() => {
            document.body.style.backgroundColor = "#f0f0f0";
        }, 1000);

        waiting = false;
        startTime = null;
        gameStarted = false;
        startBtn.style.display = "inline-block";
    });
});
