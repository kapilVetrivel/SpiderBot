import time
import argparse
from pylx16a.lx16a import LX16A, ServoTimeoutError, ServoError

def main(serial_port, pos1, pos2, move_time):
    LX16A.initialize(serial_port)
    
    # Initialize once
    servos = [None] + [LX16A(i) for i in range(1, 9)]
    
    # Health check example
    try:
        for servo in servos[1:]:
            vin = servo.get_vin()
            temp = servo.get_temp()
            if temp > 80 or vin < 6000:
                raise RuntimeError(f"Servo {servo.id_}: bad temp {temp}°C or vin {vin}mV")
    except ServoError as e:
        print(f"Servo {e.id_} health check failed: {e}")
        return
    
    def move_servos(pos, time_ms):
        try:
            for i, servo in enumerate(servos[1:], 1):
                servo.move(pos[i], time_ms, wait=True)  # Buffer moves
            for servo in servos[1:]:
                servo.move_start()  # Sync start
            time.sleep(time_ms / 1000.0)  # Wait for duration
        except ServoError as e:
            print(f"Move failed on servo {e.id_}: {e}")
    
    move_servos(pos1, move_time)
    move_servos(pos2, move_time)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="/dev/ttyUSB0")
    parser.add_argument("--time", type=int, default=1000)
    args = parser.parse_args()
    
    pos1 = [None, 70, 80, 176, 83, 172, 78, 67, 76]
    pos2 = [None, 70, 6, 176, 8.5, 172, 5.4, 67, 5.2]
    
    main(args.port, pos1, pos2, args.time)
