# Partition layouts that pass the checker

Every layout on this page was validated with
`python tools/partition_check.py --file <file> --flash <size> --ota` and reports
no errors. Copy one, change the names if you like, then run the checker again.

Rules that apply to all of them:

- The bootloader owns `0x1000` and the partition table owns `0x8000` (4 KB), so
  nothing starts below `0x9000`.
- App partitions start on a 64 KB boundary.
- The two OTA slots must be the same size, and each must be at least as large as
  the binary. `pio run -t size` prints the binary size.

## 2 MB — OTA without a filesystem

```csv
nvs,      data, nvs,     0x9000,  0x4000,
otadata,  data, ota,     0xd000,  0x2000,
app0,     app,  ota_0,   0x10000, 0xF0000,
app1,     app,  ota_1,   0x100000,0xF0000,
```

| Partition | Offset | Size |
|---|---|---|
| nvs | 0x9000 | 16 KB |
| otadata | 0xD000 | 8 KB |
| app0 | 0x10000 | 960 KB |
| app1 | 0x100000 | 960 KB |

960 KB per slot is the honest limit here. An Arduino build with Wi-Fi, a TLS
stack and a display driver is already close to it, which is why most 2 MB boards
ship without OTA.

## 4 MB — the common case

```csv
nvs,      data, nvs,      0x9000,   0x5000,
otadata,  data, ota,      0xe000,   0x2000,
app0,     app,  ota_0,    0x10000,  0x140000,
app1,     app,  ota_1,    0x150000, 0x140000,
spiffs,   data, spiffs,   0x290000, 0x160000,
coredump, data, coredump, 0x3F0000, 0x10000,
```

| Partition | Offset | Size |
|---|---|---|
| nvs | 0x9000 | 20 KB |
| otadata | 0xE000 | 8 KB |
| app0 | 0x10000 | 1280 KB |
| app1 | 0x150000 | 1280 KB |
| spiffs | 0x290000 | 1408 KB |
| coredump | 0x3F0000 | 64 KB |

1280 KB per slot fits most Arduino projects with room to grow. Drop `coredump`
first if you need space; it costs 64 KB and only helps after a crash.

## 8 MB

```csv
nvs,      data, nvs,      0x9000,   0x5000,
otadata,  data, ota,      0xe000,   0x2000,
app0,     app,  ota_0,    0x10000,  0x200000,
app1,     app,  ota_1,    0x210000, 0x200000,
spiffs,   data, spiffs,   0x410000, 0x3F0000,
```

| Partition | Offset | Size |
|---|---|---|
| app0 | 0x10000 | 2 MB |
| app1 | 0x210000 | 2 MB |
| spiffs | 0x410000 | 4032 KB |

## 16 MB

```csv
nvs,      data, nvs,      0x9000,   0x5000,
otadata,  data, ota,      0xe000,   0x2000,
app0,     app,  ota_0,    0x10000,  0x400000,
app1,     app,  ota_1,    0x410000, 0x400000,
spiffs,   data, spiffs,   0x810000, 0x7F0000,
```

| Partition | Offset | Size |
|---|---|---|
| app0 | 0x10000 | 4 MB |
| app1 | 0x410000 | 4 MB |
| spiffs | 0x810000 | 8128 KB |

## The arithmetic, once

For a slot of size `S` starting at `O`, the next partition starts at `O + S`,
and that value must land on a 64 KB boundary. With power-of-two sizes and a
power-of-two start, it does automatically; the mistakes happen when a size is
written as a decimal like `1200000` instead of `0x140000`.

If you are unsure, run the checker. It prints the table with computed offsets
and refuses to pass a layout that overlaps or overflows.
