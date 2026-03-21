import time
import serial
from pylx16a.lx16a import LX16A, ServoTimeoutError

PORT = "/dev/ttyUSB0"   # or "COMx"
update_frequency = 1/2  # seconds between updates

def connect():
    LX16A.initialize(PORT)
    print("Connected to LX-16A servo controller on port", PORT)
    LX16A.set_timeout(0.15)  # faster detection of a missing servo/bus issues

connect()

while True:
    try:
        servo = LX16A(2)
        # print("getting servo angle...")
        angle = servo.get_physical_angle()          # any command can timeout if the servo disappears
        print(f"Servo angle: {angle}")
        time.sleep(update_frequency)

    except ServoTimeoutError as e:
        # Servo e.id_ not responding; treat as disconnected and attempt recovery
        print(f"Servo {e.id_} disconnected; retrying...")
        time.sleep(update_frequency)
        connect()
        # servo = LX16A(2)         # re-create objects after reconnect

    except (serial.SerialException, OSError) as e:
        # USB serial adapter/port failure; reconnect similarly
        print(f"Serial error: {e}; retrying...")
        time.sleep(update_frequency)
        connect()
        # servo = LX16A(2)
