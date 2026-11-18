---
name: esp32-multicore-and-ipc
description: Use when code behaves differently depending on which core it runs on - a task starves the Wi-Fi stack, a shared variable corrupts, a queue overflows, or a task never runs at all. Covers affinity, priorities, spinlocks and ISR dispatch.
license: MIT
---

# Two cores on ESP32

The classic ESP32 and the S3 have two cores. The C3, C6 and S2 have one, so code
that assumed two cores silently becomes cooperative - and a blocking task that
was fine on core 1 now stops the radio.

## Core 0 belongs to the radio

The Wi-Fi and Bluetooth stacks run on core 0 at high priority. A busy loop pinned
to core 0 starves them and the symptom is not "slow Wi-Fi", it is a watchdog
reset or a disconnect every few seconds. Pin application work to core 1.

`xTaskCreatePinnedToCore(..., 1)` for anything that computes, and leave core 0
alone unless you are writing a driver.

## Priorities are absolute, not fair

A task at priority 10 that never blocks prevents every task below it from
running, forever. `vTaskDelay(1)` is the cheapest yield that still lets lower
tasks run; `taskYIELD()` only helps equal priorities.

The IDF default for `loopTask` is priority 1. A driver task at 5 that waits on a
semaphore is fine; a driver task at 5 that spins is not.

## Sharing data between cores

- `volatile` is not a lock. It stops the compiler caching the value; it does not
  make a 32-bit read-modify-write atomic.
- Use a mutex for structures, a `portMUX_TYPE` spinlock for a few variables
  touched from an ISR, and a queue when you can - it is the only one that also
  gives you backpressure.
- Never take a mutex inside an ISR. Never call `delay()` while holding a spinlock.

## The ISR is not a task

An ISR runs on whichever core took the interrupt, with interrupts disabled. It
must do the minimum and hand off:

- `IRAM_ATTR` on the handler, or it may not be in memory when flash is busy.
- `xQueueSendFromISR` / `xTaskNotifyFromISR`, then `portYIELD_FROM_ISR`.
- No `printf`, no `malloc`, no flash access, no I2C transaction.

A `printf` in an ISR works on the bench and crashes during an OTA write, because
the log goes to flash-backed buffers.

## Queues: the overflow is the design

A queue of 10 items between a 100 Hz producer and a 10 Hz consumer is not a
queue, it is a delay. Decide what happens on overflow before it happens: drop the
oldest (sensor data), block the producer (commands), or grow (nothing - it will
fill too).

| Symptom | Usually |
|---|---|
| Wi-Fi drops under load | work pinned to core 0 |
| one task never runs | a higher-priority task never blocks |
| values corrupt, no crash | shared struct without a lock |
| crash inside an ISR | log, malloc or flash access in the handler |
| works on C3, fails on ESP32 | code assumed a single core, or vice versa |

## Cross-core scheduler suspension and flash interactions

Two November 2026 reports expose distinct SMP lost-wakeup paths. A task being Ready does not mean it will run while its pinned core has suspended its scheduler.

- In [ESP-IDF #19450](https://github.com/espressif/esp-idf/issues/19450), ESP32-S3 rev0.2 on IDF v6.1 (the same code was reported in master and release/v5.5) can leave a core-1 pinned task blocked after vTaskNotifyGiveFromISR(), xTaskNotifyFromISR() or xTaskResumeFromISR() runs on core 0 while core 1 has suspended its scheduler. The report traces the task to xPendingReadyList[xCurCoreID]; xTaskResumeAll() on core 1 drains its own list.
- The proposed ISR-path fix is [PR #19451](https://github.com/espressif/esp-idf/pull/19451), commit 7266fdc, still open against master at this scan. On S3 rev0.2 / IDF v6.1, the new SMP test passes with the patch; late wake-ups fell from 19–20 per 2 s to zero and the largest gap from 49,994 µs to 1,530 µs. This PR changes ISR pending-ready-list ownership.
- In [ESP-IDF #19456](https://github.com/espressif/esp-idf/issues/19456), ESP32-S3 rev0.1 on v6.3-dev and v5.3 (not v5.2.2) can leave ipc1 Ready but never scheduled while a core-1 task continuously reads flash through esp_partition_read(). A 1 kHz esp_timer callback on core 0 blocks in synchronous esp_ipc_call(1, ...), so all timer callbacks stop until core 1 reschedules.
- The separate task-context fix is [PR #19457](https://github.com/espressif/esp-idf/pull/19457), commit dfaa88f, also open against master. On S3 rev0.1 / v6.3-dev, its new test passes and the #19456 reproducer completed 59,001 IPC calls in 60 seconds without a stall; without the fix it stalled on the first call. This PR changes SMP preemption/yield-pending behavior, not the ISR pending-ready-list path.

PR #19451 does not fix the task-context path in #19456, and PR #19457 does not fix the ISR path in #19450. Neither was merged or mapped to a released IDF version at this scan. Treat both as high-risk FreeRTOS SMP changes: pin the exact commit, review the patch and run the matching on-target test before adopting it.

Do not treat either report as a universal FreeRTOS rule. Preserve the exact IDF revision, task affinity, scheduler-suspend interval, flash API and ISR core. Avoid unbounded busy loops on a core that must service IPC, and do not put a potentially blocking cross-core esp_ipc_call() in a periodic timer callback without a bounded, target-tested handoff. A semaphore control path in #19450 behaved differently in that reproducer; validate the chosen primitive on the exact release rather than assuming every queue, notification or semaphore path is equivalent.

