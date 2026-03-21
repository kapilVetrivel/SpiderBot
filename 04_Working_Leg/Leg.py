import os, time
from pylx16a.lx16a import *
import serial.tools.list_ports

# Clear Console
os.system('cls' if os.name == 'nt' else 'clear')

print("#####################################################################")
print("######################## SPIDER BOT #################################")
print("#####################################################################\n")


def find_serial_ports():
    """
    Lists serial port names and provides details.
    """
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("No serial ports found.")
    else:
        print("Found serial ports.")
        for port in ports:
            print(f"* {port.device}: {port.description} [{port.hwid}]")
            # You can add logic here to filter or select specific ports
        return ports

print("Searching for serial ports...")

if __name__ == '__main__':

    ## Search for serial ports and select the appropriate one
    ports = find_serial_ports()
    selected_port = None
    for port in ports:
        if "ttyUSB" in port.device:
            selected_port = port.device
            print(f"Selected Port : {selected_port}\n")
    if not selected_port:
        print("No suitable serial port found. Please connect your device and try again.")
        print("Exiting program.")
        exit(1)

    ## Initialize the LX-16A servo controller
    LX16A.initialize(selected_port, 0.1)
    print("LX-16A Servo Controller initialized successfully.")

    ## Identify all servos in the serial bus
    print("Identifying connected servos...")
    connected_servos = []
    for servo_id in range(1, 10):
        try:
            servo = LX16A(servo_id)
            connected_servos.append(servo_id)
            print(f"Servo ID {servo_id} is connected.")
        except ServoTimeoutError:
            pass  # No servo at this ID, continue searching

    if not connected_servos:
        print("No servos found. Please check your connections and try again.")
        print("Exiting program.")
        exit(1)
    else:
        # print the total number of connected servos and their IDs
        print(f"Total connected servos: {len(connected_servos)}")
        print("Connected Servo IDs:", connected_servos)

    ## dynamically create servo objects for each connected servo
    print("\nCreating servo objects for connected servos...")
    servo_objects = {}
    for servo_id in connected_servos:
        try:
            servo_objects[servo_id] = LX16A(servo_id)
            print(f"Servo object created for ID {servo_id}.")
        except ServoTimeoutError:
            print(f"Failed to create servo object for ID {servo_id}. Skipping.")

    ## set angle limits for each servo
    print("\nSetting angle limits for each servo...")
    servo_limits = {
        1: (95, 145),
        2: (35, 140),
        3: (00, 240),
        4: (00, 240),
        5: (00, 240),
        6: (00, 240)
    }
    for servo_id, limits in servo_limits.items():
        if servo_id in servo_objects:
            try:
                servo_objects[servo_id].set_angle_limits(*limits)
                print(f"Angle limits set for Servo ID {servo_id}: {limits}")

                # Set servo mode

            except ServoTimeoutError:
                print(f"Failed to set angle limits for Servo ID {servo_id}. Skipping.")
        else:
            print(f"Servo ID {servo_id} not found in connected servos. Skipping angle limit setting.")

    ## Set home position for each servo
    print("\nSetting home position for each servo...")
    home_positions = {
        1: 110,
        2: 115,
        3: 120,
        4: 120,
        5: 120,
        6: 120
    }
    for servo_id, home_pos in home_positions.items():
        if servo_id in servo_objects:
            try:
                servo_objects[servo_id].move(home_pos, wait=True)
                print(f"Home position set for Servo ID {servo_id}: {home_pos} degrees")
                LX16A.move_start
            except ServoTimeoutError:
                print(f"Failed to set home position for Servo ID {servo_id}. Skipping.")
        else:
            print(f"Servo ID {servo_id} not found in connected servos. Skipping home position setting.")


print("\n#####################################################################")
print("######################## END ########################################")
print("#####################################################################\n")





        
