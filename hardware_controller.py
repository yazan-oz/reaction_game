import threading
import time
import lgpio

HARDWARE_ENABLED = True

class HardwareController:
    BUTTON_1_PIN = 18  # Keep your original pin
    BUTTON_2_PIN = 19  # Keep your original pin

    def __init__(self):
        self.pi = None
        self.button1_callback = None
        self.button2_callback = None
        self.running = False

        if HARDWARE_ENABLED:
            self.setup_gpio()
            print("Hardware controller loaded successfully!")
        else:
            print("Running in software mode (no hardware)")

    def setup_gpio(self):
        self.pi = lgpio.gpiochip_open(0)
        lgpio.gpio_claim_input(self.pi, self.BUTTON_1_PIN)
        lgpio.gpio_claim_input(self.pi, self.BUTTON_2_PIN)

        self.running = True
        self.poll_thread = threading.Thread(target=self.poll_buttons, daemon=True)
        self.poll_thread.start()

    def poll_buttons(self):
        while self.running:
            if lgpio.gpio_read(self.pi, self.BUTTON_1_PIN) == 0:  # Pressed
                if self.button1_callback:
                    self.button1_callback()
                time.sleep(0.2)
            if lgpio.gpio_read(self.pi, self.BUTTON_2_PIN) == 0:  # Pressed
                if self.button2_callback:
                    self.button2_callback()
                time.sleep(0.2)
            time.sleep(0.01)

    def on_button1(self, callback):
        self.button1_callback = callback

    def on_button2(self, callback):
        self.button2_callback = callback

    def cleanup(self):
        self.running = False
        if self.pi:
            lgpio.gpio_claim_input(self.pi, self.BUTTON_1_PIN)
            lgpio.gpio_claim_input(self.pi, self.BUTTON_2_PIN)
        print("GPIO cleaned up successfully.")