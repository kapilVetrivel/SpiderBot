import os
import time
from typing import List, Optional
from zipfile import Path
from pathlib import Path


import serial.tools.list_ports
from pylx16a.lx16a import LX16A, ServoTimeoutError

###################################################################
# Connection error handling decorator to catch exceptions in serial communication and reset connection state
def catch_disconnection(func):
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as exc:
            print(f"Connection error in {func.__name__}: {exc}")
            self.reset_connection_state()
            return None

    return wrapper


class SpiderBot:
    def __init__(self):
        self.update_frequency = 0.1
        self.time_out = 5
        self.count_scan_for_ports = 1

        self.no_of_legs = 4
        self.no_of_servos_per_leg = 2
        self.no_of_servos = self.no_of_legs * self.no_of_servos_per_leg

        self.angle_buffer = 5

        self.joint_to_servo = {
            "leg1_hip": [1, 110],
            "leg1_knee": [2, 40],
            "leg2_hip": [3, 140],
            "leg2_knee": [4, 40],
            "leg3_hip": [5, 140],
            "leg3_knee": [6, 40],
            "leg4_hip": [7, 110],
            "leg4_knee": [8, 40],
        }

        self.servo_safe_positions = {
            1: 110,
            2: 40,
            3: 140,
            4: 40,
            5: 140,
            6: 40,
            7: 110,
            8: 40,
        }

        self.selected_port: Optional[str] = None
        self.initialize_status = "Not initialized"
        self.connected_servo_ids: List[int] = []
        self.initial_pos_read = False
        self.boot_completed = False
        self.boot_count = 1

        self.clear_console()
        self.run_spider_bot()

    def clear_console(self):
        os.system("cls" if os.name == "nt" else "clear")

    def print_entry_banner(self):
        print("#####################################################################")
        print("######################## SPIDER BOT #################################")
        print("#####################################################################\n")

    #####################################################################
    # Reset connection state to allow for reinitialization in case of errors
    def reset_connection_state(self):
        self.count_scan_for_ports = 1
        self.selected_port = None
        self.initialize_status = "Not initialized"
        self.connected_servo_ids = []
        self.initial_pos_read = False
        self.boot_completed = False

    ###################################################################
    # Scan for eligible ports and select the first one that matches the criteria (contains 'ttyUSB')
    @catch_disconnection
    def scan_for_ports(self):
        while self.selected_port is None:
            ports = serial.tools.list_ports.comports()

            for port in ports:
                if "ttyUSB" in port.device:
                    self.selected_port = port.device
                    print(f"Selected port: {self.selected_port}\n")
                    self.count_scan_for_ports = 1
                    return

            print(
                f"No 'ttyUSB*' serial port found. Retrying "
                f"({self.count_scan_for_ports} of {self.time_out})..."
            )
            self.count_scan_for_ports += 1
            time.sleep(self.update_frequency)

            if self.count_scan_for_ports > self.time_out:
                raise RuntimeError(
                    "No 'ttyUSB*' serial port found after multiple attempts."
                )

    ###################################################################
    # Initialize the LX16A library with the selected port and a short timeout. This will be used for all subsequent communication with the servos.
    @catch_disconnection
    def initialize_lx16a(self):
        LX16A.initialize(self.selected_port, 0.1) if self.selected_port else None
        self.initialize_status = "Initialized"
        print("LX16A serial connection initialized successfully.\n")

    ###################################################################
    # Scan for connected servos by trying to create an instance of the LX16A class for each possible servo ID. 
    # If it succeeds, the servo is considered connected and its ID is added to the list. 
    # If it fails (e.g., due to a timeout), it moves on to the next ID. This allows us to dynamically detect which servos are actually present and responsive.
    @catch_disconnection
    def get_servo_ids(self):
        self.connected_servo_ids = []

        for servo_id in range(1, 10):
            try:
                LX16A(servo_id)
                self.connected_servo_ids.append(servo_id)
            except ServoTimeoutError:
                continue

        print(
            f"Total servo IDs connected: "
            f"{len(self.connected_servo_ids)}/{self.no_of_servos} "
            f"- {self.connected_servo_ids}\n"
        )

    ###################################################################
    # Set angle limits for a given servo ID. This is important to prevent the servos from trying to move beyond their physical limits, which could cause damage.
    @catch_disconnection
    def set_servo_limits(self, servo_id, lower_limit, upper_limit):
        servo = LX16A(servo_id)
        servo.set_angle_limits(lower_limit, upper_limit)
        print(
            f"Set limits for Servo {servo_id}: "
            f"Lower={lower_limit}, Upper={upper_limit}"
        )

    ###################################################################
    # Read the current position of a servo by its ID. 
    # The output parameter allows us to print the position if desired.
    @catch_disconnection
    def read_servo_position(self, servo_id, output=False):
        try:
            servo = LX16A(servo_id)
            position = round(servo.get_physical_angle(),1)
            if output:
                print(f"Servo {servo_id} position: {position} degrees")
            time.sleep(0.2)
            return position
        except Exception as exc:
            print(f"Failed to read position for Servo {servo_id}: {exc}")
            return None

    ###################################################################
    # Enable or disable torque for a given servo ID.
    @catch_disconnection
    def servo_torque(self, servo_id, enabled=False, output=False):
        try:
            servo = LX16A(servo_id)
            if enabled:
                servo.enable_torque()
                if output:
                    print(f"Torque enabled for Servo {servo_id}.")
            else:
                servo.disable_torque()
                if output:
                    print(
                        f"Torque disabled for Servo {servo_id}. "
                        "You can now manually move the servo."
                    )
        except Exception as exc:
            print(f"Failed to change torque for Servo {servo_id}: {exc}")
            return None

    ###################################################################
    # Move a servo to a specified position. 
    @catch_disconnection
    def move_servo(self, servo_id, position):
        try:
            servo = LX16A(servo_id)
            servo.move(position)
            current_position = self.read_servo_position(servo_id, output=False)
            print(f"Moving Servo {servo_id} to position: {current_position} degrees")
            time.sleep(0.5)
        except Exception as exc:
            print(f"Failed to move Servo {servo_id} to position {position}: {exc}")

        
    # Read the initial positions of all connected servos.
    @catch_disconnection
    def read_initial_positions(self):
        print("Reading initial servo positions...")
        for servo_id in self.connected_servo_ids:
            self.read_servo_position(servo_id, output=True)
            self.servo_torque(servo_id, enabled=False)
        self.initial_pos_read = True

    ###################################################################
    # Sweep and homing function to find the physical limits of each servo and set them as the new angle limits. 
    # This is important to ensure that the servos do not try to move beyond their physical
    @catch_disconnection
    def sweep_and_home_servos(self):

        self.active_folder = Path(__file__).parent.resolve()
        os.chdir(self.active_folder)
        
        # Check if servo_limits file already exists and import limits from there if it does, otherwise perform the sweep and save the limits to a new file. This allows us to avoid having to sweep the servos every time we start the robot, which can save time and reduce wear on the servos.
        existing_files = [f for f in os.listdir() if f.startswith("servo_limits_") and f.endswith(".txt")]
        if existing_files:
            latest_file = max(existing_files, key=os.path.getctime)
            print(f"Found existing servo limits file: {latest_file}. Importing limits from there...")
            with open(latest_file, "r") as f:
                for line in f:
                    servo_info = eval(line.strip())
                    servo_id = servo_info["servo_id"]
                    min_angle = servo_info["min_angle"]
                    max_angle = servo_info["max_angle"]
                    home_angle = servo_info["home_angle"]

                    servo = LX16A(servo_id)
                    servo.set_angle_limits(min_angle, max_angle)
                    servo.move(home_angle)
                    time.sleep(0.25)        
                

            print("Servo limits imported successfully.\n")
            return
        else:
            print("No existing servo limits file found. Starting sweep to find limits...\n")

            # get datetime stamp for file naming
            self.timestamp = time.strftime("%Y%m%d-%H%M%S")

            for servo_id in self.connected_servo_ids:
                servo = LX16A(servo_id)

                min_angle = 0
                max_angle = 240
                step = 10
                time_delay = 0.25

                servo.set_angle_limits(min_angle, max_angle)
                print(f"Servo {servo_id} initial angle limits set to {min_angle} - {max_angle} degrees")

                initial_angle = servo.get_physical_angle() # Read current position to ensure communication is working
                print(f"Initial position of Servo {servo_id}: {initial_angle} degrees. Sweeping to find limits...", end=" ")

                current_angle = initial_angle

                # Find max. angle
                while True:
                    servo.move(240) # Ensure we don't command the servo to move above 240 degrees
                    time.sleep(time_delay) # Wait for the servo to move and stabilize

                    new_angle = servo.get_physical_angle()
                    # print(f"Servo {servo_id} moved from {current_angle} to {new_angle} degrees")

                    if new_angle == current_angle:
                        print(f"Max limit: {current_angle}º", end=" ")
                        max_angle = min(new_angle, 240) - self.angle_buffer
                        break
                    current_angle = servo.get_physical_angle()

                # Find min. angle
                while True:
                    servo.move(0) # Ensure we don't command the servo to move below 0 degrees
                    time.sleep(time_delay) # Wait for the servo to move and stabilize

                    new_angle = servo.get_physical_angle()
                    # print(f"Servo {servo_id} moved from {current_angle} to {new_angle} degrees")

                    if new_angle == current_angle:
                        print(f"Min limit: {current_angle}º")
                        min_angle = max(new_angle, 0) + self.angle_buffer
                        break
                    current_angle = servo.get_physical_angle()

                # move to home target angle
                home_angle = round(min_angle + (max_angle - min_angle) / 2,1)
                servo.set_angle_limits(min_angle, max_angle)
                servo.move(home_angle)
                time.sleep(0.5)
                

                # Record servo ID, min angle, max angle, and home angle in a list and save it to a file for later import
                self.servo_info = {
                    "servo_id": servo_id,
                    "min_angle": min_angle,
                    "max_angle": max_angle,
                    "home_angle": home_angle
                }

                # Save servo info to a file named "servo_limits_{timestamp}.txt" in the active folder.                
                with open(f"servo_limits_{self.timestamp}.txt", "a") as f:
                    f.write(str(self.servo_info) + "\n")

    ###################################################################
    # Enter the motion window where you can implement the main control loop for the robot's movements.
    @catch_disconnection
    def enter_motion_window(self):
        try:
            while self.boot_completed:
                self.clear_console()
                self.print_entry_banner()
                print("Motion Window (Ctrl+C to shut down)")
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
            self.shutdown()
            self.reset_connection_state()
            print("\n\n#####################################################################")
            print("######################## END ########################################")
            print("#####################################################################\n")
            exit(0)

    ###################################################################
    # Shut down the robot by moving all servos to their safe positions and disabling torque. 
    # This is important to ensure that the robot is in a safe state when it is turned off, which can help prevent damage to the servos and the robot itself.
    # safe positions read from servo_shutdown_positions.txt file if it exists, otherwise defaults to the home position defined in the servo_limits file.
    @catch_disconnection
    def shutdown(self):

        # Check if servo_limits file already exists and import limits from there if it does, otherwise perform the sweep and save the limits to a new file. This allows us to avoid having to sweep the servos every time we start the robot, which can save time and reduce wear on the servos.
        existing_files = [f for f in os.listdir() if f.startswith("servo_shutdown_") and f.endswith(".txt")]
        if existing_files:
            latest_file = max(existing_files, key=os.path.getctime)
            print(f"Found existing servo shutdown file: {latest_file}. Importing shutdown positions from there...")
            with open(latest_file, "r") as f:
                for line in f:
                    servo_info = eval(line.strip())
                    servo_id = servo_info["servo_id"]
                    min_angle = servo_info["min_angle"]
                    max_angle = servo_info["max_angle"]
                    home_angle = servo_info["home_angle"]

                    servo = LX16A(servo_id)
                    servo.set_angle_limits(min_angle, max_angle)
                    servo.move(home_angle)
                    time.sleep(0.25)
                    servo.disable_torque()

            print("Disabled servo torque. Safe to pick up.")



    ###################################################################
    # Run the spider bot main loop.
    @catch_disconnection
    def run_spider_bot(self):
        

        while True:
            os.system("cls" if os.name == "nt" else "clear")
            self.print_entry_banner()
            print("Starting boot routine (Ctrl+C to exit)")
            print("======================================")

            try:
                if self.selected_port is None:
                    self.scan_for_ports()

                time.sleep(1)

                if self.initialize_status != "Initialized":
                    self.initialize_lx16a()

                if not self.connected_servo_ids:
                    self.get_servo_ids()

                if not self.initial_pos_read and self.connected_servo_ids:
                    self.read_initial_positions()

                self.sweep_and_home_servos()
                
                # Verify all boot steps are completed before entering the motion window
                if (self.selected_port is not None and
                    self.initialize_status == "Initialized" and
                    len(self.connected_servo_ids) == self.no_of_servos and
                    self.initial_pos_read):
                    self.boot_completed = True

                if self.boot_completed:                    
                    print("\n--> Boot routine completed. Entering motion window.")
                    input("--> Press Enter to continue ...")

                    self.enter_motion_window()

                else:
                    print(f"\n--> Boot routine not completed yet. Attempt boot routine {self.boot_count} of {self.time_out}...")
                    self.reset_connection_state()
                    self.boot_count += 1
                    if self.boot_count > self.time_out:
                        print("\n--> Boot routine failed after multiple attempts. Please check connections and restart.")
                        break
                    time.sleep(2)

            except KeyboardInterrupt:
                raise
            except Exception as exc:
                print(f"Error in main loop: {exc}")
                print("Attempting to reconnect...")
                self.reset_connection_state()


def main():
    try:
        SpiderBot()
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting...")

    except Exception as exc:
        print(f"Error initializing robot: {exc}")

    


if __name__ == "__main__":
    main()
