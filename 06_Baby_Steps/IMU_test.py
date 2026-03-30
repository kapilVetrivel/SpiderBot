import time
import board
from adafruit_lsm6ds.lsm6dsox import LSM6DSOX
import os

os.system('clear')  # Clear the console for better readability

#initialize I2C bus and sensor
i2c = board.I2C()
sensor = LSM6DSOX(i2c)

freq = 10  # Set the output data rate to 10 Hz

while True:
    #read accelerometer and gyroscope data
    accel_x, accel_y, accel_z = sensor.acceleration
    gyro_x, gyro_y, gyro_z = sensor.gyro

    #print the data to the console
    print("Accelerometer (m/s^2): X={0:.2f}, Y={1:.2f}, Z={2:.2f}".format(accel_x, accel_y, accel_z))
    print("Gyroscope (dps): X={0:.2f}, Y={1:.2f}, Z={2:.2f}".format(gyro_x, gyro_y, gyro_z))
    
    #wait for a short period before the next reading
    time.sleep(1 / freq)