import lgpio
import time

CHIP = 0
BUTTON1 = 18
BUTTON2 = 19

# Open the GPIO chip
h = lgpio.gpiochip_open(CHIP)

# Claim pins as inputs with pull-up resistors
lgpio.gpio_claim_input(h, BUTTON1, lgpio.SET_PULL_UP)
lgpio.gpio_claim_input(h, BUTTON2, lgpio.SET_PULL_UP)

print("Press Button 1 (GPIO 18) or Button 2 (GPIO 19)...")

try:
    while True:
        if lgpio.gpio_read(h, BUTTON1) == 0:  # Active LOW
            print("Button 1 pressed!")
            time.sleep(0.3)

        if lgpio.gpio_read(h, BUTTON2) == 0:  # Active LOW
            print("Button 2 pressed!")
            time.sleep(0.3)

except KeyboardInterrupt:
    pass
finally:
    lgpio.gpiochip_close(h)