#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

#define SERVICE_UUID "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHAR_UUID    "beb5483e-36e1-4688-b7f5-ea07361b26a8"

const int NUM_FLEX  = 11;
const int NUM_PRESS = 6;
unsigned long connectedAt = 0;   // global

BLEServer *server;
BLECharacteristic *characteristic;

class Callbacks : public BLEServerCallbacks {
  void onConnect(BLEServer *s) {
    Serial.println("Client connected");
  }
  void onDisconnect(BLEServer *s) {
    Serial.println("Client disconnected, advertising again");
    s->startAdvertising();   // allow reconnect
  }
};

void setup() {
  Serial.begin(115200);

  BLEDevice::init("ESP32-BLE");
  BLEDevice::setMTU(247);   // allow packets bigger than 20 bytes

  server = BLEDevice::createServer();
  server->setCallbacks(new Callbacks());

  BLEService *service = server->createService(SERVICE_UUID);
  characteristic = service->createCharacteristic(
      CHAR_UUID,
      BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY);
  characteristic->addDescriptor(new BLE2902());   // lets clients enable notifications

  service->start();
  server->getAdvertising()->addServiceUUID(SERVICE_UUID);
  server->startAdvertising();

  Serial.println("BLE advertising as ESP32-BLE");
}

void loop() {
  if (server->getConnectedCount() > 0 && millis() - connectedAt > 4000) {
    float t = millis() / 1000.0;
    String msg = "";

    // 11 flex channels: smooth open/close motion, each offset a bit
    for (int i = 0; i < NUM_FLEX; i++) {
      float curl = 0.5 + 0.5 * sin(t * 0.8 + i * 0.6);     // 0 = straight, 1 = bent
      int v = 1500 + (int)(curl * 1500) + random(-20, 21);  // ~1500 to 3000 plus noise
      msg += String(constrain(v, 0, 4095)) + ",";
    }

    // 6 contact channels: mostly near 0, occasionally "touching"
    for (int j = 0; j < NUM_PRESS; j++) {
      bool touching = sin(t * 0.5 + j * 1.1) > 0.6;
      int v = touching ? 3000 + random(-100, 101) : random(0, 50);
      msg += String(v);
      if (j < NUM_PRESS - 1) msg += ",";
    }

    characteristic->setValue(msg.c_str());
    characteristic->notify();
    Serial.println(msg);
  }
  delay(50);   // about 20 packets per second
}