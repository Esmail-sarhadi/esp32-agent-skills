---
name: esp32-dma-cache-psram
description: Use when debugging DMA failures, PSRAM buffers, cache coherency, alignment, camera, SPI, I2S or peripheral transfer corruption.
license: MIT
---

# Dma Cache Psram

DMA-capable memory and external PSRAM are not interchangeable on every ESP32 target. Memory capability, alignment, cache state and peripheral restrictions vary by SoC and IDF release.

## Memory capabilities

Allocate buffers using documented capability flags for the selected target and driver. Check whether a peripheral can DMA directly to PSRAM or requires internal DMA-capable SRAM. Do not infer behavior from another ESP32 family or Arduino core version. Record alignment and transfer-size constraints.

## Cache coherency

For targets with cache-coherency or cache-maintenance requirements, follow the peripheral driver's documented synchronization path. Do not manually flush/invalidate cache unless the architecture and API require it. Ownership transitions must be explicit: CPU writes then DMA reads; DMA writes then CPU reads.

## Buffer lifecycle

Keep DMA buffers alive until completion callback/event. Do not return stack buffers or free memory while a transfer is in flight. Use ping-pong/double buffering for streaming and define backpressure when consumers are slower than producers. Avoid heap allocation in high-frequency callbacks.

## Diagnostics

Log allocation capability, address alignment, size, largest free block and DMA error code. Test minimum and maximum transfer sizes, with PSRAM enabled/disabled and under memory pressure. Compare internal-RAM baseline with PSRAM path to isolate capability problems.

## Agent rules

Never promise DMA from PSRAM without target/driver documentation. Do not use a pointer after transfer ownership ends. Include explicit lifetime, alignment and buffer-capacity contracts in examples.

## Field evidence to capture

- Record the exact ESP32 SoC, module, board revision and schematic revision.
- Record framework, compiler, driver version and relevant configuration flags.
- Preserve raw measurements and error codes before applying filters or retries.
- Separate a suspected cause from a reproduced root cause and a verified fix.
- Link the test result to a reproducible fixture or documented manual procedure.

## Version and safety boundary

Check the selected target's datasheet, errata and framework release notes before choosing APIs or pin capabilities. Electrical protection, isolation, overcurrent limits and safe outputs must be designed independently of firmware. A passing host test is not evidence of electrical compliance or field reliability.


## P4 JPEG encoder cache-ownership report (2026-11-25)

[ESP-IDF #19496](https://github.com/espressif/esp-idf/issues/19496) is an open, reporter-specific report for ESP32-P4 rev1.3 / ESP-IDF v6.0.1. Under competing PSRAM traffic, jpeg_encoder_process() reportedly returns ESP_OK while a 64-byte cache-line-aligned zero block corrupts the compressed payload (about 1 in 100 busy encodes).

The proposed mechanism is a dirty zero line left by jpeg_alloc_encoder_mem() being written back after 2D-DMA has produced the same line. This is the reporter's source analysis, not yet a maintainer-confirmed root cause.

Before accepting a fix, verify the driver's cache/ownership contract: preserve the CPU-written header, synchronize only the aligned DMA payload before enqueue, and do not invent cache operations for another SoC. The report compares the encoder with decoder/PPA paths that invalidate output before DMA.

Regression: encode identical frames with and without PSRAM contention; compare raw bytes/hashes and decoded images; sweep alignment and output size; record exact IDF commit and cache-line behavior. The issue had no maintainer response at this scan.
