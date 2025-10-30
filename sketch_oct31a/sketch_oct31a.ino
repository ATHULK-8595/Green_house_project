#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_SHT31.h>

const char* ssid = "motog32";
const char* password = "9988776655";
const char* serverUrl = "http://10.208.83.119:1234/api/sensor_data";

// Pin definitions as before
const int MOISTURE_PIN = 34;
const int RAIN_ANALOG_PIN = 35;
const int RAIN_DIGITAL_PIN = 18;
const int WINDOW_RELAY_PIN = 2;
const int WATER_RELAY_PIN = 4;

const float TEMP_HIGH_THRESHOLD = 28.0;
const int MOISTURE_LOW_THRESHOLD = 2500;
const int RELAY_ON = LOW;  // Active LOW relay
const int RELAY_OFF = HIGH;

Adafruit_SHT31 sht31 = Adafruit_SHT31();

struct SensorData {
  float temperature;
  float humidity;
  int moisture;
  int rainAnalog;
  int rainDigital;
  String relayWindow;
  String relayWater;
} currentData;

SemaphoreHandle_t dataMutex;

void taskSensorAndRelay(void *pvParameters) {
  for (;;) {
    float temperature = sht31.readTemperature();
    float humidity = sht31.readHumidity();
    int moisture = analogRead(MOISTURE_PIN);
    int rainAnalog = analogRead(RAIN_ANALOG_PIN);
    int rainDigital = digitalRead(RAIN_DIGITAL_PIN);

    String relayWindowState = (temperature > TEMP_HIGH_THRESHOLD) ? "ON" : "OFF";
    String relayWaterState = (moisture > MOISTURE_LOW_THRESHOLD && rainDigital != LOW) ? "ON" : "OFF";

    digitalWrite(WINDOW_RELAY_PIN, (relayWindowState == "ON") ? RELAY_ON : RELAY_OFF);
    digitalWrite(WATER_RELAY_PIN, (relayWaterState == "ON") ? RELAY_ON : RELAY_OFF);

    xSemaphoreTake(dataMutex, portMAX_DELAY);
    currentData = {temperature, humidity, moisture, rainAnalog, rainDigital, relayWindowState, relayWaterState};
    xSemaphoreGive(dataMutex);

    vTaskDelay(pdMS_TO_TICKS(1000));  // Every second
  }
}

void taskSendData(void *pvParameters) {
  for (;;) {
    SensorData dataCopy;
    xSemaphoreTake(dataMutex, portMAX_DELAY);
    dataCopy = currentData;
    xSemaphoreGive(dataMutex);

    if (WiFi.status() == WL_CONNECTED) {
      HTTPClient http;
      http.begin(serverUrl);
      http.addHeader("Content-Type", "application/json");
      DynamicJsonDocument doc(256);
      doc["temperature"] = dataCopy.temperature;
      doc["humidity"] = dataCopy.humidity;
      doc["moisture"] = dataCopy.moisture;
      doc["rain_analog"] = dataCopy.rainAnalog;
      doc["rain_digital"] = dataCopy.rainDigital;
      doc["relay_window"] = dataCopy.relayWindow;
      doc["relay_water"] = dataCopy.relayWater;
      String json;
      serializeJson(doc, json);
      http.POST(json);
      http.end();
    }
    vTaskDelay(pdMS_TO_TICKS(5000));  // Every 5 seconds
  }
}

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
  Wire.begin(21, 22);
  sht31.begin(0x44);
  pinMode(MOISTURE_PIN, INPUT);
  pinMode(RAIN_ANALOG_PIN, INPUT);
  pinMode(RAIN_DIGITAL_PIN, INPUT);
  pinMode(WINDOW_RELAY_PIN, OUTPUT);
  pinMode(WATER_RELAY_PIN, OUTPUT);
  dataMutex = xSemaphoreCreateMutex();

  xTaskCreatePinnedToCore(taskSensorAndRelay, "SensorRelay", 4096, NULL, 1, NULL, 0);
  xTaskCreatePinnedToCore(taskSendData, "SendData", 4096, NULL, 1, NULL, 1);
}

void loop() {}
