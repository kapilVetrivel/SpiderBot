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
