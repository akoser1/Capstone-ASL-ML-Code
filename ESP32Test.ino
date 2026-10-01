
void setup() {

  // Start serial communication
  Serial.begin(115200);

  // Wait briefly for startup
  delay(1000);

  Serial.println("ESP32 Starting...");
}

void loop() {

  // Print a message every second
  Serial.println("Hello! ESP32 is working!");

  delay(1000);
}
