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
        self.boot_completed = False
        self.boot_count = 1

        # Set path and active folder
        self.active_folder = Path(__file__).parent.resolve()
        os.chdir(self.active_folder)        

        # run Spider Bot
        self.run_status = 1
        self.run_spiderbot()


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

            print(f"Detected {len(self.servos)-1} servos ! ")
            print(f"Detected {len(self.servos)-1} servos ! {self.connected_servo_ids}") if self.verbose != 0 else None

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
    @health_check
    def servo_move(self, pos, time_ms=1000, servo_ids=None, output=False):
        try:
            # Use all servos if none specified
            self.target_servos = self.servos[1:] if servo_ids is None else [self.servos[i] for i in servo_ids]

            # Buffer moves for target servos only
            for self.servo in self.target_servos:
                i = self.servo.get_id()
                self.servo.move(pos[i], time_ms, wait=True)

            # Sync start for target servos only
            for self.servo in self.target_servos:
                self.servo.move_start()

            # Wait for duration
            time.sleep(time_ms/1000)
            
            print(f"Moved servos {servo_ids}.") if self.verbose != 0 else None

        except ServoError as e:
            print(f"Move failed on servo: {e.id_}: {e}")
    
    ###################################################################
    # Servo Homing
    @catch_disconnection
    @health_check
    def servo_homing(self,output=False):
        print("--- ---> Servo Homing: ", end="")
        self.homing_file = [f for f in os.listdir() if f.startswith("servo_limits_") and f.endswith(".txt")]
        
        if self.homing_file:
            print("No servo homing data available. Initiating homing sequence...")
            self.timestamp = time.strftime("%Y%m%d-%H%M%S")

            pos_max = [None] + [240] * 9
            pos_min = [None] + [0] * 9

            for i, self.servo in enumerate(self.servos[1:], 1):
                print(f"Homing servo: {i}")
                # Set max. and min. angle limts to extreme values
                self.servo.set_angle_limits(0, 240)
                print(self.servo.get_angle_limits())
                
                # Find max. angle           
                self.servo_move(pos_max, time_ms=1000,servo_ids=[i])
                self.max_angle_limit = self.read_pos(servo_ids=[i])[0][1]
                time.sleep(0.5)

                # Find min. angle
                self.servo_move(pos_min, time_ms=1000,servo_ids=[i])
                self.min_angle_limit = self.read_pos(servo_ids=[i])[0][1]
                time.sleep(0.5)

                # # Move to Mid Position
                self.home_angle = (self.max_angle_limit + self.min_angle_limit)/2
                self.servo_move([None]+[self.home_angle] * 9, time_ms=500, servo_ids=[i])
                self.servo.disable_torque()
        else:
            print("Homing from previous configuration - ", end="")

            print("Successful !")
                

            




        
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
        self.read_pos(output=True)

        # Servo homing
        self.servo_homing()

        


    
    ###################################################################
    # Run SpiderBot
    @catch_disconnection
    def run_spiderbot(self):
        while self.run_status:
            try:
                self.boot_routine()
                time.sleep(10)

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
