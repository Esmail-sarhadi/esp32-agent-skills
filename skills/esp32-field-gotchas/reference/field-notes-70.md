# Seventy ESP32 failures, with the cause and the fix

Collected from the questions people actually ask on Stack Overflow, each entry
linked to the thread where the answer was worked out. Read by symptom.

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

They are the questions with the most votes and the most answers in the `esp32`
tag, filtered to the ones where the accepted answer names a concrete cause
rather than "try another library". Every entry above was checked against the
thread it links to.

The pattern worth noticing: almost none of them are about the code being wrong.
They are about the board being a physical object — a supply that sags, a pin
that is not a GPIO, a radio that takes the ADC away, a flash that wears out.
An agent that only reads the code cannot see any of that.
