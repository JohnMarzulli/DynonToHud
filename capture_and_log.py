#!/usr/bin/python3

import datetime
import time

import serial

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
    timeout=10)

serial_reader.flushInput()

with open(new_log_fileName, 'w') as output_file:
    while True:
        # Section 11-1
        # https://www.dynonavionics.com/includes/guides/FlightDEK-D180_Pilot's_User_Guide_Rev_H.pdf
        # Would have a cr/lf at the end
        # EFIS: "21301133-008+00001100000+0024-002-00+1099FC39FE01AC"
        # EMS : "211316033190079023001119-020000000000066059CHT00092CHT00090N/AXXXXX099900840084058705270690116109209047124022135111036A"
        serial_bytes = serial_reader.readline()
        if serial_bytes != None and len(serial_bytes) > 0:
            serial_input = str(serial_bytes, encoding='ascii')
            output_file.write(serial_input)
            output_file.flush()
            print(serial_input)
