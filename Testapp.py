from mcp2210 import Mcp2210, Mcp2210GpioDesignation, Mcp2210GpioDirection
import time

############ INIT USB SPI ############
def spi_exchange(data):
    global mcp
    return mcp.spi_exchange(data,cs_pin_number=0)

mcp = Mcp2210(serial_number="0000005544", reset_transactions_on_init = True)
mcp.configure_spi_timing(chip_select_to_data_delay=0,
                         last_data_byte_to_cs=0,
                         delay_between_bytes=0)
mcp.set_spi_mode(0)

# set all pins as GPIO
for i in range(9):
    mcp.set_gpio_designation(i, Mcp2210GpioDesignation.GPIO)
mcp.set_gpio_designation(0, Mcp2210GpioDesignation.CHIP_SELECT)
for i in (2,):
    mcp.set_gpio_direction(i, Mcp2210GpioDirection.OUTPUT)

print(f"Release RESET")
mcp.set_gpio_output_value(2,True)
mcp.gpio_update()
time.sleep(0.1)

#aufbau: cmd, len, 32 x data
for cmd in (1,1,1,0,1,1,1):
    test = bytes((cmd,32,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0))
    ret = spi_exchange(test)
    print(ret)
    time.sleep(1)

