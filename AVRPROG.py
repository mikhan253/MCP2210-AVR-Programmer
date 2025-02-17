from intelhex import IntelHex16bit
from mcp2210 import Mcp2210, Mcp2210GpioDesignation, Mcp2210GpioDirection
import time
import argparse

AVR_VARIANTS = {
    0x1e9502: {
        "desc":                 "ATmega32",
        "erase_time":           0.009,
        "flash_size_wd":        16*1024,
        "flash_page_size_wd":   64,
        "flash_no_pages":       256,
        "eeprom_size":          1024,
        "eeprom_page_size":     4,
        "eeprom_no_pages":      256,
        },
}
AVR_PROG_ENABLE = bytes((0b10101100,0b01010011,0,0))
def AVR_READ_SIGNATURE(adr):
    return bytes((0b00110000, 0, adr, 0))
AVR_READ_FUSEL = bytes((0b01010000,0b00000000,0,0))
AVR_READ_FUSEH = bytes((0b01011000,0b00001000,0,0))
AVR_CHIP_ERASE = bytes((0b10101100,0b10000000,0,0)) 
def AVR_LOAD_PROG_MEMORY(lh, adr, data):
    if lh=='h':
        return bytes((0b01001000, 0, adr, data))
    if lh=='l':
        return bytes((0b01000000, 0, adr, data))
def AVR_WRITE_PROG_MEMORY(page):
    return bytes((0b01001100, page >> 2, (page & 0b11) << 6, 0))
def AVR_READ_PROG_MEMORY(lh, adr):
    if lh=='h':
        return bytes((0b00101000, adr >> 8, adr & 0xff, 0))
    if lh=='l':
        return bytes((0b00100000, adr >> 8, adr & 0xff, 0))
def AVR_WRITE_FUSEL(val):
    return bytes((0b10101100,0b10100000,0,val))
def AVR_WRITE_FUSEH(val):
    return bytes((0b10101100,0b10101000,0,val))

def is_valid_hex_8bit(hex_string):
    if not hex_string.startswith("0x"):
        return False
    hex_part = hex_string[2:]
    if len(hex_part) > 2 or not all(c in "0123456789abcdefABCDEF" for c in hex_part):
        return False
    return True

def reset_mcu():
    global mcp
    mcp.set_gpio_output_value(2,False)
    mcp.gpio_update()
    time.sleep(0.01)
    mcp.set_gpio_output_value(2,True)
    mcp.gpio_update()
    time.sleep(0.01)
    mcp.set_gpio_output_value(2,False)
    mcp.gpio_update()
    time.sleep(0.03)

def spi_exchange(data):
    global mcp
    return mcp.spi_exchange(data,cs_pin_number=0)


parser = argparse.ArgumentParser(description='AVR Programming Interface')
parser.add_argument('--fuseh', '-fh', nargs=1, help='Write to FUSEH')
parser.add_argument('--fusel', '-fl', nargs=1, help='Write to FUSEL')
parser.add_argument('--flash-write', '-w', nargs=1, help='Write Flash')
parser.add_argument('--flash-read', '-r', nargs=1, help='Read Flash')
#parser.add_argument('-ew', action='store_true', help='Write EEPROM')
#parser.add_argument('-er', action='store_true', help='Read EEPROM')
args = parser.parse_args()

############ INIT USB SPI ############
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

############ INIT AVR SPI BOOTLOADER ############
reset_mcu()

if spi_exchange(AVR_PROG_ENABLE)[2] != 0x53:
    raise Exception("Synchronisation Error")

signature = []
for x in range(3):
    signature.append(spi_exchange(AVR_READ_SIGNATURE(x))[3])
signature=int.from_bytes(signature)
print(f"SIGNATURE={hex(signature)} -> {AVR_VARIANTS[signature]['desc']}")

if args.fusel:
    if not is_valid_hex_8bit(args.fusel[0]):
        raise Exception("Error, format of HEX-Byte should be for example 0xff")
    fuse_low = int(args.fusel[0], 16)
    print(f"Write FUSEL to {hex(fuse_low)}")
    spi_exchange(AVR_WRITE_FUSEL(fuse_low))

if args.fuseh:
    if not is_valid_hex_8bit(args.fuseh[0]):
        raise Exception("Error, format of HEX-Byte should be for example 0xff")
    fuse_high = int(args.fuseh[0], 16)
    print(f"Write FUSEH to {hex(fuse_high)}")
    spi_exchange(AVR_WRITE_FUSEH(fuse_high))

fuse_low = spi_exchange(AVR_READ_FUSEL)[3]
fuse_high = spi_exchange(AVR_READ_FUSEH)[3]
print(f"FUSEL={hex(fuse_low)} FUSEH={hex(fuse_high)}")

if args.flash_write:
    print(f"Open File {args.flash_write[0]}")
    hexfile = IntelHex16bit(args.flash_write[0])

    print("Chip Erase...")
    spi_exchange(AVR_CHIP_ERASE)
    time.sleep(AVR_VARIANTS[signature]['erase_time'])

    writeblock = {}

    for page in range(AVR_VARIANTS[signature]['flash_no_pages']):
        pagedata = []
        for addr in range(  AVR_VARIANTS[signature]['flash_page_size_wd'] * page,
                            AVR_VARIANTS[signature]['flash_page_size_wd'] * page + AVR_VARIANTS[signature]['flash_page_size_wd']):
            pagedata.append(hexfile[addr])
        if sum(pagedata) != 0xffff * AVR_VARIANTS[signature]['flash_page_size_wd']: #Nur befüllte Pages speichern
            writeblock[page] = pagedata

    for page, data in writeblock.items():
        while data[-1] == 0xffff: #Page bereinigen
            data.pop()
        print(f"Write Page {page}...")
        addr = 0
        for word in data:
            bytel, byteh = word.to_bytes(2,'little')
            #print(f"page[{page}] adr[{addr}] = {hex(word)} --> {hex(bytel)} {hex(byteh)}")
            spi_exchange(AVR_LOAD_PROG_MEMORY('l',addr,bytel))
            spi_exchange(AVR_LOAD_PROG_MEMORY('h',addr,byteh))
            addr += 1
        spi_exchange(AVR_WRITE_PROG_MEMORY(page))

    print(f"Verify Flash...")
    verifyfailed = False
    for page, data in writeblock.items():

        addr = page * AVR_VARIANTS[signature]['flash_page_size_wd']
        for word in data:
            bytel = spi_exchange(AVR_READ_PROG_MEMORY('l',addr))[3]
            byteh = spi_exchange(AVR_READ_PROG_MEMORY('h',addr))[3]
            rword = (byteh << 8) | bytel

            if rword != word:
                print(f"Error at Address: {hex(addr)} --> read {hex(rword)} instead of {hex(word)}")
                verifyfailed = True
            addr += 1

    if(verifyfailed):
        print("Verify Flash FAIL!")

if args.flash_read:
    print(f"Open File {args.flash_read[0]}")
    hexfile = IntelHex16bit()
    for page in range(AVR_VARIANTS[signature]['flash_no_pages']):
        print(f"Read Page {page}/{AVR_VARIANTS[signature]['flash_no_pages']-1}...")
        for addr in range(  AVR_VARIANTS[signature]['flash_page_size_wd'] * page,
                            AVR_VARIANTS[signature]['flash_page_size_wd'] * page + AVR_VARIANTS[signature]['flash_page_size_wd']):
            bytel = spi_exchange(AVR_READ_PROG_MEMORY('l',addr))[3]
            byteh = spi_exchange(AVR_READ_PROG_MEMORY('h',addr))[3]
            word = (byteh << 8) | bytel
            hexfile[addr]=word
    hexfile.tofile(args.flash_read[0], format='hex')


print(f"Release RESET")
mcp.set_gpio_output_value(2,True)
mcp.gpio_update()
time.sleep(0.01)
mcp.set_gpio_output_value(2,False)
mcp.gpio_update()
time.sleep(0.01)
mcp.set_gpio_output_value(2,True)
mcp.gpio_update()

