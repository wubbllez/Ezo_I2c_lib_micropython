from machine import Pin, I2C
from time import sleep_ms
import os

i2c = I2C(scl=Pin(5), sda=Pin(4), freq=100000)

errors = {
    1: 'SUCCESS',
    2: 'FAIL',
    254: 'NOT_READY',
    255: 'NO_DATA',
    None: 'NOT_READ_CMD'
}    

class EZO:
    def __init__(self, address: int, name: str, fwversion: str, issued_read: bool, readbuffer: bytearray, error: int or None) -> None:
        self.address = address
        self.name = name
        self.fwversion = fwversion
        self.issued_read = issued_read
        self.readbuffer = readbuffer
        self.error = error

    def send_cmd(self, command: str):
        self.error = i2c.writeto(self.address,command)
    def find(self):
        self.error = self.send_cmd("Find")
    def send_read_cmd(self):
        self.send_cmd('r')
    def send_read_with_temp_comp(self, temperature: float):
        self.send_cmd('RT,{temperature}')
    def get_name(self):
        return self.name
    def get_address(self):
        return self.address
    def set_address(self,newaddress:int):
        #blablalblablabla
        print("No")
    def get_error(self):
        print(errors[self.error])
    def read_from_device(self):
        self.readbuffer = i2c.readfrom(self.address, 32)
        return self.readbuffer


def striptrash(data: bytes):
    return data.decode('ascii').strip('\x00').strip('\x01')


def scan_ezo():
    '''
    Scans I2C bus for devices then returns devices with EZO
    '''
    devices = {}
    for address in i2c.scan():
        device = getinfo(int(address))
        device = {device.address: device}
        devices.update(device)
        sleep_ms(100)
    return devices
        

def getinfo(address: int) -> EZO:
    '''
    addr: int I2C address of EZO device
    returns EZO
    '''
    i2c.writeto(address, "i")
    sleep_ms(350)
    read = striptrash(i2c.readfrom(address, 32)).strip('?I,').split(',')
    return EZO(address=int(address),name=read[0],fwversion=read[1],issued_read=False,readbuffer=bytearray(32),error=None)

def readsensor(device: EZO):
    '''
    i2c: configured I2C construct
    device: list of individual device from scan_ezo
    '''
    device.send_read_cmd()
    sleep_ms(600)
    return striptrash(device.read_from_device())

def export_calibration(device: EZO):
    device.send_cmd("Export,?")
    sleep_ms(300)
    calresponse = striptrash(device.read_from_device()).split(',')
    if calresponse[0] == "?EXPORT":
        strings = int(calresponse[1])
        size = int(calresponse[2])
        size_recieved = 0
        calibration = []
        for i in range(strings):
            device.send_cmd("Export")
            sleep_ms(300)
            calibration.append(striptrash(device.read_from_device()))
        device.send_cmd("Export")
        sleep_ms(300)
        if striptrash(device.read_from_device()) == "*DONE":
            for line in calibration: size_recieved += len(line)
            if size == size_recieved:
                fname = device.name + "_" + str(device.address) + "_" + device.fwversion + ".txt"
                f = open(fname, "w")
                f.write(";".join(calibration))
                f.close
                print("Done! Configuration saved at: " + fname)
            else:
                print("Size mismatch! Try rerunning export.")
        else:
            print("Calibration read error!")
    else:
        print("Calibration read error!")


def import_calibration(device: EZO, file: str):
    f = open(file, "r")
    device.send_cmd("Export,?")
    sleep_ms(300)
    calresponse = striptrash(device.read_from_device()).split(',')
    calibration = f.read().split(";")
    if calresponse[0] == "?EXPORT" and len(calibration) == int(calresponse[1]):
        expect_size = int(calresponse[2])
        for line in calibration: file_size += len(line)
        size_sent = 0
        if expect_size == file_size:
            print("write the cal")
        else:
            print("Size mismatch. Do you have the right file/device selected?")
