import RPi.GPIO as GPIO
import time
from RPLCD.i2c import CharLCD
from gpiozero import Servo

# === GPIO Pin Setup ===
PIR_PIN = 17          # PIR Motion Sensor
BUZZER_PIN = 27       # Buzzer
SERVO_PIN = 18        # Servo Motor
LCD_ADDRESS = 0x27    # I2C LCD Address

# === GPIO and Device Initialization ===
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIR_PIN, GPIO.IN)
GPIO.setup(BUZZER_PIN, GPIO.OUT)
lcd = CharLCD('PCF8574', LCD_ADDRESS)
servo = Servo(SERVO_PIN)

def unlock_door():
    servo.max()
    time.sleep(2)
    servo.min()

def alert_intruder():
    GPIO.output(BUZZER_PIN, GPIO.HIGH)
    time.sleep(1)
    GPIO.output(BUZZER_PIN, GPIO.LOW)


# === Main Loop ===
try:
    while True:
        if GPIO.input(PIR_PIN):
            print("Motion Detected")
            lcd.clear()
            lcd.write_string("Motion Detected")


            # Ask for user input: 1 for known, 0 for stranger
            user_input = input("Enter 1 if known, 0 if stranger: ").strip()
            if user_input == '1':
                print("Known person - Access Granted")
                lcd.clear()
                lcd.write_string("Welcome! Access")
                unlock_door()
            elif user_input == '0':
                print("Stranger Detected")
                lcd.clear()
                lcd.write_string("Stranger Alert!")
                alert_intruder()
            else:
                print("Invalid input. Skipping...")

            time.sleep(5)  # Debounce time after detection

        time.sleep(0.1)

except KeyboardInterrupt:
    print("Program Terminated")

finally:
    GPIO.cleanup()
    lcd.close(clear=True)