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
        self.time_out = 5
        self.count_scan_for_ports = 1

        # SpiderBot Configuration
        self.no_of_legs = 4
        self.no_of_servos_per_leg = 2
        self.no_of_servos = self.no_of_legs * self.no_of_servos_per_leg
        # Include buffer limit for servo movement
        self.angle_buffer = 5 #degrees

        # Boot routine declarations
        self.selected_port = None
        self.initialze_status = None
        self.connected_servo_ids: List[int] = []
        self.initial_pos_read = False
        self.boot_completed = False
        self.boot_count = 1

        # run Spider Bot
        self.run_status = 1
        self.run_spiderbot()

    ###################################################################
    # Clear terminal
    def clear_console(self):
        os.system("cls" if os.name =="nt" else "clear")

    ###################################################################
    # Entry Banner
    def entry_banner(self):
        print("######################################################################")
        print("######################## SPIDER BOT ##################################")
        print("######################################################################\n")

    ###################################################################
    # Exit Banner
    def exit_banner(self):
        print("")
        print("#####################################################################")
        print("############################ END ####################################")
        print("#####################################################################\n")


    ###################################################################
    # Boot routine
    def boot_routine(self):
        self.entry_banner()
    
    ###################################################################
    # Run SpiderBot
    def run_spiderbot(self):
        while self.run_status:
            try:
                self.clear_console()
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
