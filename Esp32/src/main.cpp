#include <array>
#include <WiFi.h>
#include <HTTPClient.h>

#include "EPD_Core.h"

inline constexpr unsigned long long uS_TO_S_FACTOR = 1000000ULL; /* Conversion factor for micro seconds to seconds */
inline constexpr uint8_t MIN_SLEEP = 30;                         /* Time ESP32 will go to sleep (in seconds) */

RTC_DATA_ATTR int sleepInterval = 0; /* day of the month, used for checking if was powered off, and sets currentCycle */

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
    const int maxTime = 10;
    int count = 0;

    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    while (WiFi.status() != WL_CONNECTED && count < maxTime)
    {
        Serial.println('.');
        delay(1000);
        count++;
    }
    Serial.println();
    Serial.println(WiFi.localIP());
}

void flashLED()
{
    digitalWrite(EPD_LED_PIN, HIGH); // Turn the LED ON
    delay(100);
    digitalWrite(EPD_LED_PIN, LOW); // Turn the LED OFF
}

void fetchSleepHeader(const char *url)
{
    HTTPClient http;

    Serial.println("Connecting to URL: ");
    Serial.println(url);
    http.begin(url);

    if (int httpCode = http.GET(); httpCode != HTTP_CODE_OK)
    {
        Serial.printf("HTTP GET failed, code %d\n", httpCode);
        http.end();
    }

    if (int contentLength = http.getSize(); contentLength <= 0)
    {
        Serial.println("Missing Content-Length; cannot use this method");
        http.end();
        return;
    }

    WiFiClient *stream = http.getStreamPtr();

    int newSleepTime = 0;
    Serial.println("Start, Get Sleep Bytes");
    std::array<uint16_t, 3> toSeconds = {3600, 60, 1};
    for (size_t i = 0; i < 3; i++)
    {
        if (stream->available())
        {
            int c = stream->read();
            if (c < 0)
                break;
            newSleepTime += (uint8_t)c * toSeconds[i];
        }
        else
        {
            delay(1);
        }
    }
    sleepInterval = newSleepTime;
    Serial.println("End, Got Sleep Bytes");

    http.end();
}

void fetchAndLoadPart(const char *url, uint8_t CS_PIN)
{
    HTTPClient http;

    Serial.println("Connecting to URL: ");
    Serial.println(url);
    http.begin(url);

    if (int httpCode = http.GET(); httpCode != HTTP_CODE_OK)
    {
        Serial.printf("HTTP GET failed, code %d\n", httpCode);
        http.end();
    }

    int contentLength = http.getSize();

    if (contentLength <= 0)
    {
        Serial.println("Missing Content-Length; cannot use this method");
        http.end();
        return;
    }

    WiFiClient *stream = http.getStreamPtr();

    digitalWrite(EPD_DC_PIN, LOW);
    digitalWrite(CS_PIN, LOW);
    DEV_SPI_WriteByte(0x10);
    digitalWrite(EPD_DC_PIN, HIGH);

    size_t received = 0;
    while (http.connected() && received < contentLength)
    {
        if (stream->available())
        {
            int c = stream->read();
            if (c < 0)
                break;
            DEV_SPI_WriteByte((uint8_t)c);
            received++;
        }
        else
        {
            delay(1);
        }
    }
    digitalWrite(CS_PIN, HIGH);
    digitalWrite(EPD_DC_PIN, LOW);
    http.end();

    Serial.println(received == contentLength ? "Image Buffer Load Successful" : "Image Buffer Load Failed");
}

void completeImageLoad(const char *url)
{
    HTTPClient http;

    Serial.println("Connecting to URL: ");
    Serial.println(url);
    http.begin(url);
    http.POST(DEVICE_ID);
    http.end();
}

void handleSleepLogic()
{
    /*
    Configure the wake up source
    We set our ESP32 to wake up every every interval or sleep long over night
    */
    int sleepTime = sleepInterval | MIN_SLEEP;

    esp_sleep_enable_timer_wakeup(sleepTime * uS_TO_S_FACTOR);
    Serial.println("Setup ESP32 to sleep for " + String(sleepTime) + " Seconds");

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
}

void setup()
{
#ifdef EPD_E133
    flashLED();
#endif
    // Init GPIO Pins
    DEV_Module_Init();
    delay(500);

    // Print the wakeup reason for ESP32
    print_wakeup_reason();

    Serial.println("EPD Init...");
    EPD_Init();

    Serial.println("Connecting to WiFi...");
    initWiFi();

    // get sleep header and load image on the server
    Serial.println("Get Sleep and load image on Server");
#ifdef EPD_E133
    flashLED();
#endif
    fetchSleepHeader(SERVER_HOST "/v2/GetFrameHeaders/" DEVICE_ID);

    Serial.println("Display Image");
#ifdef EPD_E133
    flashLED();
#endif
    fetchAndLoadPart(SERVER_HOST "/v2/GetFrameImage/" DEVICE_ID "/part/0", EPD_CS_PIN);
#ifdef EPD_E133
    flashLED();
    fetchAndLoadPart(SERVER_HOST "/v2/GetFrameImage/" DEVICE_ID "/part/1", EPD_CS2_PIN);
    flashLED();
#endif
    completeImageLoad(SERVER_HOST "/v2/CompleteFrameImage/" DEVICE_ID);
    WiFi.mode(WIFI_OFF);

#ifdef EPD_E133
    flashLED();
#endif
    // Make the panel actually display image
    EPD_TurnOnDisplay();

    // close 5V
    Serial.println("close 5V, Module enters 0 power consumption ...");
    DEV_Module_Exit();

    Serial.println("Program Complete!");

#ifdef EPD_E133
    flashLED();
#endif
    handleSleepLogic();
    Serial.println("This will never be printed");
}

void loop()
{
    // nothing
}
