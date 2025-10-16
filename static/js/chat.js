// ===== Chat Sidebar Module =====
const Chat = {
  
  addMessage(text, type = 'system') {
    const chatContainer = document.getElementById('chat-messages');
    if (!chatContainer) {
      console.error('Chat container not found!');
      return;
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${type}`;
    
    const time = new Date().toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit'
    });
    
    messageDiv.innerHTML = `
      <div>${text}</div>
      <div class="message-time">${time}</div>
    `;
    
    chatContainer.appendChild(messageDiv);
    
    // Auto-scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    console.log(`Chat message added: ${type} - ${text}`);
  },
  
  logGameStart(mode, difficulty) {
    const modeNames = {
      'time_attack': '⚡ Time Attack',
      'unlimited': '♾️ Unlimited',
      'endurance': '💪 Endurance'
    };
    
    const difficultyNames = {
      'easy': '😊 Easy',
      'medium': '😐 Medium',
      'hard': '😤 Hard'
    };
    
    this.addMessage(
      `Started ${modeNames[mode]} mode on ${difficultyNames[difficulty]} difficulty!`,
      'user'
    );
  },
  
  logRoundResult(round, reactionTime, status, points) {
    let resultText = '';
    let messageType = 'result';
    
    if (status === 'Correct') {
      if (points > 0) {
        resultText = `Round ${round}: ✅ ${reactionTime}ms (+${points} pts)`;
      } else {
        resultText = `Round ${round}: ✅ Correct in ${reactionTime}ms`;
      }
    } else {
      resultText = `Round ${round}: ❌ Wrong button pressed`;
      messageType = 'result wrong';
    }
    
    this.addMessage(resultText, messageType);
  },
  
  logAIFeedback(feedback) {
    if (!feedback) return;
    this.addMessage(feedback, 'ai');
  },
  
  logGameEnd(finalStats) {
    this.addMessage(finalStats, 'system');
  },
  
  clearChat() {
    const chatContainer = document.getElementById('chat-messages');
    if (!chatContainer) return;
    
    chatContainer.innerHTML = `
      <div class="chat-message system">
        <div>Welcome to Reaction Time Trainer! 👋</div>
        <div class="message-time">Ready to start</div>
      </div>
    `;
  }
};

// Make Chat globally accessible
window.Chat = Chat;