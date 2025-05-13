import math
import time
from .base import i2c
import struct



# 设置四路电机驱动模块的I2C地址
MOTOR_ADDR = 0x34

# 寄存器地址
ADC_BAT_ADDR = 0x00
MOTOR_TYPE_ADDR = 0x14  # 编码电机类型设置
MOTOR_ENCODER_POLARITY_ADDR = 0x15  # 设置编码方向极性，
# 如果发现电机转速根本不受控制，要么最快速度转动，要么停止。可以将此地址的值重新设置一下
# 范围0或1，默认0
MOTOR_FIXED_PWM_ADDR = 0x1F  # 固定PWM控制，属于开环控制,范围（-100~100）
MOTOR_FIXED_SPEED_ADDR = 0x33  # 固定转速控制，属于闭环控制，
# 单位：脉冲数每10毫秒，范围（根据具体的编码电机来，受编码线数，电压大小，负载大小等影响，一般在±50左右）

MOTOR_ENCODER_TOTAL_ADDR = 0x3C  # 4个编码电机各自的总脉冲值
# #如果已知电机每转一圈的脉冲数为U，又已知轮子的直径D，那么就可以通过脉冲计数的方式得知每个轮子行进的距离
# #比如读到电机1的脉冲总数为P，那么行进的距离为(P/U) * (3.14159*D)
# #对于不同的电机可以自行测试每圈的脉冲数U，可以手动旋转10圈读出脉冲数，然后取平均值得出


# 电机类型具体值
MOTOR_TYPE_WITHOUT_ENCODER = 0
MOTOR_TYPE_TT = 1
MOTOR_TYPE_N20 = 2
MOTOR_TYPE_JGB37_520_12V_110RPM = 3  # 磁环每转是44个脉冲   减速比:90  默认

# 电机类型及编码方向极性
MotorType = MOTOR_TYPE_JGB37_520_12V_110RPM
MotorEncoderPolarity = 1

bus = i2c
def _motor_init():  # 电机初始化
    print("motor_init")
    bus.write_byte_data(MOTOR_ADDR, MOTOR_TYPE_ADDR, MotorType)  # 设置电机类型
    time.sleep(0.5)
    # 设置编码极性
    bus.write_byte_data(MOTOR_ADDR, MOTOR_ENCODER_POLARITY_ADDR, MotorEncoderPolarity)
    # 清零编码器
    bus.write_i2c_block_data(MOTOR_ADDR, MOTOR_ENCODER_TOTAL_ADDR, [0] * 16)
    # 速度清零
    bus.write_i2c_block_data(MOTOR_ADDR, MOTOR_FIXED_SPEED_ADDR, [0] * 4)


# 获取电压
def get_battery_v():
    battery = bus.read_i2c_block_data(MOTOR_ADDR, ADC_BAT_ADDR, 2)
    return (battery[0] + (battery[1] << 8)) / 1000.0


_motor_init()


# 固定参数（编码器与轮子参数）
ENCODER_PULSES_PER_REV: int = 44         # 电机轴每圈脉冲数
GEAR_RATIO: int = 45                     # 减速比
WHEEL_DIAMETER_MM: float = 54.0          # 轮子直径（单位：mm）

# 推导值
PULSES_PER_WHEEL_REV: int = ENCODER_PULSES_PER_REV * GEAR_RATIO
WHEEL_CIRCUMFERENCE_MM: float = math.pi * WHEEL_DIAMETER_MM  # ≈ 172.8 mm

def speed_to_setting(speed_mm_per_s: float) -> int:
    """
    将目标线速度（mm/s）转换为速度设定值（单位：脉冲数 / 10ms）

    参数:
        speed_mm_per_s (float): 目标速度（单位 mm/s）

    返回:
        int: 驱动板要求的速度设定值（单位：脉冲数 / 10ms）
    """
    pulses_per_second: float = (speed_mm_per_s / WHEEL_CIRCUMFERENCE_MM) * PULSES_PER_WHEEL_REV
    return round(pulses_per_second / 100)

def walk(left: float, right: float):
    """
    控制电机行走
    :param left: 左电机速度，范围[-400, 400]
    :param right: 右电机速度，范围[-400, 400]
    """
    #输入电压
    voltage = get_battery_v()
    print("V = {0}mV".format(voltage))
    print("left: ", left, " right: ", right)
    left = speed_to_setting(left)  # 转换为脉冲数 / 10ms
    right = speed_to_setting(right)  # 转换为脉冲数 / 10ms
    MAX_SPEED = 30
    # 限制速度范围
    left = max(-MAX_SPEED, min(MAX_SPEED, left))
    right = max(-MAX_SPEED, min(MAX_SPEED, right))
    print("left2: ", left, " right2: ", right)
    # 计算速度值
    bus.write_i2c_block_data(MOTOR_ADDR, MOTOR_FIXED_SPEED_ADDR,[int(left), int(right), 0, 0])

if __name__ == "__main__":
    # 测试代码
    walk(0, 0)
    time.sleep(1)
    walk(300, 300)
    # time.sleep(1)
    # walk(-100, -100)
    time.sleep(3)
    walk(0, 0)
    
