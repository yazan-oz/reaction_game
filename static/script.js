// =========================
// Reaction Game Script
// =========================

// --- Global Variables ---
let gameMode = null;
let difficulty = null;
let activeButton = null;
let reactionTimes = [];
let roundCount = 0;
let maxRounds = 0;
let gameActive = false;

// --- Utility: Random Delay ---
function randomDelay(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

// --- Start Game ---
function startGame(selectedMode, selectedDifficulty = null) {
    gameMode = selectedMode;
    difficulty = selectedDifficulty;
    reactionTimes = [];
    roundCount = 0;
    gameActive = true;

    if (gameMode === "classic") {
        if (difficulty === "easy") maxRounds = 5;
        if (difficulty === "medium") maxRounds = 7;
        if (difficulty === "hard") maxRounds = 10;
    } else if (gameMode === "endurance") {
        maxRounds = 5; // fixed 5 rounds
    } else if (gameMode === "unlimited") {
        maxRounds = Infinity; // goes until user stops
    }

    document.getElementById("status").textContent = "Game Started!";
    nextRound();
}

// --- Start New Round ---
function nextRound() {
    if (!gameActive) return;

    // End game if Classic/Endurance is finished
    if ((gameMode === "classic" || gameMode === "endurance") && roundCount >= maxRounds) {
        endGame();
        return;
    }

    roundCount++;
    document.getElementById("status").textContent = `Round ${roundCount}`;

    // Clear previous active button
    if (activeButton) {
        activeButton.classList.remove("active");
        activeButton = null;
    }

    // Choose random button
    const buttons = document.querySelectorAll(".game-button");
    const randomIndex = Math.floor(Math.random() * buttons.length);
    activeButton = buttons[randomIndex];

    // Delay before glowing
    const delay = randomDelay(1000, 3000);
    setTimeout(() => {
        if (!gameActive) return;
        activeButton.classList.add("active"); // Glow green
        activeButton.dataset.startTime = Date.now(); // Track time
    }, delay);
}

// --- Handle Button Click ---
function handleButtonClick(event) {
    if (!gameActive) return;

    const clickedButton = event.target;

    if (clickedButton === activeButton && activeButton.classList.contains("active")) {
        const reactionTime = Date.now() - activeButton.dataset.startTime;
        reactionTimes.push(reactionTime);

        document.getElementById("status").textContent =
            `✅ Correct! Reaction Time: ${reactionTime} ms`;

        activeButton.classList.remove("active");
        activeButton = null;

        // ----- Add this line to update the metrics panel -----
        updateMetrics();
    } else {
        document.getElementById("status").textContent = `❌ Wrong button!`;
        // Optional: store a "-" or wrong attempt if you track reactionTimes with status
        reactionTimes.push("-");
        
        // Update metrics even for wrong presses
        updateMetrics();
    }

    // Continue to the next round if applicable...
}


// --- End Game ---
function endGame() {
    gameActive = false;
    if (reactionTimes.length === 0) {
        document.getElementById("status").textContent = "Game Over! No results recorded.";
        return;
    }

    let resultMessage = "Game Over! ";
    if (gameMode === "endurance") {
        const avgTime = Math.round(
            reactionTimes.reduce((a, b) => a + b, 0) / reactionTimes.length
        );
        resultMessage += `Average Reaction Time: ${avgTime} ms`;
    } else {
        const bestTime = Math.min(...reactionTimes);
        resultMessage += `Best Reaction Time: ${bestTime} ms`;
    }

    document.getElementById("status").textContent = resultMessage;
}
function updateMetrics(){
  const validTimes = sessionResults.filter(r=>r.reactionTime!=="-").map(r=>r.reactionTime);
  const avg = validTimes.length ? (validTimes.reduce((a,b)=>a+b,0)/validTimes.length).toFixed(2) : "-";
  const correct = sessionResults.filter(r=>r.status==="Correct").length;
  const wrong = sessionResults.filter(r=>r.status==="Wrong").length;

  document.getElementById("avg-time").textContent = avg;
  document.getElementById("correct-count").textContent = correct;
  document.getElementById("wrong-count").textContent = wrong;
  document.getElementById("highscore").textContent = highScore === Infinity ? "-" : highScore;
}


// --- Event Listeners ---
document.querySelectorAll(".game-button").forEach(button => {
    button.addEventListener("click", handleButtonClick);
});
