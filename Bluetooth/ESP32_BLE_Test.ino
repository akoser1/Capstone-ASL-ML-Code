#include <BLEDevice.h>
#include <BLEServer.h>

#define SERVICE_UUID "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHAR_UUID    "beb5483e-36e1-4688-b7f5-ea07361b26a8"

BLEServer *server;
BLECharacteristic *characteristic;
int counter = 0;

class Callbacks : public BLEServerCallbacks {
  void onDisconnect(BLEServer *s) { s->startAdvertising(); }  // allow reconnect
};

void setup() {
  Serial.begin(115200);
  BLEDevice::init("ESP32-BLE");
  server = BLEDevice::createServer();
  server->setCallbacks(new Callbacks());

  BLEService *service = server->createService(SERVICE_UUID);
  characteristic = service->createCharacteristic(
      CHAR_UUID, BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY);
  service->start();
  server->getAdvertising()->addServiceUUID(SERVICE_UUID);
  server->startAdvertising();
  Serial.println("BLE advertising");
}

void loop() {
  if (server->getConnectedCount() > 0) {
    String msg = "Packet " + String(counter++);
    characteristic->setValue(msg.c_str());
    characteristic->notify();              // push the packet to the phone
    Serial.println(msg);
  }
  delay(1000);
}