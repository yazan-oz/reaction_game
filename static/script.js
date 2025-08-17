// ===== Game State =====
let gameMode = "classic";
let difficulty = "easy";
let targetButton = null;
let startTime = null;
let round = 0;
let maxRounds = 5;
let highScore = Infinity;

// ===== Session Storage =====
let sessionResults = [];

// ===== Settings by Difficulty =====
const difficultySettings = {
  easy: { minDelay:2000, maxDelay:4000 },
  medium: { minDelay:1000, maxDelay:3000 },
  hard: { minDelay:500, maxDelay:2000 }
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
          label: 'Correct Presses',
          data: [],
          borderColor: '#3498db',
          backgroundColor: 'rgba(52, 152, 219, 0.2)',
          tension: 0.2,
          fill: true
        }
      ]
    },
    options: { responsive: true, scales: { y: { beginAtZero:true } } }
  });
}

function updateChart() {
  if (!reactionChart) return;
  const times = sessionResults.filter(r => r.reactionTime !== "-");
  reactionChart.data.labels = sessionResults.map(r => `R${r.round}`);
  reactionChart.data.datasets[0].data = sessionResults.map(r => r.reactionTime === "-" ? null : r.reactionTime);
  reactionChart.data.datasets[1].data = sessionResults.map(r => r.status==="Correct"?1:0);
  reactionChart.update();
}

// ===== Initialize =====
window.addEventListener("DOMContentLoaded", () => {
  const stored = JSON.parse(localStorage.getItem("reactionGameAttempts")||"[]");
  if(stored.length){
    sessionResults = stored.slice(-20);
    updateAttemptsTable();
    updateHighScore();
  }
  initChart();
  updateChart();
});

// ===== Start Game =====
function startGame(){
  gameMode = document.getElementById("mode").value;
  difficulty = document.getElementById("difficulty").value;
  round = 0;
  targetButton = null;
  sessionResults = sessionResults.slice(-20);
  document.querySelector("#attempts-table tbody").innerHTML = "";
  document.getElementById("results").innerHTML = "";
  document.getElementById("status").textContent = "Game started!";
  updateRoundCounter();
  nextRound();
}

// ===== Next Round =====
function nextRound(){
  clearGlow();
  round++;
  updateRoundCounter();

  if((gameMode==="classic"||gameMode==="endurance") && round>maxRounds){
    endGame();
    return;
  }

  document.getElementById("status").textContent = "Get ready...";
  const {minDelay,maxDelay} = difficultySettings[difficulty];
  const delay = Math.floor(Math.random()*(maxDelay-minDelay+1))+minDelay;

  setTimeout(()=>{
    targetButton = Math.floor(Math.random()*3)+1;
    document.getElementById(`button${targetButton}`).classList.add("glow");
    document.getElementById("status").textContent = `Press Button ${targetButton}! (or press ${targetButton})`;
    startTime = Date.now();
  }, delay);
}

// ===== Handle Button Press =====
function handleButtonPress(button){
  if(!targetButton) return;

  let reactionTime = Date.now() - startTime;
  let statusText="";
  if(button===targetButton){
    statusText = `✅ Correct! Time: ${reactionTime} ms`;
    sessionResults.push({round, reactionTime, status:"Correct"});
    if(reactionTime<highScore){
      highScore = reactionTime;
      confetti({particleCount:100, spread:70, origin:{y:0.6}});
    }
  } else {
    statusText = `❌ Wrong! Pressed ${button}, needed ${targetButton}`;
    sessionResults.push({round, reactionTime:"-", status:"Wrong"});
  }

  document.getElementById("status").textContent = statusText;
  updateAttemptsTable();
  saveRecentAttempts();
  updateChart();
  miniCoach(sessionResults); // ← Call mini AI Coach
  clearGlow();
  targetButton = null;

  setTimeout(nextRound, gameMode==="unlimited"?1000:1500);
}

// ===== Round Counter =====
function updateRoundCounter(){
  document.getElementById("round-counter").textContent = `Round ${round} of ${maxRounds}`;
}

// ===== Update Attempts Table =====
function updateAttemptsTable(){
  const tbody = document.querySelector("#attempts-table tbody");
  tbody.innerHTML="";
  sessionResults.forEach(r=>{
    const tr=document.createElement("tr");
    tr.innerHTML=`<td>${r.round}</td><td>${r.reactionTime}</td><td>${r.status}</td>`;
    tbody.appendChild(tr);
  });
}

// ===== Highscore =====
function updateHighScore(){
  const times = sessionResults.filter(r=>r.reactionTime!=="-").map(r=>r.reactionTime);
  if(times.length) highScore = Math.min(...times);
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

// ===== End Game =====
function endGame(){
  let times = sessionResults.filter(r=>r.reactionTime!=="-").map(r=>r.reactionTime);
  const avg = times.length ? (times.reduce((a,b)=>a+b,0)/times.length).toFixed(2) : "-";
  document.getElementById("status").textContent = `Game Over! Average: ${avg} ms`;
}

// ===== Keyboard Input =====
document.addEventListener("keydown",(e)=>{
  if(["1","2","3"].includes(e.key)){
    handleButtonPress(parseInt(e.key));
  }
});
