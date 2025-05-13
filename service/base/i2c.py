import threading
import smbus2


_bus1 = smbus2.SMBus(1)

i2c_lock = threading.Lock()


def write_byte_data(address, register, value):
    with i2c_lock:
        _bus1.write_byte_data(address, register, value)


def read_byte_data(address, register):
    with i2c_lock:
        return _bus1.read_byte_data(address, register)


def write_i2c_block_data(address, register, data):
    with i2c_lock:
        _bus1.write_i2c_block_data(address, register, data)


def read_i2c_block_data(address, register, length):
    with i2c_lock:
        return _bus1.read_i2c_block_data(address, register, length)
