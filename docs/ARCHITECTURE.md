# Architecture

The implementation has three separate layers.

1. Python renders the reviewed 240 × 135 screens. Shapes are supersampled, type is rasterized at device size, and final colours are quantized to RGB565.
2. Firmware patches route the vendor display queue to new drawing code, while using the existing input and effect-apply behavior. A cooperative adapter waits for LCD completion across queue visits, avoiding overlapping asynchronous transfers.
3. Windows transport programs the MCU and uploads the corresponding graphics prefix. The browser has no connection to this transport.

## Firmware representation

`firmware/patches.json` is the authoritative set of reviewed byte replacements against one stock SHA-256. Each replacement includes its expected original bytes; ranges must be ordered, bounded and nonoverlapping. The builder checks the complete output hash and word checksum.

`firmware/assembly/` contains the drawing and queue implementation references from the integration work. It is not a standalone replacement for the vendor firmware, and the public build does not reassemble these files. Code changes require regenerating and reviewing the byte patch specification.

`firmware/clock_sprites.json` records the generated date, battery and status sprites. The dynamic clock combines these sprites with time numerals, rather than storing a full frame per minute.

## Graphics representation

`assets/graphics/atlas.png` is a lossless raster representation of the complete project-generated prefix, including baked dynamic clock sprites and earlier generated allocations. It contains no vendor graphics dump. Converting its RGB pixels to little-endian RGB565 and trimming to the declared byte length reproduces the exact reference prefix.

`assets/graphics/layout.json` maps all 134 screen states to addresses and rectangles. The build checks every active allocation against the native PNG source before producing output. Connection and Effect use full frames so a separate black clear does not flash before the new frame.

The prefix ends before the original custom-animation region. This address constraint does not imply that a firmware patch is compatible with another regional layout.

## Effect namespaces

Local menu IDs are 0–19, ordered Static through Shuttle and LED Off. Host-protocol IDs are 1–19 for the effects and 0 for Off. These are separate from internal lighting-engine state identifiers. The exact translation lives in `assets/effect_modes.json`; labelling menu 0 as Off was the earlier defect.

## Boundaries

The emulator checks selected CPU execution and modeled peripherals, not the entire physical keyboard. LCD ACKs cannot validate visual appearance. A host information dashboard would require a companion protocol; it is not in the current image.
