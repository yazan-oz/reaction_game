// ===== UI Updates Module =====
const UI = {
  
  updateStatus(message) {
    const statusEl = document.getElementById("status");
    if (statusEl) statusEl.textContent = message;
  },

  updateCountdown(message) {
    const countdownEl = document.getElementById("countdown");
    if (countdownEl) countdownEl.textContent = message;
  },

  setCountdownWarning() {
    const countdownEl = document.getElementById("countdown");
    if (countdownEl) countdownEl.style.color = "#e74c3c";
  },

  resetCountdownColor() {
    const countdownEl = document.getElementById("countdown");
    if (countdownEl) countdownEl.style.color = "#f1c40f";
  },

  showTargetButton(buttonNumber) {
    this.clearGlow();
    const targetBtn = document.getElementById(`button${buttonNumber}`);
    if (targetBtn) targetBtn.classList.add("glow");
  },

  clearGlow() {
    document.querySelectorAll(".game-button").forEach(btn => 
      btn.classList.remove("glow")
    );
  },

  celebrateNewRecord() {
    if (typeof confetti === 'function') {
      confetti({ particleCount: 100, spread: 70, origin: { y: 0.6 } });
    }
  },

  updateRoundCounter() {
    const roundCounterEl = document.getElementById("round-counter");
    if (!roundCounterEl) return;

    if (GameState.gameMode === "time_attack") {
      roundCounterEl.textContent = `Reactions: ${GameState.sessionResults.length} | Max Combo: ${GameState.maxCombo}x`;
    } else {
      const maxRoundsText = GameState.gameMode === "unlimited" ? "∞" : GameState.maxRounds;
      roundCounterEl.textContent = `Round ${GameState.round} of ${maxRoundsText}`;
    }
  },

  updateAttemptsTable() {
    const tbody = document.querySelector("#attempts-table tbody");
    if (!tbody) return;
    
    tbody.innerHTML = "";
    GameState.sessionResults.forEach(r => {
      const tr = document.createElement("tr");
      const pointsDisplay = r.points !== undefined ? r.points : "-";
      tr.innerHTML = `<td>${r.round}</td><td>${r.reactionTime}</td><td>${r.status}</td><td>${pointsDisplay}</td>`;
      tbody.appendChild(tr);
    });
  },

  resetGameInterface() {
    this.resetCountdownColor();
    document.querySelector("#attempts-table tbody").innerHTML = "";
    document.getElementById("results").innerHTML = "";
    this.updateStatus("Get ready for the game!");
    document.getElementById("coachBox").textContent = "Focus and stay alert! 🎯";
  },

  startCountdownDisplay(delay) {
    let countdownTime = Math.ceil(delay / 1000);
    const countdownInterval = setInterval(() => {
      countdownTime--;
      if (countdownTime > 0) {
        this.updateCountdown(`⏱️ ${countdownTime}...`);
      } else {
        this.updateCountdown("NOW!");
        clearInterval(countdownInterval);
      }
    }, 1000);
  }
};
