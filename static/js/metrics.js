// ===== Metrics Module =====
const Metrics = {
  
  updateLiveMetrics() {
    const validTimes = GameState.sessionResults.filter(r => r.reactionTime !== "-");
    const correctCount = GameState.sessionResults.filter(r => r.status === "Correct").length;
    const wrongCount = GameState.sessionResults.filter(r => r.status === "Wrong").length;
    
    // Average Time
    this.updateAverageTime(validTimes);
    
    // Update labels and values based on game mode
    this.updateCorrectWrongLabels(correctCount, wrongCount);
    
    // High Score
    this.updateHighScore();
  },

  updateAverageTime(validTimes) {
    const avgElement = document.getElementById("avg-time");
    if (!avgElement) return;

    if (validTimes.length > 0) {
      const avgTime = (validTimes.reduce((a, b) => a + b.reactionTime, 0) / validTimes.length).toFixed(0);
      avgElement.textContent = `${avgTime} ms`;
      
      // Add color coding
      avgElement.className = "metric-value";
      if (avgTime < 300) avgElement.classList.add("fast");
      else if (avgTime > 500) avgElement.classList.add("slow");
    } else {
      avgElement.textContent = "-";
      avgElement.className = "metric-value";
    }
  },

  updateCorrectWrongLabels(correctCount, wrongCount) {
    const correctLabel = document.getElementById("correct-label");
    const wrongLabel = document.getElementById("wrong-label");
    const correctCountElement = document.getElementById("correct-count");
    const wrongCountElement = document.getElementById("wrong-count");
    
    if (GameState.gameMode === "time_attack") {
      // Show score and combo for time attack
      if (correctLabel) correctLabel.textContent = "🎯 Score";
      if (wrongLabel) wrongLabel.textContent = "🔥 Combo";
      if (correctCountElement) correctCountElement.textContent = `${GameState.score}`;
      if (wrongCountElement) wrongCountElement.textContent = `${GameState.combo}x`;
    } else {
      // Show counts for other modes
      if (correctLabel) correctLabel.textContent = "✅ Correct";
      if (wrongLabel) wrongLabel.textContent = "❌ Wrong";
      if (correctCountElement) correctCountElement.textContent = correctCount;
      if (wrongCountElement) wrongCountElement.textContent = wrongCount;
    }
  },

  updateHighScore() {
    const highScoreElement = document.getElementById("highscore");
    if (!highScoreElement) return;

    if (GameState.highScore !== Infinity) {
      highScoreElement.textContent = `${GameState.highScore} ms`;
      highScoreElement.className = "metric-value perfect";
    } else {
      highScoreElement.textContent = "-";
      highScoreElement.className = "metric-value";
    }
  },

  calculateHighScore() {
    const times = GameState.sessionResults.filter(r => r.reactionTime !== "-").map(r => r.reactionTime);
    if (times.length) {
      return Math.min(...times);
    }
    return Infinity;
  }
};

// ===== Storage Module =====
const Storage = {
  
  saveRecentAttempts() {
    const last20 = GameState.sessionResults.slice(-20);
    localStorage.setItem("reactionGameAttempts", JSON.stringify(last20));
  },

  loadStoredAttempts() {
    const stored = JSON.parse(localStorage.getItem("reactionGameAttempts") || "[]");
    return stored.length ? stored.slice(-20) : [];
  },

  initializeFromStorage() {
    const stored = this.loadStoredAttempts();
    if (stored.length) {
      // Note: sessionResults is managed by game-core.js
      // This function returns data for initialization
      return stored;
    }
    return [];
  }
};
