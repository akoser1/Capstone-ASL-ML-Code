#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

#define SERVICE_UUID "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHAR_UUID    "beb5483e-36e1-4688-b7f5-ea07361b26a8"

// GPIO numbers (VP = GPIO36, VN = GPIO39)
// NOTE: GPIO12 is a strapping pin; consider moving it to GPIO4 or GPIO13.
const int FLEX_PINS[] = {36, 39, 34, 35, 32, 33, 25, 26, 27, 14, 13};
const int NUM_FLEX = sizeof(FLEX_PINS) / sizeof(FLEX_PINS[0]);

const int SAMPLES = 8;                      // averaging per channel
const unsigned long SEND_DELAY_MS = 4000;   // wait after connect for service discovery
const unsigned long PERIOD_MS = 50;         // about 20 packets per second

BLEServer *server;
BLECharacteristic *characteristic;
unsigned long connectedAt = 0;
unsigned long lastSend = 0;

class Callbacks : public BLEServerCallbacks {
  void onConnect(BLEServer *s) {
    connectedAt = millis();
    Serial.println("Client connected");
  }
  void onDisconnect(BLEServer *s) {
    Serial.println("Client disconnected, advertising again");
    s->startAdvertising();
  }
};

int readFlex(int pin) {
  long sum = 0;
  for (int i = 0; i < SAMPLES; i++) sum += analogRead(pin);
  return sum / SAMPLES;
}

void setup() {
  Serial.begin(115200);

  analogReadResolution(12);          // 0 to 4095
  analogSetAttenuation(ADC_11db);    // about 0 to 3.1 V usable range
  for (int i = 0; i < NUM_FLEX; i++) pinMode(FLEX_PINS[i], INPUT);

  BLEDevice::init("ESP32-BLE");
  BLEDevice::setMTU(247);            // must come after init

  server = BLEDevice::createServer();
  server->setCallbacks(new Callbacks());

  BLEService *service = server->createService(SERVICE_UUID);
  characteristic = service->createCharacteristic(
      CHAR_UUID,
      BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY);
  characteristic->addDescriptor(new BLE2902());

  service->start();
  server->getAdvertising()->addServiceUUID(SERVICE_UUID);
  server->startAdvertising();

  Serial.println("BLE advertising as ESP32-BLE");
}

void loop() {
  unsigned long now = millis();

  if (server->getConnectedCount() > 0 &&
      now - connectedAt > SEND_DELAY_MS &&
      now - lastSend >= PERIOD_MS) {
    lastSend = now;

    char buf[80];
    int len = 0;
    for (int i = 0; i < NUM_FLEX; i++) {
      len += snprintf(buf + len, sizeof(buf) - len, "%d%s",
                      readFlex(FLEX_PINS[i]), (i < NUM_FLEX - 1) ? "," : "");
    }

    characteristic->setValue((uint8_t *)buf, len);
    characteristic->notify();
    Serial.println(buf);
  }
}
