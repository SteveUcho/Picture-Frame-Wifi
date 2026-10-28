// Steve Uchoa - EPD Core Implementation
#include <span>
#include "EPD_Core.h"

/******************************************************************************
function :  Software reset
parameter:
******************************************************************************/
static void EPD_Reset(void)
{
    DEV_Digital_Write(EPD_RST_PIN, 0);
    DEV_Delay_ms(30);
    DEV_Digital_Write(EPD_RST_PIN, 1);
    DEV_Delay_ms(30);
}

/******************************************************************************
function :  send command
parameter:
     Command : Command value
     CS_PIN : Chip select pin
     data : Data to send
******************************************************************************/
void EPD_SendCommand(UBYTE Command, UBYTE CS_PIN, std::span<const uint8_t> data = {})
{
    DEV_Digital_Write(EPD_DC_PIN, 0);
#ifdef EPD_E73
    DEV_Digital_Write(EPD_CS_PIN, 0);
#elif EPD_E133
    if ((CS_PIN & EPD_CS_PIN) != 0)
    {
        DEV_Digital_Write(EPD_CS_PIN, 0);
    }
    if ((CS_PIN & EPD_CS2_PIN) != 0)
    {
        DEV_Digital_Write(EPD_CS2_PIN, 0);
    }
#endif
    DEV_SPI_WriteByte(Command);
    if (!data.empty())
    {
        DEV_Digital_Write(EPD_DC_PIN, 1);
        for (uint8_t byte : data)
        {
            DEV_SPI_WriteByte(byte);
        }
    }
    DEV_Digital_Write(EPD_CS_PIN, 1);
#ifdef EPD_E133
    DEV_Digital_Write(EPD_CS2_PIN, 1);
#endif
    DEV_Digital_Write(EPD_DC_PIN, 0);
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
    Serial.println("e-Paper busy wait");
    while (!DEV_Digital_Read(EPD_BUSY_PIN))
    { // LOW: busy, HIGH: idle
        DEV_Delay_ms(1);
    }
    Serial.println("e-Paper busy wait release");
}

#ifdef EPD_E133
/******************************************************************************
function :  Wait until it goes from HIGH to LOW to HIGH
parameter:
******************************************************************************/
static void EPD_RefreshWait(void)
{
    Serial.println("e-Paper Refresh Begin");
    while (DEV_Digital_Read(EPD_BUSY_PIN))
    { // LOW: busy, HIGH: idle
        DEV_Delay_ms(1);
    }
    Serial.println("e-Paper Refresh Begin release");
    Serial.println("e-Paper Refresh End Wait");
    while (!DEV_Digital_Read(EPD_BUSY_PIN))
    { // LOW: busy, HIGH: idle
        DEV_Delay_ms(1);
    }
    Serial.println("e-Paper Refresh End Wait release");
}
#endif

/******************************************************************************
function :  Turn On Display
parameter:
******************************************************************************/
void EPD_TurnOnDisplay(void)
{
    EPD_SendCommand(0x04, EPD_CS_PIN | EPD_CS2_PIN); // POWER_ON
    EPD_BusyWait();

#ifdef EPD_E73
    Serial.println("debug: turnon: send second command");
    EPD_SendCommand(0x06, EPD_CS_PIN, std::array<uint8_t, 4>{0x6F, 0x1F, 0x17, 0x49});
#endif

    EPD_SendCommand(0x12, EPD_CS_PIN | EPD_CS2_PIN, std::array<uint8_t, 1>{0x00}); // DISPLAY_REFRESH
#ifdef EPD_E73
    EPD_BusyWait();
#elif EPD_E133
    EPD_RefreshWait();
#endif

    EPD_SendCommand(0x02, EPD_CS_PIN | EPD_CS2_PIN, std::array<uint8_t, 1>{0x00}); // POWER_OFF
    EPD_BusyWait();

#ifdef EPD_E73
    EPD_SendCommand(0x07, EPD_CS_PIN, std::array<uint8_t, 1>{0xA5}); // DEEP_SLEEP
    delay(2000);                                                     // important, at least 2s
#endif
}

/******************************************************************************
function :  Initialize the e-Paper register
parameter:
******************************************************************************/
void EPD_Init(void)
{
    EPD_Reset();
    EPD_BusyWait();

#ifdef EPD_E73
    EPD_SendCommand(0xAA, EPD_CS_PIN, std::array<uint8_t, 6>{0x49, 0x55, 0x20, 0x08, 0x09, 0x18}); // CMDH
    EPD_SendCommand(0x01, EPD_CS_PIN, std::array<uint8_t, 1>{0x3F});                               //
    EPD_SendCommand(0x00, EPD_CS_PIN, std::array<uint8_t, 2>{0x5F, 0x69});

    EPD_SendCommand(0x05, EPD_CS_PIN, std::array<uint8_t, 4>{0x40, 0x1F, 0x1F, 0x2C});
    EPD_SendCommand(0x08, EPD_CS_PIN, std::array<uint8_t, 4>{0x6F, 0x1F, 0x1F, 0x22});
    EPD_SendCommand(0x06, EPD_CS_PIN, std::array<uint8_t, 4>{0x6F, 0x1F, 0x17, 0x49});

    EPD_SendCommand(0x03, EPD_CS_PIN, std::array<uint8_t, 4>{0x00, 0x54, 0x00, 0x44});
    EPD_SendCommand(0x60, EPD_CS_PIN, std::array<uint8_t, 2>{0x02, 0x00});
    EPD_SendCommand(0x30, EPD_CS_PIN, std::array<uint8_t, 1>{0x03});
    EPD_SendCommand(0x50, EPD_CS_PIN, std::array<uint8_t, 1>{0x3F});
    EPD_SendCommand(0x61, EPD_CS_PIN, std::array<uint8_t, 4>{0x03, 0x20, 0x01, 0xE0});
    EPD_SendCommand(0xE3, EPD_CS_PIN, std::array<uint8_t, 1>{0x2F});

    EPD_SendCommand(0x84, EPD_CS_PIN, std::array<uint8_t, 1>{0x01});
#elif EPD_E133
    EPD_SendCommand(0x74, EPD_CS_PIN, std::array<uint8_t, 9>{0x00, 0x0C, 0x0C, 0xD9, 0xDD, 0xDD, 0x15, 0x15, 0x55}); // ANTM

    EPD_SendCommand(0xF0, EPD_CS_PIN | EPD_CS2_PIN, std::array<uint8_t, 6>{0x49, 0x55, 0x13, 0x5D, 0x05, 0x10}); // CMD66
    EPD_SendCommand(0x00, EPD_CS_PIN | EPD_CS2_PIN, std::array<uint8_t, 2>{0xDF, 0x6B});                         // PSR
    EPD_SendCommand(0xA5, EPD_CS_PIN, std::array<uint8_t, 3>{0x44, 0x54, 0x00});                                 // DCDC
    EPD_SendCommand(0x30, EPD_CS_PIN | EPD_CS2_PIN, std::array<uint8_t, 1>{0x08});                               // PLL
    EPD_SendCommand(0x50, EPD_CS_PIN | EPD_CS2_PIN, std::array<uint8_t, 1>{0x37});                               // CDI
    EPD_SendCommand(0x60, EPD_CS_PIN | EPD_CS2_PIN, std::array<uint8_t, 2>{0x03, 0x03});                         // TCON

    EPD_SendCommand(0x03, EPD_CS_PIN, std::array<uint8_t, 4>{0x00, 0xC0, 0x03, 0xA8});  // POFS
    EPD_SendCommand(0x03, EPD_CS2_PIN, std::array<uint8_t, 4>{0x00, 0xC0, 0x03, 0x9A}); // POFS

    EPD_SendCommand(0x86, EPD_CS_PIN | EPD_CS2_PIN, std::array<uint8_t, 1>{0x10});                   // AGID
    EPD_SendCommand(0xE3, EPD_CS_PIN | EPD_CS2_PIN, std::array<uint8_t, 1>{0x22});                   // PWS
    EPD_SendCommand(0xE0, EPD_CS_PIN | EPD_CS2_PIN, std::array<uint8_t, 1>{0x01});                   // CCSET
    EPD_SendCommand(0x61, EPD_CS_PIN | EPD_CS2_PIN, std::array<uint8_t, 4>{0x04, 0xB0, 0x03, 0x20}); // TRES

    EPD_SendCommand(0xA4, EPD_CS_PIN, std::array<uint8_t, 9>{0x03, 0x00, 0x01, 0x03, 0x00, 0x03, 0x00, 0x00, 0x00}); // CMDA4
    EPD_SendCommand(0x01, EPD_CS_PIN, std::array<uint8_t, 6>{0x0F, 0x00, 0x28, 0x2C, 0x28, 0x38});                   // PWR
    EPD_SendCommand(0xB6, EPD_CS_PIN, std::array<uint8_t, 1>{0x07});                                                 // EN_BUF
    EPD_SendCommand(0x06, EPD_CS_PIN, std::array<uint8_t, 2>{0xE0, 0x20});                                           // BTST_P
    EPD_SendCommand(0xB7, EPD_CS_PIN, std::array<uint8_t, 1>{0x01});                                                 // BOOST_VDDP_EN
    EPD_SendCommand(0x05, EPD_CS_PIN, std::array<uint8_t, 2>{0xE0, 0x20});                                           // BTST_N
    EPD_SendCommand(0xB0, EPD_CS_PIN, std::array<uint8_t, 1>{0x01});                                                 // BUCK_BOOST_VDDN
    EPD_SendCommand(0xB1, EPD_CS_PIN, std::array<uint8_t, 1>{0x02});                                                 // TFT_VCOM_POWER
#endif
}

/******************************************************************************
function :  Clear screen
parameter:
******************************************************************************/
void EPD_Clear(void)
{
    UWORD Width = EPD_7IN3E_WIDTH / 2;
    UWORD Height = EPD_7IN3E_HEIGHT;

    Serial.println("Send command");
    EPD_SendCommand(0x10, EPD_CS_PIN);
    for (UWORD i = 0; i < Height; i++)
    {
        for (UWORD j = 0; j < Width; j++)
        {
            EPD_SendData((0x1 << 4) | 0x1);
        }
    }
    Serial.println("sent clear command");
    Serial.println("turn on display");
    EPD_TurnOnDisplay();
}

/******************************************************************************
function :  Sends the image buffer in RAM to e-Paper and displays
parameter:
    Image : Image data to display
******************************************************************************/
void EPD_Display(std::span<const uint8_t> Image)
{
    EPD_Init();

#ifdef EPD_E73
    EPD_SendCommand(0x10, EPD_CS_PIN, Image);
#elif EPD_E133
    // half the image to each side
    EPD_SendCommand(0x10, EPD_CS_PIN, Image.subspan(0, Image.size() / 2));
    EPD_SendCommand(0x10, EPD_CS2_PIN, Image.subspan(Image.size() / 2));
#endif

    EPD_TurnOnDisplay();
}

void EPD_7IN3E_DisplayPart(const UBYTE *Image, UWORD xstart, UWORD ystart, UWORD image_width, UWORD image_heigh)
{
    UWORD Width = (EPD_7IN3E_WIDTH % 2 == 0) ? (EPD_7IN3E_WIDTH / 2) : (EPD_7IN3E_WIDTH / 2 + 1);
    UWORD Height = EPD_7IN3E_HEIGHT;

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
    EPD_TurnOnDisplay();
}
