import time
from .base import i2c


class PCA9685:
    __MODE1 = 0x00
    __PRESCALE = 0xFE
    __LED0_ON_L = 0x06

    def __init__(self, address=0x40, busnum=1):
        self.address = address
        self.set_all_pwm(0, 0)
        self.write(self.__MODE1, 0x00)  # 重置

    def write(self, reg, value):
        i2c.write_byte_data(self.address, reg, value)

    def read(self, reg):
        return i2c.read_byte_data(self.address, reg)

    def set_pwm_freq(self, freq_hz):
        """设置频率（通常为 50Hz 控制舵机）"""
        prescale_val = 25000000.0 / 4096.0 / freq_hz - 1
        prescale = int(prescale_val + 0.5)
        old_mode = self.read(self.__MODE1)
        new_mode = (old_mode & 0x7F) | 0x10  # sleep
        self.write(self.__MODE1, new_mode)
        self.write(self.__PRESCALE, prescale)
        self.write(self.__MODE1, old_mode)
        time.sleep(0.005)
        self.write(self.__MODE1, old_mode | 0x80)  # restart

    def set_pwm(self, channel, on, off):
        """设置某通道的 PWM 输出"""
        base = self.__LED0_ON_L + 4 * channel
        self.write(base, on & 0xFF)
        self.write(base + 1, on >> 8)
        self.write(base + 2, off & 0xFF)
        self.write(base + 3, off >> 8)

    def set_all_pwm(self, on, off):
        self.write(0xFA, on & 0xFF)
        self.write(0xFB, on >> 8)
        self.write(0xFC, off & 0xFF)
        self.write(0xFD, off >> 8)


pwm = PCA9685()
pwm.set_pwm_freq(500)  # 50Hz，舵机常用频率


def set_brightness(left: int, right: int):
    """
    控制灯的亮度。
    :param brightness_percent: 亮度百分比 (0-100)
    """
    left = max(0, min(100, left))  # 限制范围
    pwm_max = 4095  # 12-bit 最大值
    left = int(pwm_max * (left / 100))
    pwm.set_pwm(0, 0, left)

    right = max(0, min(100, right))  # 限制范围
    right = int(pwm_max * (right / 100))
    pwm.set_pwm(1, 0, right)


if __name__ == "__main__":
    for i in range(0, 101, 10):
        set_brightness(i, i)
        time.sleep(1.5)
    set_brightness(0, 0)
    time.sleep(1)
