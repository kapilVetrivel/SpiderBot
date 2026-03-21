import os
import time
from typing import List, Optional

import serial.tools.list_ports
from pylx16a.lx16a import LX16A, ServoTimeoutError


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

        self.clear_console()
        self.print_banner()
        self.run_spider_bot()

    def clear_console(self):
        os.system("cls" if os.name == "nt" else "clear")

    def print_banner(self):
        print("#####################################################################")
        print("######################## SPIDER BOT #################################")
        print("#####################################################################\n")

    def reset_connection_state(self):
        self.count_scan_for_ports = 1
        self.selected_port = None
        self.initialize_status = "Not initialized"
        self.connected_servo_ids = []
        self.initial_pos_read = False
        self.boot_completed = False

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

    @catch_disconnection
    def initialize_lx16a(self):
        LX16A.initialize(self.selected_port, 0.1)
        self.initialize_status = "Initialized"
        print("LX16A serial connection initialized successfully.\n")

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

    @catch_disconnection
    def set_servo_limits(self, servo_id, lower_limit, upper_limit):
        servo = LX16A(servo_id)
        servo.set_angle_limits(lower_limit, upper_limit)
        print(
            f"Set limits for Servo {servo_id}: "
            f"Lower={lower_limit}, Upper={upper_limit}"
        )

    @catch_disconnection
    def read_servo_position(self, servo_id, output=False):
        try:
            servo = LX16A(servo_id)
            position = servo.get_physical_angle()
            if output:
                print(f"Servo {servo_id} position: {position} degrees")
            time.sleep(0.2)
            return position
        except Exception as exc:
            print(f"Failed to read position for Servo {servo_id}: {exc}")
            return None

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

    def read_initial_positions(self):
        print("Reading initial servo positions...")
        for servo_id in self.connected_servo_ids:
            self.read_servo_position(servo_id, output=True)
            self.servo_torque(servo_id, enabled=False)
        self.initial_pos_read = True

    def enter_motion_window(self):
        while self.boot_completed:
            self.clear_console()
            self.print_banner()
            print("Motion Window (Ctrl+C to exit)")
            time.sleep(1)

    def run_spider_bot(self):
        print("Starting boot routine (Ctrl+C to exit)")
        print("======================================")

        while True:
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
                    self.boot_completed = True

                print("\n--> Boot routine completed. Entering motion window.")
                input("--> Press Enter to continue (Homing)...")

                self.enter_motion_window()
                break

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

    print("\n\n#####################################################################")
    print("######################## END ########################################")
    print("#####################################################################\n")


if __name__ == "__main__":
    main()
