import os, time
from pylx16a.lx16a import *
import serial.tools.list_ports

# Clear Console
os.system('cls' if os.name == 'nt' else 'clear')

# Configuration
update_frequency = 1  # seconds between updates
time_out = 5

# Robot Configuration
no_of_legs = 4
no_of_servos_per_leg = 2
no_of_servos = no_of_legs * no_of_servos_per_leg

print("#####################################################################")
print("######################## SPIDER BOT #################################")
print("#####################################################################\n")

def find_serial_ports_():
    ## Search for serial port "ttyUSB*" and select it
    t_search = 0
        
    while 'selected_port' not in locals():
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if "ttyUSB" in port.device:
                selected_port = port.device
                print(f"Selected Port : {selected_port}\n")
                return selected_port
        if 'selected_port' not in locals():
            t_search += update_frequency
            if t_search >= time_out:
                print("No 'ttyUSB*' serial port found after multiple attempts. Please connect your device and try again.")
                print("Exiting program.")
                exit(1)
            print(f"No 'ttyUSB*' serial port found. Retrying ({t_search} of {time_out} attempts)...")
            time.sleep(update_frequency)



if __name__ == '__main__':
    
    ## Start main loop
    print('Starting Boot Routine (Ctrl+C to exit)')
    print('======================================')
    while True:        
        
        try:
            ## Search for serial port "ttyUSB*" and select it
            t_search = 0
            while 'selected_port' not in locals():
                print('----------------------')
                print('Serial Port Connection')
                print('----------------------')
                print("Searching for serial ports 'ttyUSB*'...")
                selected_port = find_serial_ports_()

            ## Initialize the LX-16A servo controller
            t_initialize = 0
            while 'lx16a_init' not in locals():
                print('------------------------------')
                print('Servo BusLinker Initialization')
                print('------------------------------')        
                print("Initializing LX-16A Servo Controller...", end="")
                try:
                    lx16a_init = LX16A.initialize(selected_port, 0.1)
                    print("Successful.\n")
                except Exception as e:
                    t_initialize += update_frequency
                    print(f"Cannot initialize. Retrying ({t_initialize} of {time_out} attempts)...")
                    if t_initialize >= time_out:
                        print(f"Failed Initializing LX-16A Controller: {e}")                        
                        print("Exiting program.")                        
                        exit(1)
                    time.sleep(update_frequency)

            ## Identify all servos in the serial bus
            if 'connected_servos' not in locals():
                connected_servos = []
            t_connected_servo = 1
            while len(connected_servos) < no_of_servos:
                print('--------------------')
                print('Servo Identification')
                print('--------------------')
                print("Identifying connected servos...")
                connected_servos = []
                for servo_id in range(1, 10):
                    try:
                        servo = LX16A(servo_id)
                        connected_servos.append(servo_id)
                    except ServoTimeoutError:
                        pass  # No servo at this ID, continue searching
                print(f"Servo IDs {connected_servos} are connected.")
                if len(connected_servos) < no_of_servos:
                    print(f"Found {len(connected_servos)}/{no_of_servos} servos. Retrying...(attempt {t_connected_servo} of {time_out})")
                    t_connected_servo += update_frequency
                    if t_connected_servo > time_out:
                        print(f"Failed to find all servos after multiple attempts. Found {len(connected_servos)} out of {no_of_servos}.")
                        print("Exiting program.")
                        exit(1)
                    time.sleep(update_frequency)

                else:
                    print(f"Total connected servos: {len(connected_servos)}/{no_of_servos}")
                    break  # Exit the identification loop

        except Exception as e:
            print(f"An error occurred: {e}")
            print("Restarting the process...")
            # Clear variables to restart the process
            if 'selected_port' in locals():
                del selected_port
            if 'lx16a_init' in locals():
                del lx16a_init
            time.sleep(update_frequency)  # Wait before retrying

        except KeyboardInterrupt:
            print("\nProgram interrupted by user. Exiting.")
            break
            
print("\n#####################################################################")
print("######################## END ########################################")
print("#####################################################################\n")


