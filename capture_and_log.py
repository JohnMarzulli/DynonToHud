#!/usr/bin/python3

import serial
import datetime

print(serial.__file__)

SERIAL_DEVICE = '/dev/ttyUSB0'

current_date = datetime.datetime.now()
new_log_fileName = f"{current_date.year}-{current_date.month}-{current_date.day}_{0:02d}{1:02d}.dynon180.log".format(
    current_date.hour,
    current_date.minute)

serial_reader = serial.Serial(
    SERIAL_DEVICE,
    baudrate=115200,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=0)

serial_reader.flushInput()

with open(new_log_fileName, 'w') as output_file:
    while True:
        # Would have a cr/lf at the end
        # "00082119+058-00541301200+9141+011-01+15003EA0C701A4"
        serial_bytes = serial_reader.readline()
        serial_input = str(serial_bytes, encoding='ascii') + "\n"
        output_file.write(serial_input)
        output_file.flush()
        print(serial_input)
