# LoRa and Sub-GHz Radio Planning Dossier

## Radio selection

Do not group all sub-GHz radios under the LoRa label. SX127x/SX126x devices support LoRa modulation as well as selected other modes; CC1101 is a configurable narrowband transceiver and is not a LoRa modem. Driver APIs, packet engines and RF characteristics are not interchangeable.

Record exact radio IC, module vendor/part number, crystal or TCXO, frequency band, RF switch, antenna connector and board revision. Confirm the module schematic rather than assuming the development board's pinout or RF path.

## Link budget

Estimate EIRP from conducted output power, feed loss and antenna gain. Compare expected receive power with sensitivity for the selected modulation and bandwidth, then reserve fade margin for installation, weather, foliage, polarization and interference. Use measured RSSI/SNR and packet delivery ratio to validate the link; a single long-distance packet is not a range guarantee.

## Airtime and legal constraints

Time-on-air depends on payload length, preamble, bandwidth, spreading factor, coding rate, header and CRC settings. Count retransmissions, acknowledgements, join traffic and downlinks in the duty-cycle budget. Frequency plan, EIRP, duty-cycle, dwell-time and listen-before-talk rules vary by region. Verify the current rules for the deployment jurisdiction and radio service.

## Packet reliability

Use bounded payloads, explicit version/type fields, sequence numbers and CRC at the application layer where appropriate. Define duplicate suppression, ACK policy, retry count and randomized backoff. Avoid synchronized retry storms across fleets. For LoRaWAN, use a maintained stack and the correct regional parameters; do not implement network security by copying a point-to-point example.

## SX126x-specific bring-up

Respect BUSY handshaking and command timing. Validate reset, TCXO, RF switch and DIO1 routing. Capture RESET, BUSY, NSS/SCK/MOSI/MISO and DIO1 to separate command sequencing faults from RF link failures.

## CC1101-specific bring-up

Configure frequency, modulation, deviation, channel bandwidth, data rate, sync word, packet length and CRC consistently on both ends. Handle FIFO overflow/underflow and GDO events without doing long SPI transactions in an ISR.

## Sources

- Semtech SX1261/SX1262 product and documentation: https://www.semtech.com/products/wireless-rf/lora-connect/sx1262
- TI CC1101 product and datasheet: https://www.ti.com/product/CC1101
- LoRa Alliance regional parameters: https://lora-alliance.org/resource_hub/rp002-1-0-4-regional-parameters/
- EU radio equipment regulatory framework: https://single-market-economy.ec.europa.eu/sectors/electrical-and-electronic-engineering-industries-eei/radio-equipment-directive-red_en

## Evidence boundary

Regulatory compliance must be checked for the exact country, frequency, antenna and product category. This dossier does not certify RF emissions, receiver performance or LoRaWAN interoperability.
