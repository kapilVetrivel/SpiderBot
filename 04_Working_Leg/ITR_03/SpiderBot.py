import os, time
from pylx16a.lx16a import *
import serial.tools.list_ports

def catch_disconnection(func):
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            print(f"Catch_disconnect Error: {e}") # Attempt to find the serial port again
        
    return wrapper

class SpiderBot():
    def __init__(self):
        super().__init__()
        # Clear Console
        os.system('cls' if os.name == 'nt' else 'clear')

        # Configuration
        self.update_frequency = 0.1  # seconds between updates
        self.time_out = 5

        self.count_scan_for_ports = 1

        # Robot Configuration
        self.no_of_legs = 4
        self.no_of_servos_per_leg = 2
        self.no_of_servos = self.no_of_legs * self.no_of_servos_per_leg

        # Assign Robot Joint Names to Servo IDs as Dictionary
        self.joint_to_servo = {
            "leg1_hip"  : [1, 110],
            "leg1_knee" : [2, 40],
            "leg2_hip"  : [3, 140],
            "leg2_knee" : [4, 40],
            "leg3_hip"  : [5, 140],
            "leg3_knee" : [6, 40],
            "leg4_hip"  : [7, 110],
            "leg4_knee" : [8, 40]
        }

        # Assign safe positions for servo IDs as Dictionary
        self.servo_safe_positions = {
            1: 110,
            2: 40,
            3: 140,
            4: 40,
            5: 140,
            6: 40,
            7: 110,
            8: 40
        }

        print("#####################################################################")
        print("######################## SPIDER BOT #################################")
        print("#####################################################################\n")

        self.selected_port = "None"
        self.initialize_status = "None"
        self.connected_servo_ids = []
        self.initial_pos_read = []


        self.run_SpiderBot()


    ###########################################################################
    # Serial Port Connection
    @catch_disconnection
    def scan_for_ports(self):
        while self.selected_port == "None":
            ports = serial.tools.list_ports.comports()
            for port in ports:
                if "ttyUSB" in port.device:
                    self.selected_port = port.device
                    print(f"Selected Port : {self.selected_port}\n")
                    self.count_scan_for_ports = 1
                    break

            if self.selected_port == "None":
                print(f"No 'ttyUSB*' serial port found. Retrying ({self.count_scan_for_ports} of {self.time_out} attempts)...")
                self.count_scan_for_ports += 1
                time.sleep(self.update_frequency)
                if self.count_scan_for_ports > self.time_out:
                    print("No 'ttyUSB*' serial port found after multiple attempts. Please connect your device and try again.")
                    print("Exiting program.")
                    exit(1)
                    
    ###########################################################################
    # Initialize LX16A Serial Connection
    @catch_disconnection
    def initialize_LX16A(self):
        try:
            LX16A.initialize(self.selected_port, 0.1)
            self.initialize_status = "Initialized"
            print("LX16A Serial Connection Initialized Successfully.\n")
        except Exception as e:
            print(f"Failed to initialize LX16A connection: {e}")
            print("Attempting to reconnect...")
            self.count_scan_for_ports = 1 # Reset the scan count to start scanning again
            self.selected_port = None # Remove the selected port to trigger a new scan

    ###########################################################################
    # Get all servo IDs in the serial bus
    @catch_disconnection
    def get_servo_ids(self):
        for servo_id in range(1, 10):
            try:
                servo = LX16A(servo_id)
                self.connected_servo_ids.append(servo_id)
            except ServoTimeoutError:
                pass  # No servo at this ID, continue searching
        print(f"Total Servo IDs connected: {len(self.connected_servo_ids)}/{self.no_of_servos} - {self.connected_servo_ids}\n")

    ###########################################################################
    # Set Servo Position Limits
    @catch_disconnection
    def set_servo_limits(self, servo_id, lower_limit, upper_limit):
        try:
            servo = LX16A(servo_id)
            servo.set_angle_limits(lower_limit, upper_limit)
            print(f"Set limits for Servo {servo_id}: Lower={lower_limit}, Upper={upper_limit}")
        except Exception as e:
            print(f"Failed to set limits for Servo {servo_id}: {e}")
    
    ###########################################################################
    # Read Servo Positions
    @catch_disconnection
    def read_servo_position(self, servo_id, output=False):
        try:
            servo = LX16A(servo_id)
            position = servo.get_physical_angle()
            if output:
                print(f"Servo {servo_id} position: {position} degrees")
            time.sleep(0.2) # Add a small delay to prevent overwhelming the serial connection
            return position
        except Exception as e:
            print(f"Failed to read position for Servo {servo_id}: {e}")
            return None

    ###########################################################################
    # Enable/Disable Servo Torque
    @catch_disconnection
    def servo_torque(self, servo_id, torque=0, output=False):
        try:
            servo = LX16A(servo_id)
            if torque == 0:
                servo.disable_torque()
                print(f"Torque disabled for Servo {servo_id}. You can now manually move the servo to adjust its position.") if output else None
            else:
                servo.enable_torque()
                print(f"Torque enabled for Servo {servo_id}. The servo will now hold its position.") if output else None
        except Exception as e:
            print(f"Failed to enable/disable torque for Servo {servo_id}: {e}")
            return None

    ###########################################################################
    # Move Servo to Position
    @catch_disconnection
    def move_servo(self, servo_id, position):
        try:
            servo = LX16A(servo_id)
            servo.move(position)
            print(f"Moving Servo {servo_id} to position: ", end="")
            print(f"{self.read_servo_position(servo_id, output=False)} degrees")
            time.sleep(0.5) # Add a small delay to prevent overwhelming the serial connection
        except Exception as e:
            print(f"Failed to move Servo {servo_id} to position {position}: {e}")
   
    ###########################################################################
    # Run SpiderBot Main Loop
    @catch_disconnection
    def run_SpiderBot(self):
        print('Starting Boot Routine (Ctrl+C to exit)')
        print('======================================')
        while True:
            try:
                # Ensure we have a valid port connection before proceeding
                if self.selected_port == "None":
                    self.scan_for_ports()      
                time.sleep(1) # Placeholder for main loop tasks

                # Initialize LX16A Servos
                if self.initialize_status != "Initialized":
                    self.initialize_LX16A()            

                # Get available servo IDs
                if self.connected_servo_ids == []:
                    self.get_servo_ids()

                # Get inital servo positions
                print("Reading initial servo positions...")
                if self.initial_pos_read == [] and self.connected_servo_ids != []:
                    for servo_id in self.connected_servo_ids:
                        self.read_servo_position(servo_id, output=True)
                        self.servo_torque(servo_id, torque=0) # Disable torque to allow manual movement
                        
                    self.initial_pos_read = [True] * len(self.connected_servo_ids)

                # Complete Boot Routine and enter motion window
                print("\n--> Boot routine completed. Entering motion window.")
                pause = input("--> Press Enter to continue (Homing)...")

                self.boot_completed = True
                

                while self.boot_completed:
                    os.system('cls' if os.name == 'nt' else 'clear')

                    print("#####################################################################")
                    print("######################## SPIDER BOT #################################")
                    print("#####################################################################\n")
                    print("Motion Window (Ctrl+C to exit)")

                # Move servos to safe positions
                # print("\nMoving servos to safe positions...")
                # for servo_id in self.connected_servo_ids:
                #     if servo_id in self.servo_safe_positions:
                #         self.move_servo(servo_id, self.servo_safe_positions[servo_id])
                #     else:
                #         print(f"No safe position defined for Servo {servo_id}. Skipping move command.")

                break

                
                




            except Exception as e:
                print(f"Error in main loop: {e}")
                print("Attempting to reconnect...")
                self.count_scan_for_ports = 1 # Reset the scan count to start scanning again
                self.selected_port = None # Remove the selected port to trigger a new scan

    
  

def main():
    
    try:
        robot = SpiderBot()
    except KeyboardInterrupt as e:
        print(f"\nInterrupted by User. Exiting...")
    except Exception as e:
        print(f"Error initializing robot: {e}")

    print("\n\n#####################################################################")
    print("######################## END ########################################")
    print("#####################################################################\n")


if __name__ == "__main__":
    main()