#!/bin/bash

echo raspberry | sudo -S stty -F /dev/ttyUSB0 115200
