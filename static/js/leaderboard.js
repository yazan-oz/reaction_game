// ===== Leaderboard Module =====
const Leaderboard = {
  
  // Get all scores from SERVER
  async getAllScores(gameMode, limit = 100) {
    try {
      const response = await fetch(`/api/leaderboard?mode=${gameMode}&limit=${limit}`);
      const data = await response.json();
      return data.success ? data.scores : [];
    } catch (error) {
      console.error('Failed to fetch leaderboard:', error);
      return [];
    }
  },
  
  // Save a new score to SERVER
  async saveScore(playerName, score, gameMode, avgTime, accuracy, difficulty, maxCombo) {
    try {
      console.log('Saving score:', { playerName, score, gameMode, avgTime, accuracy });
      
      const response = await fetch('/api/leaderboard', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: playerName,
          score: score,
          gameMode: gameMode,
          difficulty: difficulty,
          maxCombo: maxCombo,
          avgTime: avgTime,
          accuracy: accuracy
        })
      });
      
      console.log('Response status:', response.status);
      const data = await response.json();
      console.log('Response data:', data);
      
      if (data.success) {
        return {
          ...data.entry,
          rank: data.rank,
          total: data.total
        };
      }
      
      console.error('Save failed:', data);
      return null;
    } catch (error) {
      console.error('Failed to save score:', error);
      return null;
    }
  },
  
  // Get top scores for a specific game mode
  async getTopScores(gameMode, limit = 10) {
    return await this.getAllScores(gameMode, limit);
  },
  
  // Prompt player to save their score
  // Prompt player to save their score
  async promptSaveScore(gameMode, finalScore, avgTime, accuracy, difficulty, maxCombo = 0) {
    const playerName = prompt("🏆 Great score! Enter your name for the leaderboard:");
    
    if (playerName && playerName.trim()) {
      const saved = await this.saveScore(
        playerName.trim(), 
        finalScore, 
        gameMode, 
        avgTime, 
        accuracy, 
        difficulty,
        maxCombo
      );
      
      if (saved && saved.rank) {
        await this.displayLeaderboard();
        
        // Show rank in chat
        if (typeof Chat !== 'undefined' && Chat.addMessage) {
          Chat.addMessage(`🎉 ${playerName} ranked #${saved.rank} out of ${saved.total} players!`, 'system');
        }
        
        return saved;
      } else {
        console.error('Failed to save score:', saved);
        alert('Failed to save score. Please try again.');
      }
    }
    
    return null;
  },
  
  // Save a new score to SERVER
  async saveScore(playerName, score, gameMode, avgTime, accuracy, difficulty, maxCombo = 0) {
    try {
      console.log('Saving score:', { 
        playerName, 
        score, 
        gameMode, 
        avgTime, 
        accuracy, 
        difficulty,  // ← Check this value!
        maxCombo 
      });
      
      const response = await fetch('/api/leaderboard', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: playerName,
          score: score,
          gameMode: gameMode,
          difficulty: difficulty,  // ← Must be sent!
          maxCombo: maxCombo,
          avgTime: avgTime,
          accuracy: accuracy
        })
      });
      
      console.log('Response status:', response.status);
      const data = await response.json();
      console.log('Response data:', data);
      
      if (data.success) {
        return {
          ...data.entry,
          rank: data.rank,
          total: data.total
        };
      }
      
      console.error('Save failed:', data);
      return null;
    } catch (error) {
      console.error('Failed to save score:', error);
      return null;
    }
  },
  
  // Display leaderboard in the UI
  // Display leaderboard in the UI
  async displayLeaderboard() {
    const container = document.getElementById('leaderboard-container');
    if (!container) return;
    
    const currentMode = document.getElementById("mode") ? document.getElementById("mode").value : "time_attack";
    const topScores = await this.getTopScores(currentMode, 10);
    
    if (topScores.length === 0) {
      container.innerHTML = '<p style="text-align:center; color:#888;">No scores yet. Be the first!</p>';
      return;
    }
    
    let html = '<table style="width:100%; margin-top:10px;">';
    html += '<thead><tr>';
    html += '<th style="width:40px;">Rank</th>';
    html += '<th>Player</th>';
    
    if (currentMode === "time_attack") {
      html += '<th>Score</th>';
      html += '<th>Combo</th>';
    } else {
      html += '<th>Avg Time</th>';
      html += '<th>Accuracy</th>';
    }
    
    html += '<th>Date</th>';
    html += '</tr></thead><tbody>';
    
    topScores.forEach((entry, index) => {
      const date = new Date(entry.date);
      const dateStr = date.toLocaleDateString();
      const rank = index + 1;
      
      let rankEmoji = '';
      if (rank === 1) rankEmoji = '🥇';
      else if (rank === 2) rankEmoji = '🥈';
      else if (rank === 3) rankEmoji = '🥉';
      
      // Check if this is a Hell mode entry
      const isHellMode = entry.difficulty === 'hell';
      const hellClass = isHellMode ? ' class="hell-survivor"' : '';
      const hellBadge = isHellMode ? ' 🔥' : '';
      
      html += `<tr${hellClass}>`;
      html += `<td style="text-align:center;">${rankEmoji} ${rank}</td>`;
      html += `<td>${entry.name}${hellBadge}</td>`;
      
      if (currentMode === "time_attack") {
        html += `<td>${entry.score} pts</td>`;
        html += `<td>${entry.maxCombo || 0}x</td>`; // This should be maxCombo, not accuracy
      } else {
        html += `<td>${entry.avgTime}ms</td>`;
        html += `<td>${entry.accuracy}%</td>`;
      }
      
      html += `<td style="font-size:12px; color:#888;">${dateStr}</td>`;
      html += '</tr>';
    });
    
    html += '</tbody></table>';
    container.innerHTML = html;
  },
  
  // Clear all leaderboard data
  async clearLeaderboard() {
    if (confirm("Are you sure you want to clear the GLOBAL leaderboard? This affects all players!")) {
      try {
        const response = await fetch('/api/leaderboard/clear', {
          method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
          await this.displayLeaderboard();
          
          if (typeof Chat !== 'undefined' && Chat.addMessage) {
            Chat.addMessage('Leaderboard cleared!', 'system');
          }
        }
      } catch (error) {
        console.error('Failed to clear leaderboard:', error);
        alert('Failed to clear leaderboard');
      }
    }
  }
};

// Make Leaderboard globally accessible
window.Leaderboard = Leaderboard;