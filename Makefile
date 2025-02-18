######################################################
# Auto generated Makefile @08.12.2024 09:54:13
######################################################



PROJECT = usbmaster
CHIP = atmega32
ID = m32
TARGET = $(PROJECT).elf
TCPATH = 
CC = avr-gcc
CPP = avr-gcc
OL = O0
COMMON = -mmcu=$(CHIP)
CFLAGS = $(COMMON) -Wall -gdwarf-2 -std=gnu99 -$(OL) -funsigned-char -funsigned-bitfields -fpack-struct -fshort-enums -DF_CPU=12000000UL -DDEBUG
GENDFLAGS = 
LDFLAGS = $(COMMON) -Wl,-Map=$(PROJECT).map
HEX_FLASH_FLAGS = -R .eeprom -R .fuse -R .lock -R .singature
HEX_EEPROM_FLAGS = -j .eeprom --set-section-flags=.eeprom="alloc,load" --change-section-lma .eeprom=0 --no-change-warnings
INCLUDES =  -I./Drivers/Includes
OBJECTS =  main.o
SOBJECTS =  
EXTOBJS = 

all: clean $(TARGET) $(PROJECT).hex $(PROJECT).lss
	@echo ""
	@echo build done!


main.o : ./main.c
	$(CC) $(INCLUDES) $(GENDFLAGS) $(CFLAGS) -c ./main.c

DrvADC.o : ./Drivers/Sources/DrvADC.c
	$(CC) $(INCLUDES) $(GENDFLAGS) $(CFLAGS) -c ./Drivers/Sources/DrvADC.c


start.o : ./Drivers/Sources/start.s
	$(CC) $(INCLUDES) $(GENDFLAGS) $(CFLAGS) -x assembler-with-cpp -c ./Drivers/Sources/start.s

DrvDSU.o : ./Drivers/Sources/DrvDSU.s
	$(CC) $(INCLUDES) $(GENDFLAGS) $(CFLAGS) -x assembler-with-cpp -c ./Drivers/Sources/DrvDSU.s


$(TARGET): $(OBJECTS) $(SOBJECTS)
	$(CC) $(LDFLAGS) $(OBJECTS) $(SOBJECTS) $(EXTOBJS) $(LIBDIRS) $(LIBS) -o $(TARGET)

$(PROJECT).hex: $(TARGET)
	$(TCPATH)/avr-objcopy -O ihex $(HEX_FLASH_FLAGS) $(PROJECT).elf $(PROJECT).hex

$(PROJECT).lss: $(TARGET)
	$(TCPATH)/avr-objdump -h -S $(PROJECT).elf > $(PROJECT).lss
	@echo
	$(TCPATH)/avr-size --mcu=$(CHIP) $(TARGET)

AVRDUDE: $(PROJECT).hex
	@$(TCPATH)/avrdude -c arduino -P /dev/ttyUSB0 -p lgt8f328p -Uflash:w:$(PROJECT).hex:i

clean: 
	@rm -rf *.o *.hex *.lss *.map *.elf
	@echo cleanup done!

