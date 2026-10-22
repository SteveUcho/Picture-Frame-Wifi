// Steve Uchoa - EPD Core Implementation
#include <span>
#include "EPD_Core.h"

/******************************************************************************
function :  Software reset
parameter:
******************************************************************************/
static void EPD_7IN3E_Reset(void)
{
    DEV_Digital_Write(EPD_RST_PIN, 1);
    DEV_Delay_ms(20);
    DEV_Digital_Write(EPD_RST_PIN, 0);
    DEV_Delay_ms(2);
    DEV_Digital_Write(EPD_RST_PIN, 1);
    DEV_Delay_ms(20);
}

/******************************************************************************
function :  send command
parameter:
     Reg : Command register
******************************************************************************/
static void EPD_SendCommand(UBYTE Command, UBYTE CS_PIN)
{
    DEV_Digital_Write(EPD_DC_PIN, 0);
    DEV_Digital_Write(CS_PIN, 0);
    Serial.println("Send command " + (String)Command);
    DEV_SPI_WriteByte(Command);
    DEV_Digital_Write(CS_PIN, 1);
}
static void EPD_SendCommand(UBYTE Command, UBYTE CS_PIN, std::span<const uint8_t> data)
{
    DEV_Digital_Write(EPD_DC_PIN, 0);
    DEV_Digital_Write(CS_PIN, 0);
    Serial.println("Send command " + (String)Command);
    DEV_SPI_WriteByte(Command);
    DEV_Digital_Write(EPD_DC_PIN, 1);
    for (uint8_t byte : data) {
        DEV_SPI_WriteByte(byte);
    }
    DEV_Digital_Write(CS_PIN, 1);
}

/******************************************************************************
function :  send data
parameter:
    Data : Write data
******************************************************************************/
static void EPD_SendData(UBYTE Data)
{
    DEV_Digital_Write(EPD_DC_PIN, 1);
    DEV_Digital_Write(EPD_CS_PIN, 0);
    DEV_SPI_WriteByte(Data);
    DEV_Digital_Write(EPD_CS_PIN, 1);
}

/******************************************************************************
function :  Wait until the busy_pin goes LOW
parameter:
******************************************************************************/
static void EPD_BusyWait(void)
{
    Serial.print("e-Paper busy wait\r\n");
    while (!DEV_Digital_Read(EPD_BUSY_PIN))
    { // LOW: busy, HIGH: idle
        DEV_Delay_ms(1);
    }
    Serial.print("e-Paper busy wait release\r\n");
}

/******************************************************************************
*/
static void EPD_RefreshWait(void)
{
    Serial.print("e-Paper Refresh Begin\r\n");
    while (DEV_Digital_Read(EPD_BUSY_PIN))
    { // LOW: busy, HIGH: idle
        DEV_Delay_ms(1);
    }
    Serial.print("e-Paper Refresh Begin release\r\n");
    Serial.print("e-Paper Refresh End Wait\r\n");
    while (!DEV_Digital_Read(EPD_BUSY_PIN))
    { // LOW: busy, HIGH: idle
        DEV_Delay_ms(1);
    }
    Serial.print("e-Paper Refresh End Wait release\r\n");
}

/******************************************************************************
function :  Turn On Display
parameter:
******************************************************************************/
static void EPD_7IN3E_TurnOnDisplay(void)
{
    Serial.print("debug: turnon: send command\r\n");
    EPD_SendCommand(0x04, EPD_CS_PIN); // POWER_ON
    Serial.print("debug: turnon: readBusy\r\n");
    EPD_BusyWait();

    Serial.print("debug: turnon: send second command\r\n");

    EPD_SendCommand(0x06, EPD_CS_PIN, std::array<uint8_t, 4> {0x6F, 0x1F, 0x17, 0x49});

    EPD_SendCommand(0x12, EPD_CS_PIN, std::array<uint8_t, 1> {0x00}); // DISPLAY_REFRESH
    EPD_BusyWait();

    EPD_SendCommand(0x02, EPD_CS_PIN, std::array<uint8_t, 1> {0x00}); // POWER_OFF
    EPD_BusyWait();
}

/******************************************************************************
function :  Initialize the e-Paper register
parameter:
******************************************************************************/
static void EPD_7IN3E_Init(void)
{
    EPD_7IN3E_Reset();
    EPD_BusyWait();
    DEV_Delay_ms(30);

    EPD_SendCommand(0xAA, EPD_CS_PIN, std::array<uint8_t, 6> {0x49, 0x55, 0x20, 0x08, 0x09, 0x18}); // CMDH
    EPD_SendCommand(0x01, EPD_CS_PIN, std::array<uint8_t, 1> {0x3F}); //
    EPD_SendCommand(0x00, EPD_CS_PIN, std::array<uint8_t, 2> {0x5F, 0x69});

    EPD_SendCommand(0x05, EPD_CS_PIN, std::array<uint8_t, 4> {0x40, 0x1F, 0x1F, 0x2C});
    EPD_SendCommand(0x08, EPD_CS_PIN, std::array<uint8_t, 4> {0x6F, 0x1F, 0x1F, 0x22});
    EPD_SendCommand(0x06, EPD_CS_PIN, std::array<uint8_t, 4> {0x6F, 0x1F, 0x17, 0x49});

    EPD_SendCommand(0x03, EPD_CS_PIN, std::array<uint8_t, 4> {0x00, 0x54, 0x00, 0x44});
    EPD_SendCommand(0x60, EPD_CS_PIN, std::array<uint8_t, 2> {0x02, 0x00});
    EPD_SendCommand(0x30, EPD_CS_PIN, std::array<uint8_t, 1> {0x03});
    EPD_SendCommand(0x50, EPD_CS_PIN, std::array<uint8_t, 1> {0x3F});
    EPD_SendCommand(0x61, EPD_CS_PIN, std::array<uint8_t, 4> {0x03, 0x20, 0x01, 0xE0});
    EPD_SendCommand(0xE3, EPD_CS_PIN, std::array<uint8_t, 1> {0x2F});

    EPD_SendCommand(0x84, EPD_CS_PIN, std::array<uint8_t, 1> {0x01});
}

/******************************************************************************
function :  Clear screen
parameter:
******************************************************************************/
void EPD_7IN3E_Clear(void)
{
    UWORD Width = EPD_7IN3E_WIDTH / 2;
    UWORD Height = EPD_7IN3E_HEIGHT;

    Serial.print("Send command\r\n");
    EPD_SendCommand(0x10, EPD_CS_PIN);
    for (UWORD i = 0; i < Height; i++)
    {
        for (UWORD j = 0; j < Width; j++)
        {
            EPD_SendData((0x1 << 4) | 0x1);
        }
    }
    Serial.println("sent clear command");
    Serial.print("turn on display");
    EPD_7IN3E_TurnOnDisplay();
}

/******************************************************************************
function :  Sends the image buffer in RAM to e-Paper and displays
parameter:
******************************************************************************/
void EPD_7IN3E_Display(std::span<const uint8_t> Image)
{
    EPD_7IN3E_Init();

    EPD_SendCommand(0x10, EPD_CS_PIN, Image);

    EPD_7IN3E_TurnOnDisplay();
}

void EPD_7IN3E_DisplayPart(const UBYTE *Image, UWORD xstart, UWORD ystart, UWORD image_width, UWORD image_heigh)
{
    UWORD Width, Height;
    Width = (EPD_7IN3E_WIDTH % 2 == 0) ? (EPD_7IN3E_WIDTH / 2) : (EPD_7IN3E_WIDTH / 2 + 1);
    Height = EPD_7IN3E_HEIGHT;

    EPD_SendCommand(0x10, EPD_CS_PIN);
    for (uint16_t i = 0; i < Height; i++)
    {
        for (uint16_t j = 0; j < Width; j++)
        {
            if (i < image_heigh + ystart && i >= ystart && j < (image_width + xstart) / 2 && j >= xstart / 2)
            {
                EPD_SendData(Image[(j - xstart / 2) + (image_width / 2 * (i - ystart))]);
            }
            else
            {
                EPD_SendData(0x11);
            }
        }
    }
    EPD_7IN3E_TurnOnDisplay();
}

/******************************************************************************
function :  Enter sleep mode
parameter:
******************************************************************************/
void EPD_7IN3E_Sleep(void)
{
    EPD_SendCommand(0X02, EPD_CS_PIN); // DEEP_SLEEP
    EPD_SendData(0x00);
    EPD_BusyWait();

    EPD_SendCommand(0x07, EPD_CS_PIN); // DEEP_SLEEP
    EPD_SendData(0XA5);
}
