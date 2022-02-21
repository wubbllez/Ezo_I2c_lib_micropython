from machine import Pin, I2C
from ezo import *


devices = scan_ezo()
print(readsensor(devices[102]))