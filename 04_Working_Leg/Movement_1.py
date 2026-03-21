from math import sin, cos
from pylx16a.lx16a import *
import time

LX16A.initialize("/dev/ttyUSB0", 0.1)

try:
    servo1 = LX16A(1)
    servo2 = LX16A(2)
    servo1.set_angle_limits(95, 145)
    servo2.set_angle_limits(35, 140)
except ServoTimeoutError as e:
    print(f"Servo {e.id_} is not responding. Exiting...")
    quit()

t = 0

# set home position

# get servo positions
servo1_pos = servo1.get_physical_angle()
servo2_pos = servo2.get_physical_angle()
print(f"Servo 1 initial position: {servo1_pos} degrees")
print(f"Servo 2 initial position: {servo2_pos} degrees")

servo1_pos_home = 110
servo2_pos_home = 115

# while abs(servo1_pos - servo1_pos_home) > 1 and abs(servo2_pos - servo2_pos_home) > 1:
#     servo1.move(servo1_pos_home, wait=True)
#     servo2.move(servo2_pos_home, wait=True)
#     servo1_pos = servo1.get_physical_angle()
#     servo2_pos = servo2.get_physical_angle()
#     print(f"Moving to home position... Servo 1: {servo1_pos} degrees, Servo 2: {servo2_pos} degrees")
#     servo1.move(110)
#     servo2.move(115)
#     time.sleep(1)

# time.sleep(2)

# while True:
#     servo1_pos_req = round(sin(22/7/180*t) * 25 + servo1_pos_home,2)
#     servo2_pos_req = round(sin(22/7/180*t) * 20 + servo2_pos_home,2)
#     servo1.move(servo1_pos_req) #(55,165) range. Limits 165 +/- 55
#     servo2.move(servo2_pos_req) #(80,190) range. Limits 115 +/- 20
#     servo1_pos = servo1.get_physical_angle()
#     servo2_pos = servo2.get_physical_angle()
#     print(f"Moving to position... Servo 1: {servo1_pos} [act: {servo1_pos_req}], Servo 2: {servo2_pos} [act: {servo2_pos_req}]")

#     time.sleep(0.05)
#     t += 1
