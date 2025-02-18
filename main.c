#include <avr/io.h>
#include <avr/interrupt.h>



uint8_t Databuffer[32]="hallihallo";

uint8_t UART_RxBufferA[32];
uint8_t UART_RxBufferB[32];


/****************************************************************
 * SPI                                                          *
 ****************************************************************/
#define DrvSPI_ACK 0x01
#define DrvSPI_NACK 0x02
typedef enum {
    WAIT_FOR_CMD,
    WAIT_FOR_DATALEN,
    WAIT_FOR_DATA
} e_SPI_STATES;
typedef enum {
    CMD_NONE=0,
    CMD_READ_DATA=1
} e_SPI_COMMANDS;

volatile uint8_t DrvSPI_Datalen;
volatile uint8_t* pDrvSPI_Data;
volatile e_SPI_STATES DrvSPI_State;

void DrvSPI_SlaveInit()
{
    DDRB |= _BV(PB6);
    SPCR = _BV(SPIE) | _BV(SPE);
    DrvSPI_State = WAIT_FOR_CMD;
}

/****************************************************************
 * MAIN                                                         *
 ****************************************************************/

int main(void)
{
    uint8_t test=0;
    DrvSPI_SlaveInit();
    sei();

    while(1)
        test++;
}

ISR(SPI_STC_vect)
{
    if(DrvSPI_State==WAIT_FOR_DATALEN)
    {
        DrvSPI_Datalen = SPDR;
        DrvSPI_State = WAIT_FOR_DATA;
    }
    if(DrvSPI_State==WAIT_FOR_DATA)
    {
        if(DrvSPI_Datalen)
            DrvSPI_Datalen--;
        else
            DrvSPI_State = WAIT_FOR_CMD;
        SPDR = *pDrvSPI_Data;
        pDrvSPI_Data++;
        return;
    }
    if(DrvSPI_State==WAIT_FOR_CMD)
    {
        if((e_SPI_COMMANDS)SPDR == CMD_READ_DATA)
        {
            pDrvSPI_Data = Databuffer;
            DrvSPI_State = WAIT_FOR_DATALEN;
            SPDR = DrvSPI_ACK;
        }
        else
        {
            SPDR = DrvSPI_NACK;
            DrvSPI_State = WAIT_FOR_CMD;
        }
    }
}