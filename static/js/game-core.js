// ===== Core Game State =====
let gameMode = "time_attack";
let difficulty = "easy";
let targetButton = null;
let startTime = null;
let round = 0;
let maxRounds = 5;
let highScore = Infinity;

// ===== Time Attack State =====
let gameTimer = null;
let gameTimeLeft = 60;
let gameStartTime = null;
let score = 0;
let combo = 0;
let maxCombo = 0;

// ===== Session Storage =====
let sessionResults = [];

// ===== Debouncing State =====
let isProcessingButton = false;
let lastButtonPressTime = 0;
const DEBOUNCE_MS = 100; // Prevent duplicate presses within 100ms

// ===== Settings by Difficulty =====
const difficultySettings = {
  easy: { minDelay: 2000, maxDelay: 4000, timeLimit: 60 },
  medium: { minDelay: 1000, maxDelay: 3000, timeLimit: 45 },
  hard: { minDelay: 500, maxDelay: 2000, timeLimit: 30 }
};

// ===== Game State Access for Other Modules =====
const GameState = {
  get gameMode() { return gameMode; },
  get targetButton() { return targetButton; },
  get sessionResults() { return sessionResults; },
  get score() { return score; },
  get combo() { return combo; },
  get maxCombo() { return maxCombo; },
  get highScore() { return highScore; },
  get round() { return round; },
  get maxRounds() { return maxRounds; }
};

// ===== Core Game Logic Functions =====

function startGame() {
  // Clear any existing timer first
  if (gameTimer) {
    clearInterval(gameTimer);
    gameTimer = null;
  }
  
  gameMode = document.getElementById("mode").value;
  difficulty = document.getElementById("difficulty").value;
  round = 0;
  targetButton = null;
  isProcessingButton = false;
  lastButtonPressTime = 0;
  
  // Log game start to chat
  if (typeof Chat !== 'undefined' && Chat.logGameStart) {
    Chat.logGameStart(gameMode, difficulty);
  }
  
  // Initialize based on game mode
  if (gameMode === "time_attack") {
    gameTimeLeft = difficultySettings[difficulty].timeLimit;
    score = 0;
    combo = 0;
    maxCombo = 0;
    sessionResults = [];
    startTimeAttackTimer();
  } else if (gameMode === "endurance") {
    sessionResults = [];
  } else {
    sessionResults = sessionResults.slice(-20);
  }
  
  // Trigger UI updates
  UI.resetGameInterface();
  UI.updateRoundCounter();
  Metrics.updateLiveMetrics();
  
  setTimeout(nextRound, 1000);
}

function nextRound() {
  UI.clearGlow();
  round++;
  UI.updateRoundCounter();

  // Check end conditions
  if (gameMode === "endurance" && round > maxRounds) {
    endGame();
    return;
  }
  
  if (gameMode === "time_attack" && gameTimeLeft <= 0) {
    return;
  }

  UI.updateStatus("Wait for the glow...");
  
  const { minDelay, maxDelay } = difficultySettings[difficulty];
  let delay = Math.floor(Math.random() * (maxDelay - minDelay + 1)) + minDelay;
  
  // Time attack: reduce delay as time pressure increases
  if (gameMode === "time_attack") {
    const timeProgress = (difficultySettings[difficulty].timeLimit - gameTimeLeft) / difficultySettings[difficulty].timeLimit;
    const speedMultiplier = 1 - (timeProgress * 0.4);
    delay = Math.max(200, Math.floor(delay * speedMultiplier));
    
    UI.updateCountdown(`⏰ Time: ${gameTimeLeft}s | Score: ${score}`);
  } else {
    UI.startCountdownDisplay(delay);
  }

  setTimeout(() => {
    if (gameMode === "time_attack" && gameTimeLeft <= 0) return;
    
    targetButton = Math.floor(Math.random() * 2) + 1;
    isProcessingButton = false; // Reset processing flag for new round
    UI.showTargetButton(targetButton);
    UI.updateStatus(`🎯 Press Button ${targetButton}!`);
    
    if (gameMode !== "time_attack") {
      UI.updateCountdown("REACT NOW!");
    }
    
    startTime = Date.now();
  }, delay);
}

function handleButtonPress(button) {
  const now = Date.now();
  
  // ===== DEBOUNCE CHECK =====
  if (now - lastButtonPressTime < DEBOUNCE_MS) {
    console.log(`Button ${button} debounced (too fast: ${now - lastButtonPressTime}ms)`);
    return;
  }
  lastButtonPressTime = now;
  
  // ===== STATE VALIDATION WITH FEEDBACK =====
  if (!targetButton) {
    console.log(`Button ${button} rejected: No target button set (round not active)`);
    // Optional: Show brief visual feedback
    UI.updateStatus("⏸️ Wait for the button to glow!");
    return;
  }
  
  if (isProcessingButton) {
    console.log(`Button ${button} rejected: Already processing another button press`);
    return;
  }
  
  // ===== LOCK PROCESSING =====
  isProcessingButton = true;
  
  const reactionTime = Date.now() - startTime;
  let statusText = "";
  let points = 0;
  
  if (button === targetButton) {
    // Calculate points for time attack
    if (gameMode === "time_attack") {
      points = Math.max(10, Math.floor(1000 - reactionTime));
      combo++;
      if (combo > maxCombo) maxCombo = combo;
      points = Math.floor(points * (1 + (combo - 1) * 0.1));
      score += points;
      
      statusText = `✅ +${points} pts! ${reactionTime}ms (${combo}x combo)`;
    } else {
      statusText = `✅ Correct! ${reactionTime} ms`;
    }
    
    sessionResults.push({ round, reactionTime, status: "Correct", points: points || 0 });
    
    // Log to chat
    if (typeof Chat !== 'undefined' && Chat.logRoundResult) {
      Chat.logRoundResult(round, reactionTime, "Correct", points);
    }
    
    if (reactionTime < highScore) {
      highScore = reactionTime;
      triggerScreenFlash();
      if (gameMode !== "time_attack") {
        statusText += ` 🎉 NEW RECORD!`;
      }
    }
  } else {
    // Wrong button
    if (gameMode === "time_attack") {
      combo = 0;
      statusText = `❌ Wrong! Combo broken! (needed ${targetButton})`;
    } else {
      statusText = `❌ Wrong! Pressed ${button}, needed ${targetButton}`;
    }
    sessionResults.push({ round, reactionTime: "-", status: "Wrong", points: 0 });
    
    // Log to chat
    if (typeof Chat !== 'undefined' && Chat.logRoundResult) {
      Chat.logRoundResult(round, "-", "Wrong", 0);
    }
  }

  // Update all systems
  UI.updateStatus(statusText);
  UI.updateAttemptsTable();
  Metrics.updateLiveMetrics();
  Storage.saveRecentAttempts();
  Charts.updateChart();
  
  // Call coach with accessible data
  if (typeof miniCoach === 'function') {
    miniCoach(sessionResults);
  }
  
  UI.clearGlow();
  targetButton = null;

  // Schedule next round
  const nextRoundDelay = gameMode === "time_attack" ? 500 : 
                        gameMode === "unlimited" ? 1000 : 2000;
  setTimeout(() => {
    isProcessingButton = false; // Unlock for next round
    nextRound();
  }, nextRoundDelay);
}

function startTimeAttackTimer() {
  gameTimer = setInterval(() => {
    gameTimeLeft--;
    UI.updateCountdown(`⏰ Time: ${gameTimeLeft}s | Score: ${score}`);
    
    if (gameTimeLeft <= 10) {
      UI.setCountdownWarning();
    }
    
    if (gameTimeLeft <= 0) {
      clearInterval(gameTimer);
      gameTimer = null;
      endTimeAttackGame();
    }
  }, 1000);
}

function endTimeAttackGame() {
  if (gameTimer) {
    clearInterval(gameTimer);
    gameTimer = null;
  }
  UI.clearGlow();
  targetButton = null;
  isProcessingButton = false;
  
  const finalMessage = `⏱ Time's Up! Final Score: ${score} points!`;
  UI.updateStatus(finalMessage);
  UI.updateCountdown(`Max Combo: ${maxCombo}x | Total Reactions: ${sessionResults.length}`);
  
  // Log to chat
  if (typeof Chat !== 'undefined' && Chat.logGameEnd) {
    Chat.logGameEnd(`🏁 Game Over! Final Score: ${score} pts | Max Combo: ${maxCombo}x`);
  }
  
  // Calculate stats for leaderboard
  const validTimes = sessionResults.filter(r => r.reactionTime !== "-");
  const avgTime = validTimes.length > 0 ? 
    Math.round(validTimes.reduce((a, b) => a + b.reactionTime, 0) / validTimes.length) : 0;
  const accuracy = sessionResults.length > 0 ? 
    Math.round((validTimes.length / sessionResults.length) * 100) : 0;
  
  // Prompt to save score after a short delay (async function)
  setTimeout(async () => {
    if (typeof Leaderboard !== 'undefined' && Leaderboard.promptSaveScore) {
      await Leaderboard.promptSaveScore("time_attack", score, avgTime, maxCombo);
    }
  }, 500);
  
  // Coach message
  let coachMessage = "";
  if (score > 1000) coachMessage = "🏆 Outstanding performance! You're a time attack master!";
  else if (score > 500) coachMessage = "🔥 Great job! Your reflexes are sharp!";
  else if (score > 200) coachMessage = "💪 Good work! Keep practicing to improve your score!";
  else coachMessage = "🎯 Nice try! Focus on accuracy and speed will follow!";
  
  const coachBox = document.getElementById("coachBox");
  if (coachBox) coachBox.textContent = coachMessage;
  
  if (typeof Chat !== 'undefined' && Chat.logAIFeedback) {
    Chat.logAIFeedback(coachMessage);
  }
}

function endGame() {
  const times = sessionResults.filter(r => r.reactionTime !== "-").map(r => r.reactionTime);
  const avg = times.length ? (times.reduce((a, b) => a + b, 0) / times.length).toFixed(0) : "-";
  const accuracy = ((times.length / sessionResults.length) * 100).toFixed(1);
  
  UI.updateStatus("🏁 Game Complete!");
  UI.updateCountdown(`Average: ${avg}ms | Accuracy: ${accuracy}%`);
  
  // Log to chat
  if (typeof Chat !== 'undefined' && Chat.logGameEnd) {
    Chat.logGameEnd(`🏁 Game Complete! Avg: ${avg}ms | Accuracy: ${accuracy}%`);
  }
  
  // Prompt to save score (async function)
  const currentMode = document.getElementById("mode") ? document.getElementById("mode").value : "endurance";
  setTimeout(async () => {
    if (typeof Leaderboard !== 'undefined' && Leaderboard.promptSaveScore && avg !== "-") {
      await Leaderboard.promptSaveScore(currentMode, 0, parseFloat(avg), parseFloat(accuracy));
    }
  }, 500);
  
  // Final coach message
  if (times.length > 0) {
    const bestTime = Math.min(...times);
    const message = bestTime < 300 ? 
      "🚀 Outstanding reflexes! You're in the top tier!" :
      bestTime < 400 ? 
      "🎯 Great performance! Keep practicing!" :
      "💪 Good work! Regular practice will improve your times!";
    
    const coachBox = document.getElementById("coachBox");
    if (coachBox) coachBox.textContent = message;
    
    // Send to chat
    if (typeof Chat !== 'undefined' && Chat.logAIFeedback) {
      Chat.logAIFeedback(message);
    }
  }
}

// ===== Keyboard Input =====
document.addEventListener("keydown", (e) => {
  if (["1", "2"].includes(e.key)) {
    handleButtonPress(parseInt(e.key));
  }
});

// ===== Mobile Touch Support (add after keyboard input section) =====
function setupMobileTouch() {
  const button1 = document.getElementById('button1');
  const button2 = document.getElementById('button2');

  if (button1 && button2) {
    [button1, button2].forEach((btn, index) =>{ 
    const buttonNumber = index + 1;

    // Touch events for mobile (fires immediately)
    btn.addEventListener('touchstart', (e) =>{
      e.preventDefault(); //Prevents the 300ms delay on mobile browsers
      handleButtonPress(buttonNumber);
    }, { passive: false });
  
    // Optional: Mouse events for desktop
    btn.addEventListener('click', (e) => {
      if (!e.detail || e.detail === 0) return;
      handleButtonPress(buttonNumber);
      });
    });

    console.log("Mobile touch support initialized.");
  }
}



// ===== Initialize from Storage =====
function initializeGame() {
  const stored = Storage.initializeFromStorage();
  if (stored.length) {
    sessionResults.length = 0;
    sessionResults.push(...stored);
    UI.updateAttemptsTable();
    
    // Update high score from stored data
    const times = sessionResults.filter(r => r.reactionTime !== "-").map(r => r.reactionTime);
    if (times.length) {
      highScore = Math.min(...times);
    }
    
    Metrics.updateLiveMetrics();
  }
  setupMobileTouch();
}

// Screen flash for new high scores
function triggerScreenFlash() {
  const flash = document.getElementById('screen-flash');
  if (flash) {
    flash.style.display = 'block';
    setTimeout(() => {
      flash.style.display = 'none';
    }, 200); // Flash for 200ms
  }
}