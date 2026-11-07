# Panic and reset reasons

## Panic reasons

The reason inside `panic'ed (...)` is the diagnosis. Everything else in the dump
is detail.

| Reason | What it means | First thing to check |
|---|---|---|
| `LoadProhibited` | Read through an invalid pointer | `EXCVADDR`: `0x0` is a null dereference, a small value like `0x4` is a null plus a struct field, a heap-looking address is a use-after-free |
| `StoreProhibited` | Write through an invalid pointer | Usually a buffer overrun or a write to a const; check array bounds and `strcpy` |
| `IllegalInstruction` | Executed data as code | A corrupted function pointer, or a stack overflow that overwrote a return address |
| `InstrFetchProhibited` | Jumped to a non-code address | Same as above, usually a callback that was never set |
| `IntegerDivideByZero` | Division by zero | The divisor came from a sensor or a config value that is 0 |
| `Unhandled debug exception` | Breakpoint or watchpoint | A stray `asm("breakpoint")`, or a JTAG watchpoint left enabled |
| `Cache disabled but cached memory region accessed` | Flash access while the cache was off | An ISR or a callback running during a flash write that touches a string constant |
| `Stack canary watchpoint triggered` | Stack overflow | The task's stack is too small for what it does |

## Reset reasons

The `rst:` line at boot says how the chip got here, and it is the fastest way to
separate a firmware bug from a hardware problem.

| Value | Meaning |
|---|---|
| `rst:0x1 (POWERON_RESET)` | Cold boot. Normal after power is applied. |
| `rst:0x3 (SW_RESET)` | Software reset, typically `ESP.restart()`. |
| `rst:0xc (SW_CPU_RESET)` | CPU reset from software, usually after a panic. |
| `rst:0x8 (TG1WDT_SYS_RESET)` | Task watchdog fired. A task blocked too long. |
| `rst:0x7 (TG0WDT_SYS_RESET)` | The other core's task watchdog fired. |
| `rst:0x10 (RTCWDT_RTC_RESET)` | RTC watchdog. Often a boot loop after a bad image. |
| `rst:0xf (BROWNOUT_RESET)` | Supply dipped below the brownout threshold. Hardware. |
| `rst:0x5 (DEEPSLEEP_RESET)` | Woke from deep sleep. Normal. |

A board that prints `BROWNOUT_RESET` and then boots fine is not fixed by adding
a `delay()`; it needs a bigger capacitor or a supply that can deliver the radio
peaks.

## Decoding workflow

1. Read the `rst:` line and the panic reason. That usually narrows it to one of
   three or four candidate lines of code.
2. Extract the backtrace addresses and run them through `addr2line` with the
   exact ELF that was flashed. `tools/panic_decode.py` prints the command.
3. Add `monitor_filters = esp32_exception_decoder` to `platformio.ini` so step 2
   happens automatically from then on.
4. If the crash is intermittent, enable the core dump to flash and read it back
   with `esp-coredump info` instead of adding print statements.

## What not to do

- Do not "fix" a watchdog by feeding it. A watchdog firing means a task is
  blocking; feeding the dog hides the symptom until the queue behind it grows.
- Do not decode with a freshly built ELF. If the firmware changed since the
  crash, every line number is wrong and looks convincing.
- Do not add a null check without saying why the pointer was null. The check
  hides the bug that produced the null.
