#include <WiFi.h>
#include <HTTPClient.h>

// #include "EPD_Test.h"
#include "EPD_7in3e.h"

#define uS_TO_S_FACTOR 1000000ULL /* Conversion factor for micro seconds to seconds */
#define TIME_TO_SLEEP 45          /* Time ESP32 will go to sleep (in seconds) */
#define WAKEUP_TIME 9             /* Time in 24 hour time */
#define SLEEP_TIME 23             /* Time in 24 hour time */

#define OVERNIGHT_TIME_SLEEP ((WAKEUP_TIME + (24 - SLEEP_TIME)) * 3600) /* calculate sleep based on schedule */
#define MAX_CYCLE_COUNT ((86400 - OVERNIGHT_TIME_SLEEP) / TIME_TO_SLEEP)

RTC_DATA_ATTR int dayNumber = 0;    /* day of the month, used for checking if was powered off, and sets currentCycle */
RTC_DATA_ATTR int currentCycle = 0; /* current cycle counter */
RTC_DATA_ATTR bool syncTime = true; /* day of the month */

const char *WIFI_SSID = "MySpectrumWiFi8A-5G";
const char *WIFI_PASS = "Flush20ing20";
const char *serverUrl = "http://192.168.86.29:8000/"; // your FastAPI endpoint

const char *ntpServer = "pool.ntp.org";    // Or another reliable NTP server
const char *timeZone = "America/New_York"; // Example for Eastern Time, including DST rules

// Frame size (must match server)
const size_t FRAME_ROWS = 800;
const size_t FRAME_COLS = 480;
const size_t PIXEL_COUNT = FRAME_ROWS * FRAME_COLS;
const size_t PACKED_SIZE = (PIXEL_COUNT + 1) / 2; // two pixels per byte

uint8_t *packedBuffer = nullptr;

int timeInSeconds(struct tm *timeinfo)
{
    int hourSeconds = timeinfo->tm_hour * 3600;
    int minuteSeconds = timeinfo->tm_min * 60;
    int seconds = timeinfo->tm_sec;
    return hourSeconds + minuteSeconds + seconds;
}

int calcCurrCycle(struct tm *timeinfo)
{
    int timeSeconds = timeInSeconds(timeinfo);

    int tmep = timeSeconds - (WAKEUP_TIME * 3600);
    return 0;
}

/*
Method to print the reason by which ESP32
has been awaken from sleep
*/
void print_wakeup_reason()
{
    esp_sleep_wakeup_cause_t wakeup_reason;

    wakeup_reason = esp_sleep_get_wakeup_cause();

    switch (wakeup_reason)
    {
    case ESP_SLEEP_WAKEUP_EXT0:
        Serial.println("Wakeup caused by external signal using RTC_IO");
        break;
    case ESP_SLEEP_WAKEUP_EXT1:
        Serial.println("Wakeup caused by external signal using RTC_CNTL");
        break;
    case ESP_SLEEP_WAKEUP_TIMER:
        Serial.println("Wakeup caused by timer");
        break;
    case ESP_SLEEP_WAKEUP_TOUCHPAD:
        Serial.println("Wakeup caused by touchpad");
        break;
    case ESP_SLEEP_WAKEUP_ULP:
        Serial.println("Wakeup caused by ULP program");
        break;
    default:
        Serial.printf("Wakeup was not caused by deep sleep: %d\n", wakeup_reason);
        break;
    }
}

void initWiFi()
{
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    Serial.print("Connecting to WiFi ..");
    while (WiFi.status() != WL_CONNECTED)
    {
        Serial.print('.');
        delay(1000);
    }
    Serial.println();
    Serial.println(WiFi.localIP());
}

bool fetchPacked(const char *url, uint8_t *outBuf, size_t outSize)
{
    HTTPClient http;
    http.begin(url);

    int httpCode = http.GET();
    if (httpCode != HTTP_CODE_OK)
    {
        Serial.printf("HTTP GET failed, code %d\n", httpCode);
        http.end();
        return false;
    }

    WiFiClient *stream = http.getStreamPtr();
    size_t received = 0;

    while (http.connected() && received < outSize)
    {
        if (stream->available())
        {
            int c = stream->read();
            if (c < 0)
                break;
            outBuf[received++] = (uint8_t)c;
        }
        else
        {
            delay(1);
        }
    }

    http.end();
    return received == outSize;
}

void doAllScreenStuff(uint8_t *buffer)
{
    Debug("Apply Power To Display");
    if (DEV_Module_Init() != 0)
    {
        return;
    }

    Debug("e-Paper Init and Clear...\r\n");
    EPD_7IN3E_Init();
    // Debug("about to clear image\r\n");
    // EPD_7IN3E_Clear(EPD_7IN3E_WHITE); // WHITE
    // DEV_Delay_ms(1000);

    Debug("Display Real Image\r\n");
    EPD_7IN3E_Display(buffer);

    Debug("Put Display to Sleep...\r\n");
    EPD_7IN3E_Sleep();
    free(buffer);
    buffer = NULL;
    delay(2000); // important, at least 2s
    // close 5V
    // Debug("close 5V, Module enters 0 power consumption ...\r\n");
    // DEV_Module_Exit();
}

void initTime()
{
    // Set the time zone and NTP server
    Debug("Sync with NTP\r\n");
    configTzTime(timeZone, ntpServer);
    struct tm timeinfo;
    if (!getLocalTime(&timeinfo))
    {
        Serial.println("Failed to obtain time");
        return;
    }
    dayNumber = timeinfo.tm_mday;
    if (timeinfo.tm_hour < WAKEUP_TIME || timeinfo.tm_hour > SLEEP_TIME)
    {
        int timeSeconds = timeInSeconds(&timeinfo);
        int sleepTime = (WAKEUP_TIME * 3600) - timeSeconds;
        if (timeinfo.tm_hour > SLEEP_TIME)
        {
            sleepTime = (86400 - timeSeconds) + (WAKEUP_TIME * 3600);
        }
        esp_sleep_enable_timer_wakeup(sleepTime * uS_TO_S_FACTOR);
    }
    currentCycle = calcCurrCycle(&timeinfo);
}

void setup()
{
    Serial.begin(115200);
    // delay(2000);

    // Print the wakeup reason for ESP32
    // print_wakeup_reason();

    initWiFi();
    // if (!dayNumber || syncTime)
    // {
    //     initTime();
    // }

    /*
    Configure the wake up source
    We set our ESP32 to wake up every every interval or sleep long over night
    */

    int sleepTime = TIME_TO_SLEEP;
    // if (currentCycle > MAX_CYCLE_COUNT)
    // {
    //     Debug("End of day Cycle\r\n");
    //     syncTime = true;
    //     Debug("Set Overnight Sleep\r\n");
    //     sleepTime = OVERNIGHT_TIME_SLEEP;
    // }

    esp_sleep_enable_timer_wakeup(sleepTime * uS_TO_S_FACTOR);
    Serial.println("Setup ESP32 to sleep for " + String(sleepTime) +
                   " Seconds");

    packedBuffer = (uint8_t *)malloc(PACKED_SIZE);
    if (!packedBuffer)
    {
        Serial.println("Failed to allocate buffer!");
        while (1)
            delay(1000);
    }

    if (fetchPacked(serverUrl, packedBuffer, PACKED_SIZE))
    {
        Serial.println("Got packed buffer!");
        // Serial.print("First 16 packed bytes: ");
        // for (int i = 0; i < 16 && i < PACKED_SIZE; i++)
        // {
        //     Serial.print(packedBuffer[i]);
        // }
        // Serial.println();

        // init display, display image, display go to sleep
        doAllScreenStuff(packedBuffer);
    }
    else
    {
        Serial.println("Failed to fetch packed buffer");
    }
    Serial.print("Program Complete!");

    /*
    Next we decide what all peripherals to shut down/keep on
    By default, ESP32 will automatically power down the peripherals
    not needed by the wakeup source, but if you want to be a poweruser
    this is for you. Read in detail at the API docs
    http://esp-idf.readthedocs.io/en/latest/api-reference/system/deep_sleep.html
    Left the line commented as an example of how to configure peripherals.
    The line below turns off all RTC peripherals in deep sleep.
    */
    // esp_deep_sleep_pd_config(ESP_PD_DOMAIN_RTC_PERIPH, ESP_PD_OPTION_OFF);
    // Serial.println("Configured all RTC Peripherals to be powered down in sleep");

    /*
    Now that we have setup a wake cause and if needed setup the
    peripherals state in deep sleep, we can now start going to
    deep sleep.
    In the case that no wake up sources were provided but deep
    sleep was started, it will sleep forever unless hardware
    reset occurs.
    */
    Serial.println("Going to sleep now");
    Serial.flush();
    esp_deep_sleep_start();
    Serial.println("This will never be printed");
}

void loop()
{
    // nothing
}
