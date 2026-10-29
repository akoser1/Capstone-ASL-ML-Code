#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include <Wire.h>

// Set to 1 once the BNO085 is wired and "Adafruit BNO08x" is installed via Library Manager.
#define USE_IMU 0

#if USE_IMU
#include <Adafruit_BNO08x.h>
#endif

#define SERVICE_UUID "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHAR_UUID    "beb5483e-36e1-4688-b7f5-ea07361b26a8"

// ---------- Pins (GPIO numbers) ----------
const int MUX_COM = 34;                       // mux output -> ADC1
const int MUX_S0 = 26, MUX_S1 = 25, MUX_S2 = 4;
const int NUM_MUX_FLEX = 8;                   // F1..F8 on mux Y0..Y7

const int DIRECT_FLEX[] = {39, 36, 32};       // F9, F10, F11 (thumb)
const int NUM_DIRECT_FLEX = 3;

const int PAD_PINS[] = {14, 27, 16, 17, 21};  // C1..C5 conductive fabric
const int NUM_PADS = 5;

const int IMU_SDA = 23, IMU_SCL = 22, IMU_RST = 15;

const int NUM_FLEX = NUM_MUX_FLEX + NUM_DIRECT_FLEX;   // 11

// ---------- Timing ----------
const int SAMPLES = 8;
const unsigned long SEND_DELAY_MS = 4000;     // let the laptop finish service discovery
const unsigned long PERIOD_MS = 50;           // ~20 packets/s

BLEServer *server;
BLECharacteristic *characteristic;
unsigned long connectedAt = 0, lastSend = 0;

#if USE_IMU
Adafruit_BNO08x bno08x(IMU_RST);
sh2_SensorValue_t imuEvent;
#endif
float imuVals[7] = {0, 0, 0, 0, 0, 0, 0};     // qw,qx,qy,qz, ax,ay,az

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

// ---------- Flex reading ----------
int readAvg(int pin) {
  long sum = 0;
  for (int i = 0; i < SAMPLES; i++) sum += analogRead(pin);
  return sum / SAMPLES;
}

int readMux(int ch) {
  digitalWrite(MUX_S0, ch & 1);
  digitalWrite(MUX_S1, (ch >> 1) & 1);
  digitalWrite(MUX_S2, (ch >> 2) & 1);
  delayMicroseconds(100);        // let the mux output settle
  analogRead(MUX_COM);           // throw away first read to avoid bleed from previous channel
  return readAvg(MUX_COM);
}

// ---------- Contact pads ----------
// Returns a 10-bit mask: one bit per pad pair.
// Bit order: C1C2, C1C3, C1C4, C1C5, C2C3, C2C4, C2C5, C3C4, C3C5, C4C5
int pairBit(int a, int b) {              // a < b
  int idx = 0;
  for (int i = 0; i < a; i++) idx += (NUM_PADS - 1 - i);
  return idx + (b - a - 1);
}

int readContacts() {
  int mask = 0;
  for (int i = 0; i < NUM_PADS; i++) {
    pinMode(PAD_PINS[i], OUTPUT);
    digitalWrite(PAD_PINS[i], LOW);      // drive one pad at a time
    delayMicroseconds(5);
    for (int j = 0; j < NUM_PADS; j++) {
      if (j == i) continue;
      if (digitalRead(PAD_PINS[j]) == LOW) {
        int a = min(i, j), b = max(i, j);
        mask |= (1 << pairBit(a, b));
      }
    }
    pinMode(PAD_PINS[i], INPUT_PULLUP);  // release it
  }
  return mask;
}

// ---------- IMU ----------
#if USE_IMU
void enableImuReports() {
  bno08x.enableReport(SH2_GAME_ROTATION_VECTOR, 20000);   // 50 Hz
  bno08x.enableReport(SH2_LINEAR_ACCELERATION, 20000);
}
#endif

void updateImu() {
#if USE_IMU
  if (bno08x.wasReset()) enableImuReports();
  while (bno08x.getSensorEvent(&imuEvent)) {
    if (imuEvent.sensorId == SH2_GAME_ROTATION_VECTOR) {
      imuVals[0] = imuEvent.un.gameRotationVector.real;
      imuVals[1] = imuEvent.un.gameRotationVector.i;
      imuVals[2] = imuEvent.un.gameRotationVector.j;
      imuVals[3] = imuEvent.un.gameRotationVector.k;
    } else if (imuEvent.sensorId == SH2_LINEAR_ACCELERATION) {
      imuVals[4] = imuEvent.un.linearAcceleration.x;
      imuVals[5] = imuEvent.un.linearAcceleration.y;
      imuVals[6] = imuEvent.un.linearAcceleration.z;
    }
  }
#endif
}

// ---------- Setup ----------
void setup() {
  Serial.begin(115200);

  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);

  pinMode(MUX_S0, OUTPUT);
  pinMode(MUX_S1, OUTPUT);
  pinMode(MUX_S2, OUTPUT);
  pinMode(MUX_COM, INPUT);
  for (int i = 0; i < NUM_DIRECT_FLEX; i++) pinMode(DIRECT_FLEX[i], INPUT);
  for (int i = 0; i < NUM_PADS; i++) pinMode(PAD_PINS[i], INPUT_PULLUP);

#if USE_IMU
  Wire.begin(IMU_SDA, IMU_SCL);
  if (bno08x.begin_I2C()) {
    enableImuReports();
    Serial.println("BNO085 ready");
  } else {
    Serial.println("BNO085 not found, sending zeros for IMU");
  }
#endif

  BLEDevice::init("ESP32-BLE");
  BLEDevice::setMTU(247);

  server = BLEDevice::createServer();
  server->setCallbacks(new Callbacks());

  BLEService *service = server->createService(SERVICE_UUID);
  characteristic = service->createCharacteristic(
      CHAR_UUID, BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY);
  characteristic->addDescriptor(new BLE2902());
  service->start();
  server->getAdvertising()->addServiceUUID(SERVICE_UUID);
  server->startAdvertising();

  Serial.println("BLE advertising as ESP32-BLE");
}

// ---------- Loop ----------
// Packet: F1..F11, contactMask, qw,qx,qy,qz, ax,ay,az  (19 CSV values)
void loop() {
  updateImu();   // drain IMU events every pass

  unsigned long now = millis();
  if (now - lastSend < PERIOD_MS) return;
  lastSend = now;

  int flex[NUM_FLEX];
  for (int i = 0; i < NUM_MUX_FLEX; i++) flex[i] = readMux(i);
  for (int i = 0; i < NUM_DIRECT_FLEX; i++) flex[NUM_MUX_FLEX + i] = readAvg(DIRECT_FLEX[i]);
  int contacts = readContacts();

  char buf[200];
  int len = 0;
  for (int i = 0; i < NUM_FLEX; i++)
    len += snprintf(buf + len, sizeof(buf) - len, "%d,", flex[i]);
  len += snprintf(buf + len, sizeof(buf) - len, "%d", contacts);
  for (int i = 0; i < 7; i++)
    len += snprintf(buf + len, sizeof(buf) - len, ",%.3f", imuVals[i]);

  Serial.println(buf);   // always print, so you can debug over USB without Bluetooth

  if (server->getConnectedCount() > 0 && now - connectedAt > SEND_DELAY_MS) {
    characteristic->setValue((uint8_t *)buf, len);
    characteristic->notify();
  }
}