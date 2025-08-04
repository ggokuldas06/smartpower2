#include <WiFi.h>
#include <HTTPClient.h>

// === Pins and Calibration ===
#define SENSOR_PIN 34
#define BUTTON_PIN 27

const float VREF = 3.3;
const int ADC_RESOLUTION = 4095;
const float ACS712_SENSITIVITY = 0.066;
float zeroCurrentVoltage = 2.5;

// === WiFi Configuration ===
const char* ssid = "GIRISH_2.4G";
const char* password = "9840461142#";

// === HTTPS Config ===
const char* serverUrl = "https://webhook.site/e1974774-42d3-44b3-b34f-966e36bf9236"; // Replace with actual URL

unsigned long lastPostTime = 0;
const unsigned long postInterval = 5 * 60 * 1000UL;  // 5 minutes

void setup() {
  Serial.begin(115200);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  analogReadResolution(12);

  // === Wi-Fi Setup ===
  Serial.println("Booting...");  // So you can confirm it's running
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(" connected!");

  // === Calibrate zero-current voltage ===
  long sum = 0;
  const int calibrationSamples = 1000;

  for (int i = 0; i < calibrationSamples; i++) {
    sum += analogRead(SENSOR_PIN);
    delayMicroseconds(500);
  }

  float avgADC = sum / (float)calibrationSamples;
  zeroCurrentVoltage = (avgADC / ADC_RESOLUTION) * VREF;

  Serial.print("Calibrated Zero-Current Voltage: ");
  Serial.println(zeroCurrentVoltage, 4);
}

float getRMSCurrent(int samples, int delayMicros, float &lastVoltage, float &offsetOut) {
  float sumSquares = 0;
  long sumADC = 0;

  bool simulateSpike = digitalRead(BUTTON_PIN) == LOW;

  for (int i = 0; i < samples; i++) {
    int adc = simulateSpike ? 4095 : analogRead(SENSOR_PIN);
    sumADC += adc;

    float voltage = (adc / (float)ADC_RESOLUTION) * VREF;
    float current = (voltage - zeroCurrentVoltage) / ACS712_SENSITIVITY;
    sumSquares += current * current;

    delayMicroseconds(delayMicros);
  }

  float avgADC = sumADC / (float)samples;
  lastVoltage = (avgADC / ADC_RESOLUTION) * VREF;
  offsetOut = lastVoltage - zeroCurrentVoltage;

  float meanSquare = sumSquares / samples;
  return sqrt(meanSquare);
}

void sendDataToServer(float current, float power) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected. Skipping send.");
    return;
  }

  HTTPClient http;
  http.begin(serverUrl);  // HTTPS endpoint
  http.addHeader("Content-Type", "application/json");

  String payload = "{\"current\":" + String(current, 3) + ",\"power\":" + String(power, 1) + "}";
  int httpResponseCode = http.POST(payload);

  if (httpResponseCode > 0) {
    Serial.print("POST Success: ");
    Serial.println(httpResponseCode);
  } else {
    Serial.print("POST Failed: ");
    Serial.println(http.errorToString(httpResponseCode));
  }

  http.end();
}

void loop() {
  float voltage, offset;
  float rmsCurrent = getRMSCurrent(1000, 1000, voltage, offset);
  float powerWatts = rmsCurrent * 230.0;

  int rawADC = analogRead(SENSOR_PIN);

  Serial.print("ADC: ");
  Serial.print(rawADC);
  Serial.print(" | Voltage: ");
  Serial.print(voltage, 3);
  Serial.print(" V | Offset: ");
  Serial.print(offset, 3);
  Serial.print(" V | RMS Current: ");
  Serial.print(rmsCurrent, 3);
  Serial.print(" A | Power: ");
  Serial.print(powerWatts, 1);
  Serial.println(" W");

  // === Send to Server every 5 minutes ===
  if (millis() - lastPostTime >= postInterval) {
    sendDataToServer(rmsCurrent, powerWatts);
    lastPostTime = millis();
  }

  delay(1000);
}