import os
import time
from typing import List, Optional
from zipfile import Path
from pathlib import Path
import serial.tools.list_ports
from pylx16a.lx16a import LX16A, ServoTimeoutError, ServoError

###################################################################
# Connection error handling decorator to catch exceptions in serial communication and reset connection state
def catch_disconnection(func):
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as exc:
            print(f"Connection error in [{func.__name__}]: {exc}")
            return None

    return wrapper

class SpiderBot:
    
    def __init__(self):
        self.time_out = 5
        self.count_scan_for_ports = 1
        self.update_freq = 0.5
        self.verbose = 0

        # SpiderBot Configuration
        self.no_of_legs = 4
        self.no_of_servos_per_leg = 2
        self.no_of_servos = self.no_of_legs * self.no_of_servos_per_leg
        # Include buffer limit for servo movement
        self.angle_buffer = 5 #degrees

        # Boot routine declarations
        self.selected_port = None
        self.initialize_status = 0
        self.connected_servo_ids: List[int] = []
        self.initial_pos_read = False
        self.homing_state = False
        self.boot_completed = False
        self.boot_count = 1

        # Set path and active folder
        self.active_folder = Path(__file__).parent.resolve()
        os.chdir(self.active_folder)        

        # run Spider Bot
        self.run_status = 1
        self.run_spiderbot()

    #####################################################################
    # Reset connection state to allow for reinitialization in case of errors
    def reset_connection_state(self):
        self.count_scan_for_ports = 1
        self.selected_port = None
        self.initialize_status = 0
        self.connected_servo_ids: List[int] = []
        self.initial_pos_read = False
        self.boot_completed = False

    ###################################################################
    # Clear terminal
    @catch_disconnection
    def clear_console(self):
        os.system("cls" if os.name =="nt" else "clear")

    ###################################################################
    # Entry Banner
    @catch_disconnection
    def entry_banner(self):
        print("######################################################################")
        print("######################## SPIDER BOT ##################################")
        print("##################### Ctrl + C to exit ###############################")
        print("######################################################################")

    ###################################################################
    # Exit Banner
    @catch_disconnection
    def exit_banner(self):
        print("")
        print("#####################################################################")
        print("############################ END ####################################")
        print("#####################################################################\n")


    ###################################################################
    # Scan Ports
    @catch_disconnection
    def scan_ports(self):
        while True:
            print("--- --> Scanning Serial Port...", end="")
            for port in serial.tools.list_ports.comports():            
                if "ttyUSB" in port.device:
                    self.selected_port = port.device
                    self.count_scan_for_ports = 1
                    print("Detected! ")
                    print(f"Detected ! {self.selected_port}") if self.verbose != 0 else None
                    return
            print(
                f"No 'ttyUSB*' serial port(s) found. Retrying "
                f"({self.count_scan_for_ports} of {self.time_out})..."
                )
            self.count_scan_for_ports += 1
            time.sleep(self.update_freq)

            if self.count_scan_for_ports > self.time_out:
                raise RuntimeError("No 'ttyUSB*' serial port found after multiple attempts.")                 

    
    ###################################################################
    # Initialize Serial Port
    @catch_disconnection
    def initialize_lx16a(self):
        print("--- --> Initializing Serial Port...", end="")

        LX16A.initialize(self.selected_port, 0.1) if self.selected_port else None
        self.initialize_status = 1
        print("Completed!")


    ###################################################################
    # Detect Servos on serial port
    @catch_disconnection
    def detect_servos(self):
        print("--- --> Identifying Servos...", end="")
        self.servos = [None] + [LX16A(i) for i in range(1, 9)]
        if len(self.servos) > 1:

            for self.servo in self.servos[1:]:
                self.servo_id = self.servo.get_id(poll_hardware=True)
                self.connected_servo_ids.append(self.servo_id)

            # print(f"Detected {len(self.servos)-1} servos ! ")
            print(f"Detected {len(self.servos)-1} servos ! {self.connected_servo_ids}" if self.verbose != 0 else f"Detected {len(self.servos)-1} servos ! ")

    ###################################################################
    # Servo Health Check
    def health_check(func):
        def health_wrapper(self, *args, **kwargs):
            servo_ids = kwargs.get('servo_ids')
            if servo_ids:  # Quick check for specific servos only
                for sid in servo_ids:
                    try:
                        servo = self.servos[sid]
                        vin = servo.get_vin()
                        temp = servo.get_temp()
                        if temp > 80 or vin < 6000:
                            print(f"WARN Servo {sid}: Temp {temp}°C Vin {vin}mV")
                    except:
                        pass
            else:  # Full check only when no servo_ids
                for servo in self.servos[1:]:
                    try:
                        vin = servo.get_vin()
                        temp = servo.get_temp()
                        temp = servo.get_temp()
                        if temp > 80 or vin < 6000:
                            print(f"WARN Servo {servo._id}: Temp {temp}°C Vin {vin}mV")
                    except:
                        pass
            return func(self, *args, **kwargs)
        return health_wrapper

        
    ###################################################################
    # Read Servo Position
    @catch_disconnection
    @health_check
    def read_pos(self, servo_ids=None, output=False):
     
        # Use all servos if none specified
        self.target_servos = self.servos[1:] if servo_ids is None else [self.servos[i] for i in servo_ids]
        self.positions = []
        for self.servo in self.target_servos:
            i = self.servo._id
            try:
                self.pos = self.servo.get_physical_angle()
                self.positions.append([i, self.pos])
                print(f"--- --- --> Servo {i} : {self.pos}º") if self.verbose != 0 or output else None
            except Exception as e:
                print(f"Failed to read servo {i}: {e}")
                self.positions.append([i, None])
        return self.positions

    ###################################################################
    # Servo Move
    @catch_disconnection
    # @health_check
    def servo_move(self, pos, time_ms=1000, servo_ids=None, output=False, torque=True):
        try:
            # Use all servos if none specified
            self.target_servos = self.servos[1:] if servo_ids is None else [self.servos[i] for i in servo_ids]

            # Enable torque
            for self.servo in self.target_servos:
                self.servo.enable_torque()
                
            # Buffer moves for target servos only
            for self.servo in self.target_servos:
                i = self.servo.get_id()
                self.servo.move(pos[i], time_ms, wait=True)

            # Sync start for target servos only
            for self.servo in self.target_servos:
                self.servo.move_start()

            # Wait for duration
            time.sleep(time_ms/1000)

            # Disable torque
            for self.servo in self.target_servos:
                self.servo.disable_torque() if not torque else None
            
            print(f"--- --- --> Moved servos {servo_ids}.") if self.verbose != 0 else None

        except ServoError as e:
            print(f"Move failed on servo: {e.id_}: {e}")
    
    ###################################################################
    # Servo Homing
    @catch_disconnection
    @health_check
    def servo_homing(self,output=False):
        print("--- --> Servo Homing: ", end="")
        self.homing_file = [f for f in os.listdir() if f.startswith("servo_limits_") and f.endswith(".txt")]
        
        if not self.homing_file:
            print("No servo homing data available. Initiating homing sequence...", end="")
            self.timestamp = time.strftime("%Y%m%d-%H%M%S")

            pos_max = [None] + [240] * 9
            pos_min = [None] + [0] * 9

            for i, self.servo in enumerate(self.servos[1:], 1):
                if True:
                    print(f"Homing servo: {i}", end="")
                    # Set max. and min. angle limts to extreme values
                    self.servo.set_angle_limits(0, 240)
                    # print(self.servo.get_angle_limits())
                    
                    # Find max. angle           
                    self.servo_move(pos_max, time_ms=2000,servo_ids=[i])
                    self.max_angle_limit = min(self.read_pos(servo_ids=[i])[0][1], 240) - self.angle_buffer
                    time.sleep(0.5)

                    # Find min. angle
                    self.servo_move(pos_min, time_ms=2000,servo_ids=[i])
                    self.min_angle_limit = max(self.read_pos(servo_ids=[i])[0][1], 0) + self.angle_buffer
                    time.sleep(0.5)

                    # # Move to Mid Position
                    self.home_angle = round((self.max_angle_limit + self.min_angle_limit)/2,1)
                    print([None]+[self.home_angle] * 9)
                    self.servo_move([None]+[self.home_angle] * 9, time_ms=1000, servo_ids=[i])
                    # self.servo.disable_torque()
                    print("Done !")

                    # Record servo ID, min angle, max angle, and home angle in a list and save it to a file for later import
                    self.servo_info = {
                        "servo_id": self.servo._id,
                        "min_angle": self.min_angle_limit,
                        "max_angle": self.max_angle_limit,
                        "home_angle": self.home_angle
                    }

                    # Save servo info to a file named "servo_limits_{timestamp}.txt" in the active folder.                
                    with open(f"servo_limits_{self.timestamp}.txt", "a") as f:
                        f.write(str(self.servo_info) + "\n")

            self.homing_state = True

        else:
            print("Homing from previous configuration - ", end="")
            self.homing_file = max(self.homing_file, key=os.path.getctime)

            self.servo_id = []
            self.min_angle_limit = []
            self.max_angle_limit = []
            self.home_angle = []
            with open(self.homing_file, "r") as f:
                for line in f:
                    self.servo_info = eval(line.strip())
                    # self.servo_id = self.servo_info["servo_id"]
                    # self.min_angle_limit = self.servo_info["min_angle"]
                    # self.max_angle_limit = self.servo_info["max_angle"]
                    # self.home_angle = self.servo_info["home_angle"]

                    self.servo_id.append(self.servo_info["servo_id"])
                    # self.min_angle_limit.append(self.servo_info["min_angle"])
                    # self.max_angle_limit.append(self.servo_info["max_angle"])
                    self.home_angle.append(self.servo_info["home_angle"])

            self.servo_move([None] + self.home_angle, time_ms=1000, servo_ids=self.servo_id)
            print("Successful !")
            self.homing_state = True
                    
    ###################################################################
    # Forward Movement
    @catch_disconnection
    def move_fwd(self):
        print("--- --> Moving Forward...", end="")

    
    
    ###################################################################
    # Boot routine
    @catch_disconnection
    def boot_routine(self):
        self.clear_console()
        self.entry_banner()
        print("--> Starting Boot Routine...")

        if self.selected_port == None:
            self.scan_ports()
        if self.initialize_status == 0:
            self.initialize_lx16a()
        if not self.connected_servo_ids:
            self.detect_servos()

        # Get initial servo positions
        print("--- --> Reading initial servo positions...")
        self.read_pos(output=True)
        
        # Servo homing
        if not self.homing_state:
            self.servo_homing()

        if self.selected_port != None and self.initialize_status == 1 and self.homing_state == 1:
            print("--> Boot Routine Completed Successfully !")
            print("--> Initiating Motion Control...")
            self.boot_completed = True
            return None
        else:
            print("--> Boot Routine Failed ! Retrying...")
            self.boot_count += 1
            if self.boot_count > self.time_out:
                print("--> Boot Routine Failed. Exiting...")
                self.run_status = 0


    ###################################################################
    # Motion Control
    @catch_disconnection
    def motion_control(self):
        try:
            while self.boot_completed:
                self.clear_console()
                self.entry_banner()
                print("======== Motion Control Window (Ctrl + C to Shut Down) ========")
                print("1. Get servo positions")
                print("2. Move Forward")
                print("3. Move Backward")
                print("4. Disable/Enable Torque (Safe to Pick Up)")
                print("5. Move to Home position")

                choice = input("\nEnter your choice: ")
                if choice == "1":
                    self.read_pos(output=True)
                    input("Press Enter to continue...")
                elif choice == "2":
                    print("Moving Forward...")
                    input("Press Enter to continue...")
                elif choice == "3":
                    print("Moving Backward...")
                    input("Press Enter to continue...")
                elif choice == "4":
                    print("Toggling Torque...")
                    for self.servo in self.servos[1:]:
                        if self.servo._torque_enabled:
                            self.servo.disable_torque()
                        else:
                            self.servo.enable_torque()
                    time.sleep(0.5)
                elif choice == "5":
                    print("Moving to Home position...")
                    self.servo_move([None] + self.home_angle, time_ms=1000, servo_ids=self.servo_id)
                    input("Press Enter to continue...")
                else:
                    print("Invalid choice. Please try again.")


                time.sleep(0.2)
        except KeyboardInterrupt:
            print("\n--> Shutting down...")
            self.shutdown()
            self.reset_connection_state()
            self.exit_banner()
            exit(0)
        

        
    ###################################################################
    # Shut Down
    @catch_disconnection
    def shutdown(self):

        # Check if servo_limits file already exists and import limits from it.
        self.shutdown_files = [f for f in os.listdir() if f.startswith("servo_shutdown_") and f.endswith(".txt")]
        if self.shutdown_files:
            self.shutdown_file = max(self.shutdown_files, key=os.path.getctime)
            print(f"Found existing servo shutdown file: {self.shutdown_file}. Importing shutdown positions from there...") if self.verbose != 0 else None
            self.servo_id = []
            self.min_angle_limit = []
            self.max_angle_limit = []
            self.home_angle = []
            with open(self.shutdown_file, "r") as f:
                for line in f:
                    self.servo_info = eval(line.strip())
                    # self.servo_id = self.servo_info["servo_id"]
                    # self.min_angle_limit = self.servo_info["min_angle"]
                    # self.max_angle_limit = self.servo_info["max_angle"]
                    # self.home_angle = self.servo_info["home_angle"]

                    self.servo_id.append(self.servo_info["servo_id"])
                    # self.min_angle_limit.append(self.servo_info["min_angle"])
                    # self.max_angle_limit.append(self.servo_info["max_angle"])
                    self.home_angle.append(self.servo_info["home_angle"])

            self.servo_move([None] + self.home_angle, time_ms=1000, servo_ids=self.servo_id, torque=False)

            print("Successful ! Torque disabled - Safe to pick up.")                   


    
    ###################################################################
    # Run SpiderBot
    @catch_disconnection
    def run_spiderbot(self):
        while self.run_status:
            try:
                self.boot_routine()
                time.sleep(2)
                self.motion_control() if self.boot_completed else None
                time.sleep(5)

            except KeyboardInterrupt:
                self.run_status = int(input("\nKeyboard Interruption: [Enter]-Continue or [0]-Exit ? :") or "1")
                time.sleep(1)
            self.exit_banner()


######################################################################################################################################


###################################################################
# main declaration
def main():
    try:
        SpiderBot()
    except KeyboardInterrupt:
        print("\n\n--> Force abort by user. Exiting...")
    except Exception as exc:
        print(f"Error executing main(): {exc}")
    

###################################################################
# Run when file is main
if __name__ == "__main__":
    main()
