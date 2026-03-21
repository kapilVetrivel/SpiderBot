import os, time
from pylx16a.lx16a import *
import serial.tools.list_ports

os.system("clear")

LX16A.initialize("/dev/ttyUSB0", 0.1)
servo_ids = [1,3,5,7,
             2,4,6,8] # List of servo IDs to check

min_angle = 0
max_angle = 240
step = 5
time_delay = 0.1

# get datetime stamp for file naming
timestamp = time.strftime("%Y%m%d-%H%M%S")

try:
    for servo_id in servo_ids:
        servo = LX16A(servo_id)

        min_angle = 0
        max_angle = 240
        step = 10
        time_delay = 0.5

        servo.set_angle_limits(min_angle, max_angle)
        print(f"Servo angle limits set to {min_angle} - {max_angle} degrees")

        initial_angle = servo.get_physical_angle() # Read current position to ensure communication is working
        print(f"Initial servo position: {initial_angle} degrees")


        # move servo step by step and find end positions: if the angle of the servo does not change after a move command, we have reached the end of the range. 
        # doing it in both directions will help us find the limits more accurately, as there may be some play in the gears that causes the servo to not respond to small angle changes near the limits.
        print("\nSweeping servo to find limits...")
        current_angle = initial_angle

        # find max angle

        while True:
            servo.move(min(current_angle + step, 240)) # Ensure we don't command the servo to move above 240 degrees
            time.sleep(time_delay) # Wait for the servo to move and stabilize

            new_angle = servo.get_physical_angle()
            print(f"Moved from {current_angle} to {new_angle} degrees")

            if new_angle == current_angle:
                print(f"Reached limit at {current_angle} degrees")
                max_angle = min(new_angle, 240)
                break
            current_angle = servo.get_physical_angle()


        # find min angle

        while True:
            servo.move(max(current_angle - step,0)) # Ensure we don't command the servo to move below 0 degrees
            time.sleep(time_delay) # Wait for the servo to move and stabilize

            new_angle = servo.get_physical_angle()
            print(f"Moved from {current_angle} to {new_angle} degrees")

            if new_angle == current_angle:
                print(f"Reached limit at {current_angle} degrees")
                min_angle = max(new_angle, 0)
                break
            current_angle = servo.get_physical_angle()

        # move to home target angle
        target_angle = round(min_angle + (max_angle - min_angle) / 2,1)
        servo.move(target_angle)
        print(f"\nMoving to target angle: {target_angle} degrees")
        time.sleep(1) # Wait for the servo to reach the target position

        servo.set_angle_limits(min_angle, max_angle)
        print(f"Servo angle limits set to {min_angle} - {max_angle} degrees")

        servo.disable_torque() # Disable torque to allow manual movement

        # record the all servo id, min, max angles, mid position in a file for future reference and save in folder of the python file.
        # file name is recorded against date time stamp to avoid overwriting previous records.
        with open(f"servo_limits_{timestamp}.txt", "a") as f:
            f.write(f"Servo ID: {servo_id}, Min Angle: {min_angle}, Max Angle: {max_angle}, Target Angle: {target_angle}\n")
            print(f"Servo limits saved to servo_limits_{timestamp}.txt")
        

    
        





except ServoTimeoutError as e:
    print(f"Servo {e.id_} is not responding. Exiting...")
    quit()
