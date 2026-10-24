/*****************************************************************************
* | File      	:   DEV_Config.h
* | Author      :   Waveshare team, Steve Ucho
* | Function    :   Hardware underlying interface
* | Info        :
*----------------
* |	This version:   V1.0
* | Date        :   2026-10-21
* | Info        :
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documnetation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to  whom the Software is
# furished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
******************************************************************************/
#ifndef _DEV_CONFIG_H_
#define _DEV_CONFIG_H_

#include <Arduino.h>
#include <stdint.h>
#include <stdio.h>
#include <SPI.h>

/**
 * data
 **/
using UBYTE = uint8_t;
using UWORD = uint16_t;
using UDOUBLE = uint32_t;

/**
 * GPIO config
 **/

// GPIO Right Side
// also connected is pwr to 3.3v
inline constexpr UBYTE EPD_MOSI_PIN = D10;
inline constexpr UBYTE EPD_SCK_PIN = D8;
inline constexpr UBYTE EPD_PWR_PIN = D0;

// GPIO Left Side
inline constexpr UBYTE EPD_CS_PIN = D3;
inline constexpr UBYTE EPD_CS2_PIN = D2;
inline constexpr UBYTE EPD_DC_PIN = D4;
inline constexpr UBYTE EPD_RST_PIN = D5;
inline constexpr UBYTE EPD_BUSY_PIN = D6;

// GPIO MISC
inline constexpr UBYTE GPIO_PIN_SET = 1;
inline constexpr UBYTE GPIO_PIN_RESET = 0;

/**
 * GPIO read and write
 **/
#define DEV_Digital_Write(_pin, _value) digitalWrite(_pin, _value == 0 ? LOW : HIGH)
#define DEV_Digital_Read(_pin) digitalRead(_pin)

/**
 * delay x ms
 **/
#define DEV_Delay_ms(__xms) delay(__xms)

/*------------------------------------------------------------------------------------------------------*/
UBYTE DEV_Module_Init(void);
void DEV_GPIO_Init(void);
void DEV_SPI_Init(void);

void GPIO_Mode(UBYTE GPIO_Pin, UBYTE Mode);
void DEV_SPI_WriteByte(UBYTE data);
void DEV_SPI_SendByte(UBYTE data);
UBYTE DEV_SPI_ReadByte();
void DEV_SPI_Write_nByte(UBYTE *pData, UDOUBLE len);
void DEV_Module_Exit(void);
#endif
