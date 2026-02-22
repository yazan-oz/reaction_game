// ===== Hardware Integration Module =====
const Hardware = {
  
  gameStatePolling: null,
  lastKnownState: null,

  init() {
    console.log('Physical button integration ready');
    this.startPolling();
    this.setupGameSyncHook();
  },

  // Global function for syncing JavaScript game state with Flask
  syncFlaskRound: async function(targetButton) {
    try {
      console.log(`Syncing Flask: target button ${targetButton}`);
      
      const response = await fetch('/api/start_round', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_button: targetButton })
      });
      
      if (response.ok) {
        console.log('Flask round synced successfully');
      } else {
        console.log('Flask sync failed:', response.status);
      }
    } catch (error) {
      console.log('Flask sync error:', error);
    }
  },

  startPolling() {
    if (this.gameStatePolling) return;
    
    this.gameStatePolling = setInterval(async () => {
      try {
        const response = await fetch('/api/status');
        const gameState = await response.json();
        
        // Update hardware status indicator
        this.updateHardwareStatus(gameState);
        
        // Check if Flask processed a hardware button press
        if (gameState.waiting_for_press === false && 
            gameState.last_message && 
            (gameState.last_message.includes('Correct!') || gameState.last_message.includes('Wrong'))) {
          
          // If this is a new result, trigger JavaScript button handler
          if (JSON.stringify(gameState) !== JSON.stringify(this.lastKnownState)) {
            console.log('Hardware button result detected:', gameState.last_message);
            
            // Extract which button was pressed from Flask result
            let buttonPressed = null;
            if (gameState.last_message.includes('Expected 1')) {
              buttonPressed = 2; // Wrong button
            } else if (gameState.last_message.includes('Expected 2')) {
              buttonPressed = 1; // Wrong button
            } else if (gameState.current_button) {
              buttonPressed = gameState.current_button; // Correct button
            }
            
            // Call JavaScript game logic
            if (buttonPressed && typeof handleButtonPress === 'function') {
              console.log(`Bridging hardware button ${buttonPressed} to JavaScript game`);
              handleButtonPress(buttonPressed);
            }
          }
        }
        
        this.lastKnownState = {...gameState};
        
      } catch (error) {
        // Silently ignore polling errors
      }
    }, 200);
  },

  updateHardwareStatus(gameState) {
    const indicator = document.getElementById('hardware-indicator');
    const statusBox = document.getElementById('hardware-status');
    
    if (!indicator || !statusBox) return;
    
    if (gameState.hardware_available) {
      indicator.textContent = 'Connected ✅';
      statusBox.classList.remove('disconnected');
    } else {
      indicator.textContent = 'Disconnected ❌';
      statusBox.classList.add('disconnected');
    }
  },

  setupGameSyncHook() {
    // Monitor DOM for button glow changes to detect when round starts
    const button1 = document.getElementById('button1');
    const button2 = document.getElementById('button2');
    
    if (button1 && button2) {
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
            const target = mutation.target;
            
            // Check if a button just started glowing
            if (target.classList.contains('glow')) {
              let targetButton = null;
              if (target.id === 'button1') targetButton = 1;
              if (target.id === 'button2') targetButton = 2;
              
              if (targetButton) {
                console.log(`Button ${targetButton} started glowing - syncing with Flask`);
                this.syncFlaskRound(targetButton);
              }
            }
          }
        });
      });
      
      // Start observing both buttons for class changes
      observer.observe(button1, { attributes: true, attributeFilter: ['class'] });
      observer.observe(button2, { attributes: true, attributeFilter: ['class'] });
      
      console.log('DOM-based sync detection active - watching for button glow');
    } else {
      console.log('Could not find buttons for DOM monitoring');
    }
  },

  cleanup() {
    if (this.gameStatePolling) {
      clearInterval(this.gameStatePolling);
      this.gameStatePolling = null;
    }
  }
};

// Make syncFlaskRound globally accessible for template compatibility
window.syncFlaskRound = Hardware.syncFlaskRound;