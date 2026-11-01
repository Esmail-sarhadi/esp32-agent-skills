# One hundred and sixty ESP32 failures, with the cause and the fix

Collected from the questions people actually ask on Stack Overflow. Each entry
links to the thread that covers it - a few share one thread when the accepted
answer explains both cases. Read by symptom.

Legend: **see** = what the board does, **cause** = why, **fix** = what to change.

---

## Power, brownout and boot (1-9)

1. **Brownout when Wi-Fi starts** — see: `Brownout detector was triggered` right after `WiFi.begin()`. cause: the radio's transmit peaks pull ~350 mA and a thin USB cable or a small LDO sags below 2.5 V. fix: 470 µF bulk capacitor at the module, a regulator rated for 500 mA, a short thick cable. · [60171641](https://stackoverflow.com/q/60171641)
2. **ESP32-CAM browns out at boot** — see: reboot loop as soon as the camera initialises. cause: camera and Wi-Fi start together and exceed the board's regulator. fix: separate 5 V supply with a large capacitor; the on-board regulator is not enough for camera + radio. · [60171641](https://stackoverflow.com/q/60171641)
3. **Board will not enter download mode** — see: `Failed to connect ... Timed out waiting for packet header`. cause: the auto-reset circuit did not assert GPIO0 low, or the cable is charge-only. fix: hold BOOT, tap EN, release; try another cable. · [70532139](https://stackoverflow.com/q/70532139)
4. **Invalid head of packet** — see: `Failed to connect to ESP32: Invalid head of packet (0x00)`. cause: something else is talking on the UART at boot, or the baud is wrong. fix: disconnect other serial devices, lower the upload speed to 115200. · [73134391](https://stackoverflow.com/q/73134391)
5. **The port does not exist** — see: no COM port at all. cause: missing CP210x/CH340 driver, or the board is in a state where the USB bridge is unpowered. fix: install the bridge driver, check Device Manager, try a powered hub. · [73923341](https://stackoverflow.com/q/73923341)
6. **ESP32-CAM sends nothing on serial** — see: upload succeeds, monitor is silent. cause: the camera boards power the USB-serial chip only when GPIO0 is low, and the sketch reconfigures the UART pins. fix: use a USB-TTL adapter on U0TXD/U0RXD, keep GPIO0 high after flashing. · [76021459](https://stackoverflow.com/q/76021459)
7. **Stack canary watchpoint triggered** — see: `Debug exception reason: Stack canary watchpoint triggered`. cause: a stack buffer overflow, usually a large local array or `sprintf` into a small buffer. fix: move large buffers to static or heap, size them by the worst case, and enable `CONFIG_COMPILER_STACK_CHECK`. · [56779459](https://stackoverflow.com/q/56779459)
8. **TG1WDT_SYS_RST on minimal code** — see: an ESP32-C3 resets immediately even with an empty sketch. cause: a bootloader or partition mismatch, often after flashing a binary built for another target. fix: erase the flash (`esptool erase_flash`) and reflash a build for that exact chip. · [79759209](https://stackoverflow.com/q/79759209)
9. **Board stops booting after a partition change** — see: boot loop, or `invalid header` in the ROM log. cause: `boot_app0.bin` missing, or the app partition offset no longer matches the table. fix: reflash bootloader, partitions and boot_app0 together; the app offset must be 0x10000-aligned. · [67149410](https://stackoverflow.com/q/67149410)

## GPIO and strapping (10-17)

10. **Driving GPIO6-11 kills the board** — see: it compiles, flashes, then never boots again. cause: those pins are the SPI flash bus. fix: never use them; `pincheck.py` rejects them. · [65125302](https://stackoverflow.com/q/65125302)
11. **`INPUT_PULLUP` does nothing on GPIO34-39** — see: a button reads floating noise. cause: those pins are input-only and have no internal pull-up or pull-down at all. fix: external 10 kΩ resistor, or move the button to a pin that has one. · [53324715](https://stackoverflow.com/q/53324715)
12. **It boots on the bench, fails in the enclosure** — see: works until power is cycled. cause: a strapping pin (0, 2, 12, 15) is held at the wrong level by attached hardware at reset. fix: keep GPIO12 low at boot, do not load GPIO0/2/15 with anything that pulls them during reset. · [65125302](https://stackoverflow.com/q/65125302)
13. **The on-board LED will not blink** — see: `digitalWrite(2, HIGH)` changes nothing. cause: on many boards the LED is on GPIO2 but wired active-low, or it is a WS2812 on a different pin. fix: invert the logic, and check the board's schematic — the pin is not standard. · [79943423](https://stackoverflow.com/q/79943423)
14. **`digitalWrite` is too slow** — see: a bit-banged protocol misses timing. cause: the Arduino API costs microseconds per call. fix: direct register access (`GPIO.out_w1ts`), or better, use the RMT/LEDC peripheral. · [52348930](https://stackoverflow.com/q/52348930)
15. **Touch pins stop working with Wi-Fi** — see: `touchRead` returns garbage. cause: the touch peripheral shares hardware with the radio. fix: do not mix touch and Wi-Fi on the same channel plan; read touch only while the radio is idle. · [65125302](https://stackoverflow.com/q/65125302)
16. **A pin works as input but not output** — see: the output never changes. cause: it is one of GPIO34-39, which have no output driver. fix: pick another pin; there is nothing to enable. · [53324715](https://stackoverflow.com/q/53324715)
17. **Board reboots when a relay switches** — see: reset exactly when the load turns on. cause: inductive kickback on the GPIO rail, or a ground loop. fix: flyback diode across the coil, opto-isolation, separate supply for the relay board. · [60171641](https://stackoverflow.com/q/60171641)

## ADC (18-23)

18. **`analogRead` returns 0 once Wi-Fi connects** — see: readings worked before `WiFi.begin()`. cause: ADC2 is unavailable while the radio is on; there is no workaround. fix: move the sensor to ADC1 (GPIO32-39). · [65125302](https://stackoverflow.com/q/65125302)
19. **The top of the range is compressed** — see: values flatten near 3.2 V. cause: at 11 dB attenuation the ADC is not linear above ~2.5 V. fix: use a divider so the signal lands mid-range, or calibrate with `analogReadMilliVolts`. · [56833346](https://stackoverflow.com/q/56833346)
20. **Measuring battery voltage** — see: a divider reads low and drifts. cause: the sample-and-hold capacitor loads a high-impedance divider. fix: keep the divider under 10 kΩ, add 100 nF at the pin. · [56266857](https://stackoverflow.com/q/56266857)
21. **Reading VCC without an external pin** — see: no way to know the supply. cause: there is no internal VCC channel. fix: measure an internal reference through a known divider, or use `esp_adc_cal` with a factory-calibrated reference. · [56833346](https://stackoverflow.com/q/56833346)
22. **Readings are noisy** — see: ±20 counts of jitter. cause: the ADC is noisy by design. fix: average N samples (noise drops by √N), add a capacitor, keep the sensor wire short. · [65725609](https://stackoverflow.com/q/65725609)
23. **Sampling audio or a fast signal** — see: `analogRead` cannot keep up. cause: it is a slow, blocking call. fix: use I2S in ADC mode with DMA; it samples continuously without the CPU. · [65725609](https://stackoverflow.com/q/65725609)

## I2C and SPI (24-30)

24. **The sensor is never detected** — see: `i2c.scan()` finds nothing. cause: no pull-ups, wrong pins, or the device is on a different address than the datasheet's default. fix: 4.7 kΩ to 3.3 V on SDA and SCL, confirm the address with a scan, check the pin mapping of your board. · [79330446](https://stackoverflow.com/q/79330446)
25. **SCL stuck low** — see: the bus is dead until power cycle. cause: a slave is holding the line after a partial transfer. fix: clock SCL manually nine times to let it release, then issue a STOP. · [79237471](https://stackoverflow.com/q/79237471)
26. **`ENODEV` but the scan works** — see: MicroPython finds the address then throws `[Errno 19]`. cause: the driver was constructed with the wrong address or a stale bus object. fix: recreate the bus, pass the scanned address explicitly. · [67703244](https://stackoverflow.com/q/67703244)
27. **SPI transfer ends early** — see: the transaction stops mid-buffer. cause: the length was given in bytes where the driver expects words, or CS was released too soon. fix: check the length units and keep CS asserted for the whole transaction. · [49348228](https://stackoverflow.com/q/49348228)
28. **MPU-6050 FIFO returns nonsense** — see: the first samples are correct then garbage. cause: the FIFO is read without checking the count register, or without clearing it. fix: read `FIFO_COUNT`, read exactly that many bytes, reset the FIFO on overrun. · [60419390](https://stackoverflow.com/q/60419390)
29. **I2C works alone, fails with Wi-Fi** — see: timeouts only when the radio is active. cause: the radio's interrupts delay the bus, and the default timeout is short. fix: raise the I2C timeout, lower the clock to 100 kHz, retry the transaction. · [63696993](https://stackoverflow.com/q/63696993)
30. **Two devices with the same address** — see: both respond, both return the other's data. cause: fixed-address parts cannot share a bus. fix: use a TCA9548A multiplexer, or move one device to a second I2C bus. · [79330446](https://stackoverflow.com/q/79330446)

## UART (31-35)

31. **Garbled serial output** — see: readable at first, then symbols. cause: baud mismatch, or the monitor is attached to the wrong UART (USB CDC vs UART0). fix: match the baud exactly, and print to the same port the monitor is on. · [79670176](https://stackoverflow.com/q/79670176)
32. **`Serial.print` and `Serial.printf` disagree** — see: different values for the same variable. cause: the format specifier does not match the type (`%d` for a `long`, `%f` for a double that was promoted). fix: use `PRIu32`/`%lu` and cast explicitly. · [60691951](https://stackoverflow.com/q/60691951)
33. **Long lines get truncated** — see: only the first ~120 characters arrive. cause: the RX buffer is 256 bytes by default. fix: raise `SERIAL_RX_BUFFER_SIZE` at build time, or drain faster. · [60879021](https://stackoverflow.com/q/60879021)
34. **`SoftwareSerial` does not work** — see: nothing received. cause: the ESP32 has three hardware UARTs; bit-banging is unreliable and unsupported. fix: use `HardwareSerial(1)` or `(2)` with explicit pins. · [60094545](https://stackoverflow.com/q/60094545)
35. **Waking from light sleep on serial data** — see: the UART does not wake the chip. cause: the wake source must be enabled before sleeping and the pin must be a valid wake pin. fix: `gpio_wakeup_enable` on the RX pin plus `esp_sleep_enable_gpio_wakeup`. · [79700029](https://stackoverflow.com/q/79700029)

## Wi-Fi (36-43)

36. **The board drops off and reconnects in a loop** — see: connects, disconnects, repeats every few seconds. cause: the application reconnects on top of the core's own reconnect logic, and both fight. fix: disable one of them; add exponential backoff instead of a tight retry. · [48024780](https://stackoverflow.com/q/48024780)
37. **Wi-Fi and Bluetooth together are unstable** — see: enabling both makes one of them fail. cause: they share one radio and one antenna; coexistence needs time-slicing. fix: enable coexistence in `menuconfig`, expect lower throughput on both, or move to a chip with two radios. · [65636417](https://stackoverflow.com/q/65636417)
38. **The antenna choice is not what you think** — see: terrible range on a module with an external antenna connector. cause: the RF switch must be told which antenna to use, and some modules need a solder jumper moved. fix: check the module's antenna selection pin/strapping, not the software. · [55865909](https://stackoverflow.com/q/55865909)
39. **The access point always uses 192.168.4.1** — see: clients cannot reach the device on another subnet. cause: the default AP IP is fixed. fix: `WiFi.softAPConfig()` before `softAP()`. · [58976055](https://stackoverflow.com/q/58976055)
40. **mDNS works on one device and not another** — see: `device.local` resolves from a laptop but not a phone. cause: Android's resolver does not do mDNS by default. fix: do not rely on mDNS for discovery; publish the IP over the protocol you already have. · [79405699](https://stackoverflow.com/q/79405699)
41. **`connect()` returns errno 104** — see: `Connection reset by peer` after a few requests. cause: the server closed a keep-alive connection and the client reused it. fix: handle the reset by reconnecting, do not assume a socket stays open. · [72320853](https://stackoverflow.com/q/72320853)
42. **HTTP GET takes seconds** — see: each request is slow even on a good network. cause: DNS resolution and a new TLS handshake per request. fix: reuse the connection, cache the resolved IP, or move to a persistent protocol. · [72242061](https://stackoverflow.com/q/72242061)
43. **Checking whether the internet is up** — see: `WiFi.status()` says connected but nothing loads. cause: it only reports the link, not reachability. fix: ping the gateway or fetch a small known URL with a short timeout, and cache the result. · [60906082](https://stackoverflow.com/q/60906082)

## BLE (44-47)

44. **Advertising stops once a client connects** — see: no longer discoverable after the first connection. cause: advertising is not restarted on disconnect, and some stacks stop it on connect. fix: restart advertising in the disconnect handler. · [72913315](https://stackoverflow.com/q/72913315)
45. **BLE keeps the chip awake** — see: deep sleep never reaches microamps. cause: the BLE stack holds the radio and a timer. fix: deinit BLE before sleeping, and use `esp_bluedroid_disable`. · [61811536](https://stackoverflow.com/q/61811536)
46. **A device will not pair** — see: the phone sees it, pairing fails. cause: missing bonding flags, or a security request the peripheral never answers. fix: set bonding and MITM explicitly and store the keys in NVS. · [67864472](https://stackoverflow.com/q/67864472)
47. **BLE and Wi-Fi share the antenna** — see: throughput collapses when both are active. cause: single radio, time-sliced. fix: expect it, or schedule BLE advertising only in Wi-Fi idle windows. · [65636417](https://stackoverflow.com/q/65636417)

## Flash, NVS and OTA (48-55)

48. **"Sketch too big"** — see: the build fails at link time. cause: the default partition table gives the app only ~1.2 MB. fix: choose a partition scheme with a bigger app slot; do not shrink the code. · [75396355](https://stackoverflow.com/q/75396355)
49. **NVS runs out of space** — see: `ESP_ERR_NVS_NO_FREE_PAGES`. cause: the NVS partition is 20 KB by default and entries have overhead. fix: enlarge the NVS partition in the table, or store large blobs in SPIFFS/LittleFS. · [55222899](https://stackoverflow.com/q/55222899)
50. **Writing flash every second** — see: the device dies after months. cause: flash endurance is ~100k erase cycles per sector. fix: buffer in RAM and flush on a timer or on change; never log to NVS in a loop. · [73783849](https://stackoverflow.com/q/73783849)
51. **EEPROM, NVS or SPIFFS?** — see: no clear choice. cause: they solve different problems. fix: NVS for small key-values, SPIFFS/LittleFS for files, EEPROM emulation only for compatibility. · [70826170](https://stackoverflow.com/q/70826170)
52. **EEPROM wear** — see: `EEPROM.commit()` in a loop. cause: each commit erases a sector. fix: commit on change with a debounce, or keep the value in NVS which does wear levelling. · [59817278](https://stackoverflow.com/q/59817278)
53. **Storing a string permanently** — see: `EEPROM.write` truncates. cause: it writes bytes, not strings. fix: write length + bytes, or use NVS with `nvs_set_str`. · [56139657](https://stackoverflow.com/q/56139657)
54. **The best way to store frequent data** — see: samples every second. cause: flash is the wrong medium for that rate. fix: ring buffer in RAM, flush batches to flash, or use RTC memory across deep sleep. · [63780850](https://stackoverflow.com/q/63780850)
55. **Writing NVS during production flashing** — see: each unit needs a unique ID. cause: NVS is initialised at first boot, not at flash time. fix: generate an NVS partition image and flash it with the rest, or provision over serial on first boot. · [73937267](https://stackoverflow.com/q/73937267)

## Crashes, memory and the watchdog (56-63)

56. **`LoadProhibited`** — see: `Guru Meditation Error: Core 1 panic'ed (LoadProhibited)`. cause: dereferencing NULL or a freed pointer. fix: check every pointer that came from `malloc`, `strchr`, or a failed lookup; `EXCVADDR` in the dump tells you the address. · [63399901](https://stackoverflow.com/q/63399901)
57. **Reading a backtrace** — see: a list of addresses. cause: the addresses are only meaningful with the matching ELF. fix: keep the ELF from that exact build and run `xtensa-esp32-elf-addr2line -pfiaC -e firmware.elf <addresses>`. · [65630477](https://stackoverflow.com/q/65630477)
58. **`Interrupt wdt timeout on CPU1`** — see: panic with no obvious code path. cause: an ISR ran longer than the interrupt watchdog allows. fix: move work out of the ISR into a task via a queue; never call `delay`, `printf` or allocate inside an ISR. · [71992044](https://stackoverflow.com/q/71992044)
59. **`Task watchdog got triggered`** — see: reset after ~5 s of silence. cause: a task blocked or looped without yielding. fix: find the blocking call; add `vTaskDelay` only if the loop is genuinely idle. · [66278271](https://stackoverflow.com/q/66278271)
60. **The watchdog fires during a long operation** — see: a legitimate long flash write or computation trips it. cause: the task never yields to the idle task. fix: subscribe the task to the TWDT and call `esp_task_wdt_reset()` inside the loop, or chunk the work. · [51750377](https://stackoverflow.com/q/51750377)
61. **Zeroing PSRAM eats all memory** — see: allocation fails after initialising a large buffer. cause: `calloc`-style zeroing touches every page and commits it. fix: allocate, then zero only what you use; check `ESP.getFreePsram()` before and after. · [79260342](https://stackoverflow.com/q/79260342)
62. **MQTT publish crashes with a stack overflow** — see: reboot inside the publish call. cause: TLS plus MQTT needs more stack than the default task size. fix: raise the task stack to 8-16 KB, or publish from a dedicated task. · [67824787](https://stackoverflow.com/q/67824787)
63. **`multiple definition of ...`** — see: link error after adding a second source file. cause: a variable defined in a header included twice. fix: `extern` in the header, define it in exactly one `.c`. · [57759461](https://stackoverflow.com/q/57759461)

## RTOS and timing (64-67)

64. **A task must never return** — see: crash or silent stop when the function ends. cause: FreeRTOS tasks are not allowed to return; there is nowhere to return to. fix: end with `vTaskDelete(NULL)` or an infinite loop. · [63634917](https://stackoverflow.com/q/63634917)
65. **Stopping a task cleanly** — see: `vTaskDelete` from outside leaves resources held. cause: the task never gets to free its own memory. fix: signal it with a notification or a flag, let it clean up, then delete itself. · [62113104](https://stackoverflow.com/q/62113104)
66. **`std::mutex` versus `xSemaphore`** — see: a C++ mutex deadlocks or does not protect. cause: the C++ wrapper is not integrated with the RTOS scheduler the way the native primitives are. fix: use `xSemaphoreCreateMutex` / `std::mutex` consistently, never mix the two on the same resource. · [57430102](https://stackoverflow.com/q/57430102)
67. **Rotary encoder misses steps** — see: counts are lost when the motor runs. cause: the ISR is too slow, or the pins have no hardware filter. fix: keep the ISR to a single counter increment, use the PCNT peripheral for real encoders. · [66388689](https://stackoverflow.com/q/66388689)

## Build and toolchain (68-70)

68. **`esp_wifi.h: No such file or directory`** — see: the build cannot find an IDF header. cause: the component is not in `REQUIRES`, or the include path is not set. fix: add the component to the CMake `REQUIRES`/`PRIV_REQUIRES` list. · [74900268](https://stackoverflow.com/q/74900268)
69. **`idf.py` is not recognised** — see: the command is missing after install. cause: the export script was not sourced in this shell. fix: run `export.sh` (or `. ./export.sh`) in the same terminal, every time. · [63615242](https://stackoverflow.com/q/63615242)
70. **`collect2.exe: error: ld returned 1 exit status`** — see: the build fails only at link. cause: two libraries define the same symbol, or a library is missing from the build. fix: read the lines above the error — the linker always names the symbol; then remove the duplicate or add the missing dependency. · [64778211](https://stackoverflow.com/q/64778211)

---

## Why these seventy

They come from the highest voted questions in the `esp32` tag, filtered to the
ones where the accepted answer names a concrete cause rather than "try another
library". Every entry was written against the thread it links to; where two
entries share a link, that answer covers both.

The pattern worth noticing: almost none of them are about the code being wrong.
They are about the board being a physical object — a supply that sags, a pin
that is not a GPIO, a radio that takes the ADC away, a flash that wears out.
An agent that only reads the code cannot see any of that.

---

# Part two: sleep, storage, security, buses and tasks (71-110)

## Sleep, ULP and wake sources (71-79)

71. **Deep sleep still draws milliamps** — see: 8 mA instead of 10 µA. cause: the USB-serial chip is still powered, a GPIO is left driving a load, or the regulator has high quiescent current. fix: measure on the battery rail only, `gpio_hold_en` the pins that must keep state, use a board without an always-on USB bridge. · [56548700](https://stackoverflow.com/q/56548700)
72. **A GPIO change does not wake the chip** — see: the interrupt works while awake, nothing after deep sleep. cause: only RTC-capable pins (0-15 on the classic ESP32) can wake from deep sleep. fix: use `esp_sleep_enable_ext1_wakeup()` with a bitmask of RTC pins and the level you want. · [54500282](https://stackoverflow.com/q/54500282)
73. **The ULP cannot touch a normal peripheral** — see: ULP code reads zero or hangs. cause: the ULP has its own tiny instruction set and can only reach RTC memory and a few registers. fix: keep the ULP to sampling and simple arithmetic, and let the main cores do everything else. · [61484531](https://stackoverflow.com/q/61484531)
74. **ULP wake period drifts by minutes** — see: a "60 s" wake drifts. cause: the RTC slow clock is an RC oscillator with several percent tolerance. fix: calibrate it against the XTAL, or accept the drift and resync time when the radio is on. · [66606880](https://stackoverflow.com/q/66606880)
75. **Variables lose their value after sleep** — see: a counter resets every wake. cause: deep sleep powers down normal RAM; only RTC memory survives. fix: `RTC_DATA_ATTR` on the few values that must persist, and keep them small. · [56548700](https://stackoverflow.com/q/56548700)
76. **`ext0` wake never fires** — see: no wake on a valid pin. cause: `ext0` works on a single RTC pin and a specific level, and the pin must be configured as an RTC IO first. fix: `rtc_gpio_init` + `rtc_gpio_pullup`, then `esp_sleep_enable_ext0_wakeup(pin, level)`. · [54500282](https://stackoverflow.com/q/54500282)
77. **Touch does not wake the board** — see: touch works while awake, not as a wake source. cause: touch wake has to be armed separately and only works on touch-capable pins. fix: `esp_sleep_enable_touchpad_wakeup()` plus `touch_pad_set_fsm_mode`. · [54500282](https://stackoverflow.com/q/54500282)
78. **Light sleep and deep sleep behave differently** — see: a sketch that survives light sleep dies after deep sleep. cause: light sleep keeps RAM and the peripherals; deep sleep keeps almost nothing. fix: treat them as different features, not a tuning knob. · [56548700](https://stackoverflow.com/q/56548700)
79. **Brownout right after waking** — see: a reset exactly when the radio starts. cause: the bulk capacitor is discharged after a long sleep and the RF inrush pulls the rail down. fix: larger capacitor, and bring the radio up after a short delay so the supply recovers. · [60171641](https://stackoverflow.com/q/60171641)

## OTA, partitions and storage (80-87)

80. **OTA uploads but nothing changes** — see: the write succeeds, the old firmware still runs. cause: the OTA API writes to the inactive partition; without `set_boot_partition` and a reboot the bootloader still starts the old one. fix: `esp_ota_end()` then `esp_ota_set_boot_partition()` then restart. · [55354110](https://stackoverflow.com/q/55354110)
81. **A bad OTA bricks the device** — see: the new image boots once and dies. cause: no rollback configured, so a broken image stays active. fix: enable `CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE` and call `esp_ota_mark_app_valid_cancel_rollback()` only after the device proves itself. · [55354110](https://stackoverflow.com/q/55354110)
82. **Boot loop after editing the partition table** — see: `invalid header` or an immediate reset. cause: the table moved the app offset but the bootloader and `otadata` were not reflashed with it. fix: flash bootloader, partition table and otadata together, and keep the app offset 0x10000-aligned. · [79573140](https://stackoverflow.com/q/79573140)
83. **SPIFFS shows far less than 4 MB** — see: `SPIFFS.totalBytes()` reports a few hundred KB. cause: the filesystem size is whatever the partition table gives it, not the flash size. fix: enlarge the `spiffs`/`littlefs` partition in the table. · [63568190](https://stackoverflow.com/q/63568190)
84. **The filesystem corrupts after a power cut** — see: mount fails after an unexpected reset. cause: SPIFFS is not power-loss resilient. fix: move to LittleFS, which keeps a journal, or call `format` on mount failure and rebuild. · [63568190](https://stackoverflow.com/q/63568190)
85. **The device crashes during OTA writes** — see: a panic inside a flash write. cause: writing flash disables the cache, so any code running from flash — including ISRs — faults. fix: put interrupt handlers in IRAM (`IRAM_ATTR`) and stop other flash users during the write. · [55354110](https://stackoverflow.com/q/55354110)
86. **HTTPS OTA fails the handshake** — see: `HTTPClient` returns -1 over `https`. cause: no certificate, or a clock so wrong that the cert looks not-yet-valid. fix: set the time first and pin a CA; `setInsecure()` works but removes the only protection OTA has. · [69998482](https://stackoverflow.com/q/69998482)
87. **OTA over a slow link times out** — see: the download stalls near the end. cause: the default HTTP timeout is shorter than the transfer. fix: raise the timeout, stream into `esp_ota_write` in chunks, and never buffer the whole image. · [69998482](https://stackoverflow.com/q/69998482)

## TLS, HTTPS and time (88-92)

88. **TLS handshake fails with a valid certificate** — see: `setCACert` still fails. cause: the system clock is at 1970, so the certificate is not valid yet. fix: sync time over SNTP before the first HTTPS call. · [68356924](https://stackoverflow.com/q/68356924)
89. **The certificate expires and the product dies** — see: every device stops talking on the same day. cause: a leaf certificate was pinned instead of a CA, or the root changed. fix: pin a CA bundle, ship an update path for the bundle, and monitor expiry. · [79290534](https://stackoverflow.com/q/79290534)
90. **`time(nullptr)` returns a 1970 timestamp** — see: time is never valid. cause: `configTime` is asynchronous and returns immediately. fix: wait until the value is above a sane floor (e.g. 1.6e9) before trusting it, with a timeout. · [68356924](https://stackoverflow.com/q/68356924)
91. **WebSocket closes with code 1006** — see: the socket dies with no close frame. cause: nothing was sent for longer than the proxy or server idle timeout. fix: send a ping every 20-30 s and handle a reconnect instead of assuming the link is alive. · [66246069](https://stackoverflow.com/q/66246069)
92. **UDP packets vanish on the soft-AP** — see: heavy loss when the ESP32 is the access point. cause: modem sleep parks the radio between beacons. fix: `WiFi.setSleep(false)` while streaming, and expect lower throughput than the datasheet suggests. · [68803924](https://stackoverflow.com/q/68803924)

## CAN, RMT, DAC and touch (93-99)

93. **TWAI receives nothing** — see: no frames at all. cause: no transceiver on the bus, TX/RX swapped, no 120 Ω termination, or a bitrate mismatch. fix: check the transceiver first, then the termination, then the timing. · [68527367](https://stackoverflow.com/q/68527367)
94. **The LED strip flickers when CAN is active** — see: WS2812 glitches under bus load. cause: the strip refresh is timing-critical and the CAN ISR delays it. fix: drive the strip from RMT, keep the CAN ISR short, and do not refresh from inside a handler. · [78921826](https://stackoverflow.com/q/78921826)
95. **`rmtWrite` blocks the whole loop** — see: the main loop stutters during a strip update. cause: the blocking variant waits for the transmission. fix: `rmt_write_items(..., false)` and wait on the done semaphore, or double-buffer two transactions. · [78921826](https://stackoverflow.com/q/78921826)
96. **DAC output does nothing** — see: `dacWrite` has no effect. cause: the DAC exists only on GPIO25 and GPIO26, and both are also ADC2 channels. fix: use those two pins only, and do not expect them to work as ADC while Wi-Fi is on. · [79276197](https://stackoverflow.com/q/79276197)
97. **Touch readings drift over hours** — see: thresholds that worked stop working. cause: the touch baseline is not recalibrated and the environment changed. fix: run `touch_pad_set_meas_time` sensibly, recalibrate the baseline periodically, and add a guard ring on the PCB. · [54500282](https://stackoverflow.com/q/54500282)
98. **A PCNT pin cannot be used for wake** — see: `ext1` wake does nothing on a pin that works elsewhere. cause: the pulse counter has taken the pin. fix: `pcnt_unit_disable` and release the GPIO before arming the wake source. · [54316980](https://stackoverflow.com/q/54316980)
99. **The servo jitters** — see: random twitches even with a clean PWM signal. cause: the servo's current spikes brown out the shared 5 V rail. fix: separate supply, common ground, and a capacitor at the servo. · [60171641](https://stackoverflow.com/q/60171641)

## RTOS, memory and watchdogs (100-105)

100. **A queue send from an ISR crashes** — see: `LoadProhibited` inside the interrupt. cause: `xQueueSend` was used instead of the ISR variant. fix: `xQueueSendFromISR` with the woken flag, and create the queue before attaching the interrupt. · [71185014](https://stackoverflow.com/q/71185014)
101. **The task stack overflows when parsing JSON** — see: a reset inside `deserializeJson`. cause: JSON parsing needs several KB of stack, and the default task stack is smaller than that. fix: parse on a dedicated task with 8-16 KB, or use a filter to read only the fields you need. · [78288058](https://stackoverflow.com/q/78288058)
102. **PSRAM allocation fails** — see: `ps_malloc` returns NULL on a module with PSRAM. cause: PSRAM is not enabled in the build, or the allocator was asked for internal RAM. fix: enable SPIRAM in the board config and use `heap_caps_malloc(size, MALLOC_CAP_SPIRAM)`. · [71083711](https://stackoverflow.com/q/71083711)
103. **The watchdog still fires after disabling it** — see: WDT resets continue. cause: there are three watchdogs — task, interrupt and RTC — and they are configured separately. fix: identify which one from the reset reason, then handle that one. · [62786654](https://stackoverflow.com/q/62786654)
104. **`LoadProhibited` only in a task** — see: the same code works in `loop()`. cause: the task stack is too small, or it holds a pointer to another task's stack. fix: size the stack in bytes, pass data by value or by heap, never by a pointer into a stack frame. · [79705623](https://stackoverflow.com/q/79705623)
105. **Heap shrinks over days** — see: free heap falls and never recovers. cause: fragmentation from `String` concatenation and many small allocations of different sizes. fix: fixed-size buffers, reserve() up front, and check `heap_caps_get_largest_free_block` rather than the total. · [63780850](https://stackoverflow.com/q/63780850)

## Network servers, BLE and RF (106-110)

106. **The captive portal never opens on Android** — see: the phone connects and does nothing. cause: Android probes `connectivitycheck.gstatic.com/generate_204` and expects a 204 or a redirect. fix: answer that path explicitly and resolve every DNS name to the AP address. · [79693016](https://stackoverflow.com/q/79693016)
107. **Clients on the soft-AP have no internet** — see: they connect but cannot reach the web. cause: the ESP32 is an access point, not a router; there is no NAT in the default stack. fix: add a NAT layer (`esp_netif_napt_enable` on newer IDF) or accept an offline-only AP. · [76529566](https://stackoverflow.com/q/76529566)
108. **The AP IP is printed before it exists** — see: `WiFi.softAPIP()` returns 0.0.0.0. cause: the AP starts asynchronously. fix: wait for the `AP_START` / `got_ip` event before printing or advertising the address. · [73999244](https://stackoverflow.com/q/73999244)
109. **Two BLE profiles fight over one callback** — see: notifications stop when a second service is added. cause: a single GATTS handler cannot own two profiles' events. fix: register one handler per profile and dispatch on `gatts_if`. · [56791714](https://stackoverflow.com/q/56791714)
110. **A phone will not reconnect after reflashing** — see: the device is invisible to a phone that paired before. cause: the phone still holds the old bond while the ESP32 lost its keys. fix: delete the bond on the phone, or call `esp_ble_remove_bond_device` and re-pair. · [68614591](https://stackoverflow.com/q/68614591)

---

# Part three: updates, cameras, buses, tasks and tooling (111-160)

## OTA, flashing and boot (111-118)

111. **An OTA upload dies halfway through** — see: `Update.begin()` succeeds and the write stops. cause: SPIFFS or LittleFS is still mounted, and the flash region the update writes to is held by the filesystem. fix: `SPIFFS.end()` (or `LittleFS.end()`) before `Update.begin()`, and remount afterwards. · [72830659](https://stackoverflow.com/q/72830659)
112. **An OTA POST delivers a file the device rejects** — see: `Update` reports no error but the image never boots. cause: the request was sent as `multipart/form-data`, so the boundary and part headers ended up inside the binary. fix: send the raw `.bin` as the request body with no form wrapper and let `Update` write it byte for byte. · [67160638](https://stackoverflow.com/q/67160638)
113. **Writing the otadata partition by hand breaks the next boot** — see: the device picks the wrong slot after a manual write. cause: the two `otadata` sectors are a sequence counter plus a CRC that the IDF owns; a hand-built copy loses the sequence and the bootloader falls back. fix: never write `otadata` yourself — call `esp_ota_set_boot_partition()` and let the IDF commit it. · [76213938](https://stackoverflow.com/q/76213938)
114. **`flash read err, 1000` on every boot** — see: a reset loop before any of your code runs. cause: the flash contents and the bootloader disagree after a partial or mismatched flash. fix: erase the whole chip first (`esptool.py erase_flash`, or PlatformIO's Erase Flash), then flash bootloader, partition table and app together. · [68761428](https://stackoverflow.com/q/68761428)
115. **A project header will not `#include` in ESP-IDF** — see: advice from ordinary CMake answers does nothing. cause: IDF wraps CMake in a component model, so a top-level `include_directories()` is not what the compiler sees. fix: declare `INCLUDE_DIRS` and `SRCS` in that component's `CMakeLists.txt`, and `REQUIRES` the component that owns the header. · [68317455](https://stackoverflow.com/q/68317455)
116. **A warning stops the whole build** — see: `-Werror` behaviour with no such flag in your CMake. cause: the IDF build enables `-Werror` by default, so every warning is an error. fix: add `-Wno-error` for the target, or fix the warning; suppressing it per file is the smaller change. · [70069893](https://stackoverflow.com/q/70069893)
117. **An Arduino library is missing from an IDF build** — see: `AsyncWebServer` not found although it is installed. cause: IDF compiles only what a component declares, and Arduino libraries are gated behind `CONFIG_ARDUINO_SELECTIVE_*` options. fix: enable the library in `Kconfig.projbuild` or menuconfig so the component is actually built in. · [73683184](https://stackoverflow.com/q/73683184)
118. **A hand-written linker script never reaches `app_main`** — see: the board resets when built with a custom `main.ld`. cause: the second-stage bootloader expects the IDF image header and entry point; a bare-metal layout has neither. fix: keep the IDF bootloader and replace only what you must, and debug the handoff with JTAG/OpenOCD rather than by flashing repeatedly. · [79594159](https://stackoverflow.com/q/79594159)

## Cameras (119-124)

119. **`esp_camera_init()` called twice reboots the board** — see: the camera works, then the device restarts when a PIR fires. cause: `esp_camera_init()` can be called once per boot and there is no de-init, so the second call faults. fix: initialise once in `setup()`; on a sensor event only capture, and if a re-init is genuinely needed, restart the board deliberately. · [62792183](https://stackoverflow.com/q/62792183)
120. **The ESP32-CAM stream cannot be read from OpenCV** — see: a browser shows the video, `cv2.VideoCapture` does not. cause: the sketch serves a single JPEG or an MJPEG stream on a path OpenCV does not guess. fix: serve a real `multipart/x-mixed-replace` stream on a known path and open that exact URL. · [60029614](https://stackoverflow.com/q/60029614)
121. **Pushing the camera to YouTube fails** — see: the RTSP libraries do not accept the target. cause: RTMP and RTSP are different protocols, and the Arduino RTSP libraries act as a server rather than a client that pushes to a remote. fix: pick one — serve RTSP locally, or push RTMP with a client library. · [60908201](https://stackoverflow.com/q/60908201)
122. **Uploading to the ESP32-CAM times out** — see: "Failed to connect to ESP32: Timed out waiting for packet header". cause: the USB-serial adapter cannot drive the board into download mode, or the board is not held in reset long enough. fix: hold IO0 low across a reset, use a known-good adapter, and drop the upload baud rate first. · [61828099](https://stackoverflow.com/q/61828099)
123. **Camera and cellular modem brown out together** — see: each works alone, neither works together. cause: both draw from the same 3.3 V regulator; moving to the 5 V pin does not help when the regulator is the limit. fix: give the modem its own supply with a common ground, and size the bulk capacitance for the transmit burst. · [76769836](https://stackoverflow.com/q/76769836)
124. **An LVGL canvas renders as diagonal garbage** — see: the image is skewed rather than blank. cause: the stride argument was passed as 0, so LVGL assumed a row length that does not match the buffer. fix: pass the real stride in bytes per row. · [79899105](https://stackoverflow.com/q/79899105)

## Buses: I2C, SPI, UART, OneWire (125-136)

125. **`i2c clock choice is invalid` when an OLED driver starts** — see: u8g2 on IDF refuses to initialise. cause: the driver config leaves `clk_flags` unset, so the requested frequency is rejected. fix: set `conf.master.clk_flags = 0` next to `clk_speed`. · [70111041](https://stackoverflow.com/q/70111041)
126. **"Card Mount Failed" on a microSD breakout** — see: the card reads fine in a PC. cause: many microSD modules carry their own regulator and level shifter and want 5 V on VCC; feeding 3.3 V leaves them out of spec. fix: power the module from VIN/5 V, not from the 3V3 pin. · [59992639](https://stackoverflow.com/q/59992639)
127. **`spi_bus_initialize: host already in use`** — see: the second device on the same SPI host fails. cause: the bus is initialised twice; only the first `spi_bus_initialize()` per host is allowed. fix: initialise the bus once and attach devices with `spi_bus_add_device()`. · [64368823](https://stackoverflow.com/q/64368823)
128. **Garbage on the serial line at every reset** — see: the first bytes after boot are nonsense. cause: the ROM bootloader prints its own message at a different baud rate before your sketch runs. fix: read and discard the first burst, or match the bootloader baud; it is not your data. · [59425170](https://stackoverflow.com/q/59425170)
129. **The UART interrupt fires per byte instead of per buffer** — see: the ISR runs far more often than expected. cause: the RX FIFO threshold was left at its default instead of the level you wanted. fix: set `rx_thresh` explicitly in `uart_intr_config_t` and install the handler with `uart_isr_register()`. · [74611642](https://stackoverflow.com/q/74611642)
130. **`uart_intr_config_t` is undefined** — see: the ROM UART header is missing. cause: the ROM header path differs per chip. fix: include the target-specific one (`esp32/rom/uart.h`, `esp32s2/rom/uart.h`, …) behind `CONFIG_IDF_TARGET_*`. · [62453460](https://stackoverflow.com/q/62453460)
131. **`SerialBT.readString()` returns empty the second time** — see: printing it loses the data. cause: the first call consumed the stream; a stream cannot be read twice. fix: read once into a `String`, then print that variable. · [58418969](https://stackoverflow.com/q/58418969)
132. **A DS18B20 reads a constant -127** — see: every reading is -127. cause: -127 means no device answered — wrong pin, missing 4.7 kΩ pull-up, or the sensor wired to the wrong leg. fix: 4.7 kΩ from data to 3V3, data on the pin you actually named, and confirm that pin exists on that board. · [61172204](https://stackoverflow.com/q/61172204)
133. **An analog sensor reads 0 only while Wi-Fi is on** — see: the same code works before `WiFi.begin()`. cause: the pin is on ADC2, which the radio takes over. fix: move the sensor to an ADC1 pin (GPIO32-39 on the classic ESP32). · [79157323](https://stackoverflow.com/q/79157323)
134. **`hostbyname(): dns failed` from HTTPClient** — see: the URL works in a browser. cause: `http.begin()` was handed a full URL where it expects host and port separately, so the whole string was resolved as a hostname. fix: pass host and port as separate arguments, or use the single-String overload that parses the URL. · [68508224](https://stackoverflow.com/q/68508224)
135. **A WebSocket peer cannot tell JSON from binary** — see: the receiver mis-parses frames. cause: both payload kinds go out with the same framing and no type marker. fix: prefix each frame with a one-byte type tag, or send binary as binary frames and JSON as text frames. · [73130077](https://stackoverflow.com/q/73130077)
136. **The Wi-Fi event handler runs in a storm** — see: `SYSTEM_EVENT_STA_*` repeats endlessly. cause: the handler is registered more than once, or the reconnect path immediately retriggers the same transition. fix: register once, and guard the reconnect so a failed connect does not start another immediately. · [67576386](https://stackoverflow.com/q/67576386)

## Interrupts, tasks and memory (137-145)

137. **`LoadProhibited` inside an ISR** — see: the handler crashes only sometimes. cause: the handler lives in flash, and a flash write or cache miss during an interrupt makes fetching it fault. fix: mark it `IRAM_ATTR` and keep anything it calls in IRAM too. · [69724249](https://stackoverflow.com/q/69724249)
138. **`IRAM_ATTR` is unknown in VS Code** — see: red squiggles while the build works. cause: the editor's include paths are not configured for the IDF headers. fix: point `c_cpp_properties.json` at the IDF include paths, or let the extension generate it. · [74080261](https://stackoverflow.com/q/74080261)
139. **Logging or NVS access inside an ISR** — see: `lock_acquire` assertions or a crash. cause: logging and flash access take locks and can block; neither is allowed in interrupt context. fix: set a flag or push to a queue in the ISR and do the work in a task. · [79264150](https://stackoverflow.com/q/79264150)
140. **Code after `xTaskCreate()` never runs** — see: the task body does not start either. cause: on plain FreeRTOS a created task only starts when the scheduler runs; a bare-metal build never calls `vTaskStartScheduler()`. fix: call `vTaskStartScheduler()` at the end of setup, or keep `app_main` which does it for you. · [78307599](https://stackoverflow.com/q/78307599)
141. **A large lookup table eats the heap** — see: allocation fails although the array is constant. cause: the table is copied into RAM instead of being read from flash. fix: keep it in flash and read through the accessor, or `PROGMEM` with `pgm_read_*` on Arduino. · [61559745](https://stackoverflow.com/q/61559745)
142. **Heap falls a little on every BLE scan** — see: free heap never recovers. cause: `BLEUtils::buildHexData()` allocates and returns a buffer the caller has to free. fix: free the returned pointer, or format the address without that helper. · [64708167](https://stackoverflow.com/q/64708167)
143. **Everything is slow and you cannot tell which resource ran out** — see: guessing between RAM, CPU and network. cause: no measurement. fix: track `xPortGetFreeHeapSize()` over time — a steady heap with slow responses points at CPU or the network, a falling one points at a leak. · [69374672](https://stackoverflow.com/q/69374672)
144. **MQTT over TLS connects and drops immediately** — see: error 119 straight after the handshake. cause: the broker sends FIN, which is usually a certificate or client-id rejection rather than a transport failure. fix: read the broker's reason code before touching the TLS configuration, and confirm the client id is unique. · [75299434](https://stackoverflow.com/q/75299434)
145. **MicroPython runs out of memory during a TLS handshake** — see: `MemoryError` before the connection completes. cause: the handshake needs a large contiguous block, and some builds have much less headroom than others. fix: use a build with more free heap, keep buffers small, and connect before allocating anything else. · [65960193](https://stackoverflow.com/q/65960193)

## Power, sleep and reset (146-151)

146. **Brownout the moment Wi-Fi starts** — see: a reset exactly when the radio comes up. cause: the transmit burst pulls the rail below the brownout threshold. fix: bigger bulk capacitor, a supply that can deliver the peak, and no LEDs on the same rail. · [58902331](https://stackoverflow.com/q/58902331)
147. **A bootloop after enabling secure boot** — see: the same project flashes and runs without it. cause: the image was built without the matching secure-boot configuration, so the ROM rejects it. fix: rebuild the whole chain with secure boot enabled, including the bootloader, and flash it in one go. · [48596147](https://stackoverflow.com/q/48596147)
148. **NVS encryption needs two partitions, not one** — see: the encrypted NVS partition will not mount. cause: NVS encryption uses its own keys partition, separate from the data partition. fix: add an `nvs_keys` partition and generate the keys before enabling encryption. · [69952750](https://stackoverflow.com/q/69952750)
149. **`EnableWakeupByPin()` does nothing** — see: the board sleeps and never wakes. cause: in nanoFramework the call has been observed not to arm the wake source. fix: configure the pin and wake source in the order the documentation gives, and verify the wake cause after boot rather than assuming it fired. · [64210760](https://stackoverflow.com/q/64210760)
150. **Light sleep wake fails on a C6 super-mini** — see: the board does not come back. cause: the wake source and the pin configuration have to agree with the chip, and the C6 pin map is not the classic one. fix: check the wake-capable pins for that specific chip before wiring, and confirm the wake cause in the reset reason. · [79448665](https://stackoverflow.com/q/79448665)
151. **Wi-Fi connects on every other attempt** — see: `assoc -> init (0x2c)` on the failing runs. cause: the station is re-initialised instead of retried, so the association is torn down mid-flight. fix: watch the state transition rather than the return code, and retry from `init` with a delay instead of immediately. · [78808438](https://stackoverflow.com/q/78808438)

## Tooling, build and debug (152-160)

152. **JTAG connects but the debugger never reaches `main`** — see: the session stops early. cause: the interface is wired correctly but the openocd configuration or the board's strapping does not match. fix: start from Espressif's JTAG debugging example for that exact chip rather than adapting a generic config. · [66554440](https://stackoverflow.com/q/66554440)
153. **OpenOCD cannot see an ESP32-C3** — see: the debugger fails to read JTAG data. cause: the Microsoft libusb driver (10.x) does not work with the on-board USB-JTAG on this chip. fix: replace it with the 6.x driver through Zadig, then reconnect. · [79440857](https://stackoverflow.com/q/79440857)
154. **`gpio_new_pin_glitch_filter` is undefined** — see: the function exists in the docs. cause: it was added in ESP-IDF 5.1, and the Arduino core in use was built on 2.0.14. fix: check which IDF the framework was built on before using an API from the docs; upgrade or implement the filter yourself. · [77358619](https://stackoverflow.com/q/77358619)
155. **Unit-testing your own code with the IDF test framework** — see: the harness assumes it is testing IDF components. cause: `unity` and the test runner are set up for in-tree components, not for an application. fix: keep your tests in their own component with a `test` app, or run them on the host where the logic does not need hardware. · [51176779](https://stackoverflow.com/q/51176779)
156. **`esp_log_set_vprintf` does nothing on Arduino** — see: the redirect is ignored. cause: the Arduino core initialises logging differently from a plain IDF app. fix: install the vprintf hook and route it to your own sink; several people have posted working wrappers for exactly this. · [60442350](https://stackoverflow.com/q/60442350)
157. **`httpd` URI wildcards do not match** — see: a registered handler is never called. cause: wildcard matching is disabled by default in the HTTP server config. fix: set `config.httpd.uri_match_fn = httpd_uri_match_wildcard` before `httpd_start()`. · [77711387](https://stackoverflow.com/q/77711387)
158. **An encryption helper truncates at 21 bytes** — see: only part of the input is encrypted. cause: the buffer size constant was the signature length (256 for a 2048-bit key) but the function expected a different unit. fix: pass the length the API documents, in the unit it documents. · [76113716](https://stackoverflow.com/q/76113716)
159. **`WiFiClient` cannot reach a service on your PC** — see: the browser works, the ESP32 does not. cause: the PC's firewall blocks the port, or the ESP32 is on a different subnet (a phone hotspot versus the LAN). fix: check both are on the same subnet, then allow the port through the firewall. · [70302464](https://stackoverflow.com/q/70302464)
160. **A copied project will not build** — see: ninja and CMake errors after moving the folder. cause: the build directory still holds absolute paths from the old location. fix: delete the build directory and let CMake recreate it. · [65549638](https://stackoverflow.com/q/65549638)
