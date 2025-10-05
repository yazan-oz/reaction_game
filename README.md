# 🎯 Reaction Time Trainer

A hardware-integrated web-based reaction time game built with Raspberry Pi, Flask, and JavaScript. Features physical button controls, real-time analytics, AI coaching, and multiple game modes.

## Features

### Game Modes
- **⚡ Time Attack** - Score as many points as possible within a time limit
- **♾️ Unlimited** - Endless practice mode 
- **💪 Endurance** - Complete 5 rounds for accuracy training

### Key Capabilities
- Physical button integration via Raspberry Pi GPIO
- Real-time performance metrics and analytics
- AI-powered coaching feedback
- Multiple difficulty levels
- Performance visualization with Chart.js
- Local storage for session history
- Responsive web interface
- Standalone kiosk mode on 3.5" LCD display

## Hardware Requirements

- Raspberry Pi 5 (or compatible model)
- 2x Physical buttons connected to GPIO pins 21 and 19
- Optional: 3.5" LCD display for standalone kiosk mode
- Pull-up resistors for buttons (or use internal pull-ups)

## Software Requirements

- Python 3.11+
- Flask
- lgpio library for GPIO control
- Modern web browser (Chrome/Chromium recommended)

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yazan-oz/reaction_game.git
cd reaction_game
```

### 2. Install Python Dependencies
```bash
pip3 install flask
# lgpio usually pre-installed on Raspberry Pi OS
```

### 3. Configure GPIO Pins
Edit `hardware_controller.py` if using different GPIO pins:
```python
BUTTON_1_PIN = 21  # Default GPIO pin for button 1
BUTTON_2_PIN = 19  # Default GPIO pin for button 2
```

### 4. Run the Application
```bash
python3 app.py --no-debug
```

The game will be accessible at:
- Local: `http://localhost:5000`
- Network: `http://[YOUR_PI_IP]:5000`
- Mobile optimized: `http://[YOUR_PI_IP]:5000/mobile`

## Project Structure

```
reaction_game/
├── app.py                          # Flask server and API routes
├── hardware_controller.py          # GPIO interface for physical buttons
├── static/
│   ├── css/
│   │   └── styles.css             # Styling
│   └── js/
│       ├── game-core.js           # Core game logic
│       ├── ui-updates.js          # DOM manipulation
│       ├── metrics.js             # Performance tracking
│       ├── charts.js              # Analytics visualization
│       ├── coach.js               # AI coaching system
│       └── hardware.js            # Physical button integration
└── templates/
    ├── template.html              # Main web interface
    └── mobile.html                # LCD-optimized interface
```

## Modular Architecture

The codebase uses a modular design pattern:
- **game-core.js** - Pure game mechanics and state management
- **ui-updates.js** - All DOM manipulation and visual updates
- **metrics.js** - Performance calculations and storage
- **charts.js** - Data visualization with Chart.js
- **coach.js** - AI feedback based on performance
- **hardware.js** - Bridge between GPIO buttons and game logic

This separation allows easy maintenance and feature additions.

## Hardware Integration

### GPIO Button Setup
1. Connect buttons between GPIO pins and ground
2. Internal pull-up resistors are enabled by default
3. Button press = LOW (0), Released = HIGH (1)

### How It Works
- Physical buttons detected via GPIO polling
- Hardware events bridge to JavaScript game logic
- Seamless integration with web interface
- Works alongside virtual button clicks and keyboard input

## Kiosk Mode (LCD Display)

### Setup for 3.5" LCD
1. Install LCD drivers (LCD-show for compatible displays)
2. Configure autostart:
```bash
mkdir -p ~/.config/autostart
nano ~/.config/autostart/kiosk.desktop
```
Add:
```
[Desktop Entry]
Type=Application
Name=Kiosk
Exec=/home/pi-5/start_kiosk.sh
```

3. Create kiosk script at `~/start_kiosk.sh`:
```bash
#!/bin/bash
sleep 15  # Wait for system boot
pkill -f "python3 app.py"
sleep 2

cd ~/reaction_game
python3 app.py --no-debug &
sleep 5

export DISPLAY=:0
chromium-browser --kiosk --incognito --force-device-scale-factor=0.67 http://localhost:5000/mobile &
```

4. Make executable: `chmod +x ~/start_kiosk.sh`

The Pi will now boot directly into the game on the LCD display.

## API Endpoints

- `GET /` - Main game interface
- `GET /mobile` - Mobile-optimized interface
- `POST /api/start_round` - Initialize new game round
- `GET /api/status` - Current game state
- `POST /api/buttons/<id>/press` - Virtual button press
- `GET /api/test_buttons` - Hardware diagnostic endpoint

## Troubleshooting

### GPIO "Busy" Error
If you see `GPIO busy` errors:
```bash
# Always run without debug mode
python3 app.py --no-debug
```
Debug mode causes Flask to restart, leaving GPIO pins claimed.

### Physical Buttons Not Working
1. Check GPIO pin numbers in `hardware_controller.py`
2. Verify button wiring (should connect to ground when pressed)
3. Test with: `http://localhost:5000/api/test_buttons`
4. Check Flask logs for hardware detection messages

### Kiosk Won't Start
1. Ensure 15-second delay at start of kiosk script
2. Check autostart file location: `~/.config/autostart/kiosk.desktop`
3. Verify graphical boot: `sudo systemctl set-default graphical.target`

## Performance Optimization

- Mobile interface removes CSS animations for better LCD performance
- Polling interval set to 200ms for responsive hardware detection
- Chart.js used for efficient data visualization
- LocalStorage for client-side session persistence

## Future Enhancements

- [ ] Multiplayer competitive mode
- [ ] Online leaderboards
- [ ] Sound effects and audio feedback
- [ ] Adaptive difficulty based on performance
- [ ] Data export for long-term tracking
- [ ] Network multiplayer

## Contributing

This is a personal learning project, but suggestions and improvements are welcome via issues or pull requests.

## License

MIT License - See LICENSE file for details

## Acknowledgments

- Built as a learning project exploring hardware-software integration
- Uses Chart.js for analytics visualization
- Hardware control via lgpio library
- LCD support through LCD-show drivers

## Author

**Yazan** - High school student exploring embedded systems and web development

---

**Note:** This project demonstrates integration of physical hardware with modern web technologies. The modular architecture allows it to work both as a standalone kiosk with physical buttons and as a network-accessible web application.
