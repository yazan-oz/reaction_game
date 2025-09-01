// ===== Game State =====
let gameMode = "time_attack"; // Default to time attack now
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

// ===== Settings by Difficulty =====
const difficultySettings = {
  easy: { minDelay:2000, maxDelay:4000, timeLimit: 60 },
  medium: { minDelay:1000, maxDelay:3000, timeLimit: 45 },
  hard: { minDelay:500, maxDelay:2000, timeLimit: 30 }
};

// ===== Chart =====
let reactionChart = null;
function initChart() {
  const ctx = document.getElementById('reactionChart').getContext('2d');
  reactionChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [
        {
          label: 'Reaction Time (ms)',
          data: [],
          borderColor: '#2ecc71',
          backgroundColor: 'rgba(46, 204, 113, 0.2)',
          tension: 0.2,
          fill: true
        },
        {
          label: 'Accuracy (1=Correct, 0=Wrong)',
          data: [],
          borderColor: '#3498db',
          backgroundColor: 'rgba(52, 152, 219, 0.2)',
          tension: 0.2,
          fill: false,
          yAxisID: 'accuracy'
        }
      ]
    },
    options: { 
      responsive: true, 
      scales: { 
        y: { 
          beginAtZero: true,
          title: { display: true, text: 'Reaction Time (ms)' }
        },
        accuracy: {
          type: 'linear',
          display: true,
          position: 'right',
          min: 0,
          max: 1,
          title: { display: true, text: 'Accuracy' }
        }
      }
    }
  });
}

function updateChart() {
  if (!reactionChart) return;
  reactionChart.data.labels = sessionResults.map(r => `R${r.round}`);
  reactionChart.data.datasets[0].data = sessionResults.map(r => r.reactionTime === "-" ? null : r.reactionTime);
  reactionChart.data.datasets[1].data = sessionResults.map(r => r.status==="Correct"?1:0);
  reactionChart.update();
}

// ===== Update Live Metrics =====
function updateLiveMetrics() {
  const validTimes = sessionResults.filter(r => r.reactionTime !== "-");
  const correctCount = sessionResults.filter(r => r.status === "Correct").length;
  const wrongCount = sessionResults.filter(r => r.status === "Wrong").length;
  
  // Average Time
  const avgElement = document.getElementById("avg-time");
  if (avgElement) {
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
  }
  
  // Update labels and values based on game mode
  const correctLabel = document.getElementById("correct-label");
  const wrongLabel = document.getElementById("wrong-label");
  const correctCountElement = document.getElementById("correct-count");
  const wrongCountElement = document.getElementById("wrong-count");
  
  if (gameMode === "time_attack") {
    // Show score and combo for time attack
    if (correctLabel) correctLabel.textContent = "🎯 Score";
    if (wrongLabel) wrongLabel.textContent = "🔥 Combo";
    if (correctCountElement) correctCountElement.textContent = `${score}`;
    if (wrongCountElement) wrongCountElement.textContent = `${combo}x`;
  } else {
    // Show counts for other modes
    if (correctLabel) correctLabel.textContent = "✅ Correct";
    if (wrongLabel) wrongLabel.textContent = "❌ Wrong";
    if (correctCountElement) correctCountElement.textContent = correctCount;
    if (wrongCountElement) wrongCountElement.textContent = wrongCount;
  }
  
  // High Score
  const highScoreElement = document.getElementById("highscore");
  if (highScoreElement) {
    if (highScore !== Infinity) {
      highScoreElement.textContent = `${highScore} ms`;
      highScoreElement.className = "metric-value perfect";
    } else {
      highScoreElement.textContent = "-";
      highScoreElement.className = "metric-value";
    }
  }
}

// ===== Initialize =====
window.addEventListener("DOMContentLoaded", () => {
  const stored = JSON.parse(localStorage.getItem("reactionGameAttempts")||"[]");
  if(stored.length){
    sessionResults = stored.slice(-20);
    updateAttemptsTable();
    updateHighScore();
    updateLiveMetrics();
  }
  initChart();
  updateChart();
});

// ===== Start Game =====
function startGame(){
  // Clear any existing timer first!
  if (gameTimer) {
    clearInterval(gameTimer);
    gameTimer = null;
  }
  
  gameMode = document.getElementById("mode").value;
  difficulty = document.getElementById("difficulty").value;
  round = 0;
  targetButton = null;
  
  // Reset countdown color
  document.getElementById("countdown").style.color = "#f1c40f";
  
  // Initialize based on game mode
  if (gameMode === "time_attack") {
    // Time Attack setup
    gameTimeLeft = difficultySettings[difficulty].timeLimit;
    score = 0;
    combo = 0;
    maxCombo = 0;
    sessionResults = []; // Fresh start
    startTimeAttackTimer();
  } else if (gameMode === "endurance") {
    sessionResults = []; // Fresh start for endurance
  } else {
    // Unlimited - keep some history
    sessionResults = sessionResults.slice(-20);
  }
  
  document.querySelector("#attempts-table tbody").innerHTML = "";
  document.getElementById("results").innerHTML = "";
  document.getElementById("status").textContent = "Get ready for the game!";
  document.getElementById("coachBox").textContent = "Focus and stay alert! 🎯";
  
  updateRoundCounter();
  updateLiveMetrics();
  setTimeout(nextRound, 1000);
}

// ===== Time Attack Timer =====
function startTimeAttackTimer() {
  const countdownElement = document.getElementById("countdown");
  
  gameTimer = setInterval(() => {
    gameTimeLeft--;
    countdownElement.textContent = `⏰ Time: ${gameTimeLeft}s | Score: ${score}`;
    
    if (gameTimeLeft <= 10) {
      countdownElement.style.color = "#e74c3c"; // Red warning
    }
    
    if (gameTimeLeft <= 0) {
      clearInterval(gameTimer);
      gameTimer = null;
      endTimeAttackGame();
    }
  }, 1000);
}

function endTimeAttackGame() {
  // Make sure we clean up everything
  if (gameTimer) {
    clearInterval(gameTimer);
    gameTimer = null;
  }
  clearGlow();
  targetButton = null;
  
  const finalMessage = `🏁 Time's Up! Final Score: ${score} points!`;
  document.getElementById("status").textContent = finalMessage;
  document.getElementById("countdown").textContent = `Max Combo: ${maxCombo}x | Total Reactions: ${sessionResults.length}`;
  
  // Coach final message
  let coachMessage = "";
  if (score > 1000) coachMessage = "🏆 Outstanding performance! You're a time attack master!";
  else if (score > 500) coachMessage = "🔥 Great job! Your reflexes are sharp!";
  else if (score > 200) coachMessage = "💪 Good work! Keep practicing to improve your score!";
  else coachMessage = "🎯 Nice try! Focus on accuracy and speed will follow!";
  
  document.getElementById("coachBox").textContent = coachMessage;
}

// ===== Next Round =====
function nextRound(){
  clearGlow();
  round++;
  updateRoundCounter();

  // Check end conditions
  if(gameMode === "endurance" && round > maxRounds){
    endGame();
    return;
  }
  
  // For time attack, check if time is up
  if(gameMode === "time_attack" && gameTimeLeft <= 0) {
    return; // Game already ended
  }

  document.getElementById("status").textContent = "Wait for the glow...";
  
  const {minDelay, maxDelay} = difficultySettings[difficulty];
  let delay = Math.floor(Math.random()*(maxDelay-minDelay+1))+minDelay;
  
  // Time attack: reduce delay as time pressure increases
  if (gameMode === "time_attack") {
    const timeProgress = (difficultySettings[difficulty].timeLimit - gameTimeLeft) / difficultySettings[difficulty].timeLimit;
    const speedMultiplier = 1 - (timeProgress * 0.4);
    delay = Math.max(200, Math.floor(delay * speedMultiplier));
    
    document.getElementById("countdown").textContent = `⏰ Time: ${gameTimeLeft}s | Score: ${score}`;
  } else {
    // Countdown display for other modes
    let countdownTime = Math.ceil(delay / 1000);
    const countdownInterval = setInterval(() => {
      countdownTime--;
      if (countdownTime > 0) {
        document.getElementById("countdown").textContent = `⏱️ ${countdownTime}...`;
      } else {
        document.getElementById("countdown").textContent = "NOW!";
        clearInterval(countdownInterval);
      }
    }, 1000);
  }

  setTimeout(()=>{
    // Double check time attack hasn't ended and we have time left
    if(gameMode === "time_attack" && gameTimeLeft <= 0) return;
    
    targetButton = Math.floor(Math.random()*3)+1;
    document.getElementById(`button${targetButton}`).classList.add("glow");
    document.getElementById("status").textContent = `🎯 Press Button ${targetButton}!`;
    
    if (gameMode !== "time_attack") {
      document.getElementById("countdown").textContent = "REACT NOW!";
    }
    
    startTime = Date.now();
  }, delay);
}

// ===== Handle Button Press =====
function handleButtonPress(button){
  if(!targetButton) return;

  let reactionTime = Date.now() - startTime;
  let statusText="";
  let points = 0;
  
  if(button===targetButton){
    // Calculate points for time attack
    if (gameMode === "time_attack") {
      // Base points: faster reaction = more points
      points = Math.max(10, Math.floor(1000 - reactionTime));
      // Combo multiplier
      combo++;
      if (combo > maxCombo) maxCombo = combo;
      points = Math.floor(points * (1 + (combo - 1) * 0.1)); // 10% bonus per combo level
      score += points;
      
      statusText = `✅ +${points} pts! ${reactionTime}ms (${combo}x combo)`;
    } else {
      statusText = `✅ Correct! ${reactionTime} ms`;
    }
    
    sessionResults.push({round, reactionTime, status:"Correct", points: points || 0});
    
    if(reactionTime<highScore){
      highScore = reactionTime;
      confetti({particleCount:100, spread:70, origin:{y:0.6}});
      if (gameMode !== "time_attack") {
        statusText += ` 🎉 NEW RECORD!`;
      }
    }
  } else {
    // Wrong button
    if (gameMode === "time_attack") {
      combo = 0; // Reset combo
      statusText = `❌ Wrong! Combo broken! (needed ${targetButton})`;
    } else {
      statusText = `❌ Wrong! Pressed ${button}, needed ${targetButton}`;
    }
    sessionResults.push({round, reactionTime:"-", status:"Wrong", points: 0});
  }

  document.getElementById("status").textContent = statusText;
  updateAttemptsTable();
  updateLiveMetrics();
  saveRecentAttempts();
  updateChart();
  miniCoach(sessionResults);
  clearGlow();
  targetButton = null;

  // Shorter delay for time attack to keep pace up
  const nextRoundDelay = gameMode === "time_attack" ? 500 : 
                        gameMode === "unlimited" ? 1000 : 2000;
  setTimeout(nextRound, nextRoundDelay);
}

// ===== Round Counter =====
function updateRoundCounter(){
  if (gameMode === "time_attack") {
    document.getElementById("round-counter").textContent = `Reactions: ${sessionResults.length} | Max Combo: ${maxCombo}x`;
  } else {
    const maxRoundsText = gameMode === "unlimited" ? "∞" : maxRounds;
    document.getElementById("round-counter").textContent = `Round ${round} of ${maxRoundsText}`;
  }
}

// ===== Update Attempts Table =====
function updateAttemptsTable(){
  const tbody = document.querySelector("#attempts-table tbody");
  if (!tbody) return; // Safety check
  
  tbody.innerHTML="";
  sessionResults.forEach(r=>{
    const tr=document.createElement("tr");
    const pointsDisplay = r.points !== undefined ? r.points : "-";
    tr.innerHTML=`<td>${r.round}</td><td>${r.reactionTime}</td><td>${r.status}</td><td>${pointsDisplay}</td>`;
    tbody.appendChild(tr);
  });
}

// ===== Highscore =====
function updateHighScore(){
  const times = sessionResults.filter(r=>r.reactionTime!=="-").map(r=>r.reactionTime);
  if(times.length) {
    highScore = Math.min(...times);
    updateLiveMetrics();
  }
}

// ===== Save Attempts =====
function saveRecentAttempts(){
  const last20 = sessionResults.slice(-20);
  localStorage.setItem("reactionGameAttempts", JSON.stringify(last20));
}

// ===== Clear Glow =====
function clearGlow(){
  document.querySelectorAll(".game-button").forEach(btn=>btn.classList.remove("glow"));
}

// ===== End Game (for non-time-attack modes) =====
function endGame(){
  let times = sessionResults.filter(r=>r.reactionTime!=="-").map(r=>r.reactionTime);
  const avg = times.length ? (times.reduce((a,b)=>a+b,0)/times.length).toFixed(0) : "-";
  const accuracy = ((times.length / sessionResults.length) * 100).toFixed(1);
  
  document.getElementById("status").textContent = `🏁 Game Complete!`;
  document.getElementById("countdown").textContent = `Average: ${avg}ms | Accuracy: ${accuracy}%`;
  
  // Final coach message
  if (times.length > 0) {
    const bestTime = Math.min(...times);
    const message = bestTime < 300 ? 
      "🚀 Outstanding reflexes! You're in the top tier!" :
      bestTime < 400 ? 
      "🎯 Great performance! Keep practicing!" :
      "💪 Good work! Regular practice will improve your times!";
    document.getElementById("coachBox").textContent = message;
  }
}

// ===== Keyboard Input =====
document.addEventListener("keydown",(e)=>{
  if(["1","2","3"].includes(e.key)){
    handleButtonPress(parseInt(e.key));
  }
});