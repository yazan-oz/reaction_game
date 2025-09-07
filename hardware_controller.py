import threading
import time
import sys
import os

# Diagnostic logging function
def log_diagnostic(message, error=None):
    """Log diagnostic information with timestamp"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] HARDWARE DIAGNOSTIC: {message}")
    if error:
        print(f"[{timestamp}] ERROR DETAILS: {str(error)}")
        print(f"[{timestamp}] ERROR TYPE: {type(error).__name__}")

class HardwareController:
    BUTTON_1_PIN = 18
    BUTTON_2_PIN = 19
    
    def __init__(self):
        self.pi = None
        self.button_callbacks = {}
        self.running = False
        self.poll_thread = None
        self.hardware_available = False
        
        log_diagnostic("Initializing HardwareController...")
        self._check_system_requirements()
        
        if self._initialize_gpio():
            self.hardware_available = True
            log_diagnostic("Hardware controller initialized successfully!")
        else:
            log_diagnostic("Hardware controller failed to initialize - running in software mode")
    
    def _check_system_requirements(self):
        """Check system requirements and log diagnostic info"""
        log_diagnostic(f"Python version: {sys.version}")
        log_diagnostic(f"Platform: {sys.platform}")
        
        # Check if we're running on Raspberry Pi
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                if 'BCM' in cpuinfo:
                    log_diagnostic("Running on Raspberry Pi - GPIO should be available")
                else:
                    log_diagnostic("WARNING: Not running on Raspberry Pi - GPIO may not work")
        except Exception as e:
            log_diagnostic("Could not read /proc/cpuinfo", e)
        
        # Check lgpio availability
        try:
            import lgpio
            log_diagnostic(f"lgpio library found - version info: {lgpio}")
        except ImportError as e:
            log_diagnostic("lgpio library not found - install with: sudo apt install python3-lgpio", e)
            return False
        
        # Check permissions
        try:
            # Test if we can access GPIO device files
            gpio_devices = ['/dev/gpiochip0', '/dev/gpiomem']
            for device in gpio_devices:
                if os.path.exists(device):
                    log_diagnostic(f"GPIO device found: {device}")
                    # Test read access
                    try:
                        with open(device, 'rb') as f:
                            log_diagnostic(f"Can read {device} - permissions OK")
                    except PermissionError:
                        log_diagnostic(f"Permission denied reading {device} - try: sudo usermod -a -G gpio $USER")
                else:
                    log_diagnostic(f"GPIO device not found: {device}")
        except Exception as e:
            log_diagnostic("Error checking GPIO device permissions", e)
        
        return True
    
    def _initialize_gpio(self):
        """Initialize GPIO with detailed error reporting"""
        try:
            import lgpio
            log_diagnostic("Attempting to open GPIO chip...")
            
            # Try to open the GPIO chip
            self.pi = lgpio.gpiochip_open(0)
            log_diagnostic(f"GPIO chip opened successfully - handle: {self.pi}")
            
            # Configure button pins as inputs with pull-up resistors
            log_diagnostic(f"Configuring pin {self.BUTTON_1_PIN} as input...")
            lgpio.gpio_claim_input(self.pi, self.BUTTON_1_PIN, lgpio.SET_PULL_UP)
            
            log_diagnostic(f"Configuring pin {self.BUTTON_2_PIN} as input...")
            lgpio.gpio_claim_input(self.pi, self.BUTTON_2_PIN, lgpio.SET_PULL_UP)
            
            # Test reading the pins
            btn1_state = lgpio.gpio_read(self.pi, self.BUTTON_1_PIN)
            btn2_state = lgpio.gpio_read(self.pi, self.BUTTON_2_PIN)
            log_diagnostic(f"Initial pin states - Button 1: {btn1_state}, Button 2: {btn2_state}")
            
            # Start polling thread
            self.running = True
            self.poll_thread = threading.Thread(target=self._poll_buttons, daemon=True)
            self.poll_thread.start()
            log_diagnostic("Button polling thread started")
            
            return True
            
        except ImportError as e:
            log_diagnostic("Failed to import lgpio library", e)
            log_diagnostic("Install with: sudo apt update && sudo apt install python3-lgpio")
            return False
        except Exception as e:
            log_diagnostic("Failed to initialize GPIO", e)
            if "GPIO busy" in str(e) or "busy" in str(e):
                log_diagnostic("GPIO pins are busy (already claimed). This usually happens because:")
                log_diagnostic("1. Flask debug mode restarted the app")
                log_diagnostic("2. Previous run didn't clean up properly")
                log_diagnostic("3. Another program is using the GPIO pins")
                log_diagnostic("Solutions:")
                log_diagnostic("- Restart without debug mode: python3 app.py --no-debug")
                log_diagnostic("- Or wait a moment and try again")
                log_diagnostic("- Or use: sudo systemctl restart systemd-modules-load")
            elif "Permission denied" in str(e):
                log_diagnostic("Permission issue detected. Try:")
                log_diagnostic("1. sudo usermod -a -G gpio $USER")
                log_diagnostic("2. Log out and log back in")
                log_diagnostic("3. Or run with sudo (not recommended)")
            elif "No such device" in str(e):
                log_diagnostic("GPIO device not found. Make sure:")
                log_diagnostic("1. You're running on a Raspberry Pi")
                log_diagnostic("2. GPIO is enabled in raspi-config")
            return False
    
    def _poll_buttons(self):
        """Poll buttons in background thread"""
        import lgpio
        last_button1_state = 1  # Assuming pull-up (1 = not pressed)
        last_button2_state = 1
        button1_press_count = 0
        button2_press_count = 0
        poll_count = 0
        
        log_diagnostic("Button polling started - will log first 10 seconds of activity")
        
        while self.running:
            try:
                # Read current button states
                current_button1 = lgpio.gpio_read(self.pi, self.BUTTON_1_PIN)
                current_button2 = lgpio.gpio_read(self.pi, self.BUTTON_2_PIN)
                
                # Log pin states periodically for first 10 seconds
                poll_count += 1
                if poll_count % 1000 == 0 and poll_count <= 10000:  # Every second for first 10 seconds
                    log_diagnostic(f"Pin states - Pin {self.BUTTON_1_PIN}: {current_button1}, Pin {self.BUTTON_2_PIN}: {current_button2}")
                
                # Detect any state changes (not just presses)
                if current_button1 != last_button1_state:
                    log_diagnostic(f"Button 1 state change: {last_button1_state} -> {current_button1}")
                    if current_button1 == 0:  # Press detected (high to low)
                        button1_press_count += 1
                        log_diagnostic(f"Button 1 PRESSED (#{button1_press_count})")
                        if 1 in self.button_callbacks:
                            self.button_callbacks[1]()
                    else:  # Release detected (low to high)
                        log_diagnostic("Button 1 released")
                
                if current_button2 != last_button2_state:
                    log_diagnostic(f"Button 2 state change: {last_button2_state} -> {current_button2}")
                    if current_button2 == 0:  # Press detected (high to low)
                        button2_press_count += 1
                        log_diagnostic(f"Button 2 PRESSED (#{button2_press_count})")
                        if 2 in self.button_callbacks:
                            self.button_callbacks[2]()
                    else:  # Release detected (low to high)
                        log_diagnostic("Button 2 released")
                
                last_button1_state = current_button1
                last_button2_state = current_button2
                
                time.sleep(0.01)  # 10ms polling interval
                
            except Exception as e:
                log_diagnostic("Error in button polling", e)
                break
        
        log_diagnostic("Button polling stopped")
    
    def set_button_callback(self, button_id, callback):
        """Set callback function for button press"""
        self.button_callbacks[button_id] = callback
        log_diagnostic(f"Callback set for button {button_id}")
    
    def is_available(self):
        """Check if hardware is available"""
        return self.hardware_available
    
    # Motor control methods (placeholder implementations)
    def set_motor_position(self, position):
        """Set stepper motor position"""
        log_diagnostic(f"Motor position set to {position} (placeholder)")
        # TODO: Implement actual stepper motor control
    
    def performance_meter_update(self, reaction_time):
        """Update performance meter based on reaction time"""
        log_diagnostic(f"Performance meter updated: {reaction_time}ms (placeholder)")
        # TODO: Implement actual performance meter
    
    def tension_build_animation(self, duration):
        """Run tension building animation"""
        log_diagnostic(f"Starting tension animation for {duration} seconds")
        time.sleep(duration)  # Simple delay for now
        log_diagnostic("Tension animation complete")
    
    def snap_back(self):
        """Snap motor back to zero position"""
        log_diagnostic("Motor snap back (placeholder)")
        self.set_motor_position(0)
    
    def cleanup(self):
        """Cleanup GPIO resources"""
        log_diagnostic("Cleaning up hardware controller...")
        self.running = False
        
        if self.poll_thread and self.poll_thread.is_alive():
            log_diagnostic("Waiting for polling thread to stop...")
            self.poll_thread.join(timeout=1.0)
        
        if self.pi is not None:
            try:
                import lgpio
                lgpio.gpio_free(self.pi, self.BUTTON_1_PIN)
                lgpio.gpio_free(self.pi, self.BUTTON_2_PIN)
                lgpio.gpiochip_close(self.pi)
                log_diagnostic("GPIO resources cleaned up successfully")
            except Exception as e:
                log_diagnostic("Error during GPIO cleanup", e)
        
        self.pi = None
        log_diagnostic("Hardware controller cleanup complete")

# Create the hardware instance
try:
    hardware = HardwareController()
    if hardware.is_available():
        log_diagnostic("Hardware controller instance created and available")
    else:
        log_diagnostic("Hardware controller instance created but not available")
        hardware = None
except Exception as e:
    log_diagnostic("Failed to create hardware controller instance", e)
    hardware = None