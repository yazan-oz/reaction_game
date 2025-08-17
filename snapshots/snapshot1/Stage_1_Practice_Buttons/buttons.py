# Simple button press simulation
button_pressed = False

def press_button():
    global button_pressed
    button_pressed = True
    print("Button pressed!")

# Simulate button press
press_button()

if button_pressed:
    print("Button state detected correctly.")