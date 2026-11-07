// Compile-only proof for the rules in skills/.
//
// Each function below is the smallest correct form of one rule. Nothing here
// talks to hardware in setup(); the point is that the compiler checks the API
// surface the skills recommend, on the core version the README claims.

#include <Arduino.h>
#include <Wire.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <freertos/queue.h>

// ---------------------------------------------------------------------------
// esp32-pwm-and-timing
// Duty is a count, not a percentage, and it depends on the resolution.
// ---------------------------------------------------------------------------
namespace pwm {

constexpr uint32_t kFreqHz = 5000;   // above the flicker a moving eye sees
constexpr uint8_t kResolution = 10;  // 1024 steps
constexpr uint32_t kMaxDuty = (1u << kResolution) - 1;

inline uint32_t dutyFor(uint8_t percent) {
  return (static_cast<uint32_t>(percent) * kMaxDuty) / 100u;
}

// Arduino core 3.x: attach the pin directly, write with the pin number.
void begin(uint8_t pin) {
  ledcAttach(pin, kFreqHz, kResolution);
  ledcWrite(pin, dutyFor(50));
}

}  // namespace pwm

// ---------------------------------------------------------------------------
// esp32-adc-and-sensors
// ADC1 only (ADC2 is unavailable while Wi-Fi is on), calibrated millivolts.
// ---------------------------------------------------------------------------
namespace adc {

constexpr uint8_t kAdc1Pin = 34;  // input-only, ADC1, safe with Wi-Fi on
constexpr uint8_t kSamples = 16;

void begin() {
  analogReadResolution(12);
  analogSetPinAttenuation(kAdc1Pin, ADC_11db);
}

// Returns calibrated millivolts; analogRead() alone is not a voltage.
uint32_t readMillivolts() {
  uint32_t total = 0;
  for (uint8_t i = 0; i < kSamples; i++) {
    total += analogReadMilliVolts(kAdc1Pin);
  }
  return total / kSamples;
}

}  // namespace adc

// ---------------------------------------------------------------------------
// esp32-i2c-bus
// A scan that gives up instead of hanging when a device holds SDA low.
// ---------------------------------------------------------------------------
namespace i2c {

constexpr uint8_t kSda = 21;
constexpr uint8_t kScl = 22;
constexpr uint32_t kTimeoutMs = 50;

uint8_t scan(uint8_t *found, uint8_t maxFound) {
  Wire.begin(kSda, kScl, 100000);
  Wire.setTimeOut(kTimeoutMs);
  uint8_t count = 0;
  for (uint8_t address = 1; address < 127 && count < maxFound; address++) {
    Wire.beginTransmission(address);
    if (Wire.endTransmission() == 0) {
      found[count++] = address;
    }
  }
  return count;
}

}  // namespace i2c

// ---------------------------------------------------------------------------
// esp32-freertos
// An ISR that hands work to a task through a queue, and a task with a stack
// size stated in bytes rather than guessed.
// ---------------------------------------------------------------------------
namespace rtos {

QueueHandle_t queue = nullptr;
constexpr uint32_t kStackBytes = 4096;  // xTaskCreate takes bytes on ESP32

struct Event {
  uint32_t atMs;
  uint8_t pin;
};

void IRAM_ATTR onEdge() {
  Event event{millis(), 0};
  BaseType_t woken = pdFALSE;
  xQueueSendFromISR(queue, &event, &woken);
  if (woken == pdTRUE) {
    portYIELD_FROM_ISR();
  }
}

void consumer(void *arg) {
  (void)arg;
  Event event{};
  for (;;) {
    if (xQueueReceive(queue, &event, portMAX_DELAY) == pdTRUE) {
      // handle it here, never in the ISR
    }
  }
}

void begin() {
  queue = xQueueCreate(16, sizeof(Event));
  xTaskCreatePinnedToCore(consumer, "consumer", kStackBytes / 4, nullptr, 5,
                          nullptr, 0);
}

}  // namespace rtos

// ---------------------------------------------------------------------------
// esp32-addressable-leds
// Current is the number that kills a strip, not the data protocol.
// ---------------------------------------------------------------------------
namespace leds {

constexpr uint16_t kCount = 60;
constexpr uint16_t kMilliampsPerLedFullWhite = 60;
constexpr uint16_t kUsbBudgetMilliamps = 500;

// 0 when the strip fits, otherwise the milliamps that have to come from
// somewhere other than the board's regulator.
uint16_t shortfallMilliamps() {
  const uint32_t needed = static_cast<uint32_t>(kCount) * kMilliampsPerLedFullWhite;
  return needed > kUsbBudgetMilliamps ? needed - kUsbBudgetMilliamps : 0;
}

}  // namespace leds

// ---------------------------------------------------------------------------
// esp32-partitions-and-ota
// App partitions are aligned to 0x10000 and the two OTA slots must match.
// ---------------------------------------------------------------------------
namespace partitions {

constexpr uint32_t kAppAlignment = 0x10000;

inline bool aligned(uint32_t offset) { return offset % kAppAlignment == 0; }

// Returns 0 when the layout is usable, else the first problem as a code.
uint8_t check(uint32_t slot0, uint32_t slot1, uint32_t slotSize) {
  if (!aligned(slot0) || !aligned(slot1)) return 1;
  if (slot1 - slot0 != slotSize) return 2;
  if (slot1 + slotSize > ESP.getFlashChipSize()) return 3;
  return 0;
}

}  // namespace partitions

// ---------------------------------------------------------------------------
// esp32-modbus-rs485
// CRC-16/MODBUS, the check every frame needs before it is trusted.
// ---------------------------------------------------------------------------
namespace modbus {

uint16_t crc16(const uint8_t *data, size_t length) {
  uint16_t crc = 0xFFFF;
  for (size_t i = 0; i < length; i++) {
    crc ^= data[i];
    for (uint8_t bit = 0; bit < 8; bit++) {
      if (crc & 0x0001) {
        crc = static_cast<uint16_t>((crc >> 1) ^ 0xA001);
      } else {
        crc = static_cast<uint16_t>(crc >> 1);
      }
    }
  }
  return crc;
}

}  // namespace modbus

// ---------------------------------------------------------------------------
// esp32-debugging
// A restart reason is read, not guessed.
// ---------------------------------------------------------------------------
namespace crash {

const char *lastResetReason() {
  switch (esp_reset_reason()) {
    case ESP_RST_POWERON: return "power on";
    case ESP_RST_SW: return "software restart";
    case ESP_RST_PANIC: return "panic";
    case ESP_RST_INT_WDT: return "interrupt watchdog";
    case ESP_RST_TASK_WDT: return "task watchdog";
    case ESP_RST_WDT: return "other watchdog";
    case ESP_RST_BROWNOUT: return "brownout";
    default: return "other";
  }
}

}  // namespace crash

// ---------------------------------------------------------------------------
// Wiring the pieces together. setup() only calls things that cannot block, so
// this sketch also runs on hardware without misbehaving.
// ---------------------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  delay(200);

  pwm::begin(25);
  adc::begin();
  rtos::begin();

  uint8_t found[8];
  const uint8_t devices = i2c::scan(found, sizeof(found));

  const uint16_t shortfall = leds::shortfallMilliamps();
  const uint8_t layout = partitions::check(0x10000, 0x150000, 0x140000);
  const uint8_t frame[] = {0x01, 0x03, 0x00, 0x00, 0x00, 0x0A};
  const uint16_t crc = modbus::crc16(frame, sizeof(frame));

  Serial.printf("reset reason : %s\n", crash::lastResetReason());
  Serial.printf("i2c devices  : %u\n", devices);
  Serial.printf("led shortfall: %u mA\n", shortfall);
  Serial.printf("partition    : %u (0 = ok)\n", layout);
  Serial.printf("modbus crc   : 0x%04X\n", crc);
  Serial.printf("adc millivolts: %lu\n", static_cast<unsigned long>(adc::readMillivolts()));
  Serial.printf("pwm duty     : %lu of %lu\n", static_cast<unsigned long>(pwm::dutyFor(50)),
                static_cast<unsigned long>(pwm::kMaxDuty));
}

void loop() { delay(1000); }
