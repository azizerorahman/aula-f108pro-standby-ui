# Validation and current limits

## Public export checks

The repository's tests verify:

- Asset dimensions, manifest hashes, RGB565 round trips and all 134 regenerated screens.
- The 20-entry native effect order, including LED Off at menu ID 19.
- Graphics atlas reconstruction, allocation correspondence and the custom-animation boundary.
- Ordered, bounded byte patches and rejection of an unsupported stock image.
- No image EXIF/text metadata, private workspace paths, local network addresses or obvious credential files.
- Relative documentation links and offline preview navigation.

The local export also reproduced the exact MCU and graphics hashes from the development build. Default Windows transport verification exercises seven simulated transfer scenarios without opening a device. CI does not download or redistribute proprietary firmware and does not program hardware.

## Historical engineering evidence

Earlier isolated checks recorded 970 asynchronous display cases, 80 native knob cases, 40 lighting checks, 261 browser/asset checks and seven transport scenarios. These counts belong to those specific test harnesses, not to the smaller public export test suite. Raw session and device records are deliberately excluded.

The development hardware displayed the large clock, square menus and settings. Earlier defects included overlapping LCD DMA, incorrect clock startup routing, a Connection black-clear flash and an Off-first label mismatch. Corrections exist in the published patch and graphics reference.

## Pending hardware checks

The latest graphics upload received 1,807 page replies plus Apply/Finalize replies. There is no SPI readback checksum. The last record still requires physical LED Off/effect correspondence, Connection idle/selection flicker, typing/knob regression and reconnect-persistence checks.

Neither USB enumeration nor a CPU emulator proves complete keyboard operation. Radio behavior, electrical LED output, long-run stability and other hardware revisions need separate validation. See the aggregate [validation record](validation.json).
