// Board facts: what the chip reports about itself.
//
// Used to verify that the `esp32` profile in data/esp32-pins.json is the right
// one for the module on the desk, and that partition_check.py is being called
// with the right --flash value.

#include <Arduino.h>

void setup() {
  Serial.begin(115200);
  delay(300);
  Serial.println();
  Serial.println("=== board facts ===");
  Serial.printf("chip        : %s rev %d, %d core(s)\n",
                ESP.getChipModel(), ESP.getChipRevision(), ESP.getChipCores());
  Serial.printf("cpu         : %u MHz\n", getCpuFrequencyMhz());
  Serial.printf("flash       : %u MB (%u bytes)\n",
                ESP.getFlashChipSize() / (1024 * 1024), ESP.getFlashChipSize());
  Serial.printf("sdk         : %s\n", ESP.getSdkVersion());
  Serial.printf("free heap   : %u bytes\n", ESP.getFreeHeap());
  Serial.println("=== end ===");
}

void loop() {
  // A heartbeat proves the sketch is still running rather than stuck in setup.
  Serial.printf("alive  uptime=%lus  heap=%u\n", millis() / 1000, ESP.getFreeHeap());
  delay(2000);
}
