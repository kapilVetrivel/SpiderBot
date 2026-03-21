import os, time
from pylx16a.lx16a import *
import serial.tools.list_ports

os.system("clear")

LX16A.initialize("/dev/ttyUSB0", 0.1)
servo_id = 3
target_angle = 120

min_angle = 0
max_angle = 240

try:
    servo = LX16A(servo_id)

    servo.set_angle_limits(min_angle, max_angle)
    print(f"Servo angle limits set to {min_angle} - {max_angle} degrees")

    

    initial_angle = servo.get_physical_angle() # Read current position to ensure communication is working
    print(f"Initial servo position: {initial_angle} degrees")

    offset = -1*round(target_angle - initial_angle,1)
    print(f"Calculated offset: {offset} degrees")

    if abs(offset) > .24:
        servo.set_angle_offset(offset, permanent=False)
        print(f"Angle offset of {offset} degrees applied permanently to Servo {servo_id}.")

    updated_angle = servo.get_physical_angle() # Read current position to ensure communication is working
    print(f"Updated servo position: {updated_angle} degrees")

    servo.move(target_angle)
    print(f"Moving Servo {servo_id} to target angle: {target_angle} degrees")
    time.sleep(1) # Wait for the servo to reach the target position

    servo.disable_torque() # Disable torque to allow manual movement



except ServoTimeoutError as e:
    print(f"Servo {e.id_} is not responding. Exiting...")
    quit()
