# Build and installation

This is a developer-oriented experimental build. It changes both the keyboard MCU firmware and the external screen graphics. A settings factory reset does not reinstall either payload.

## Compatibility

Read [COMPATIBILITY.md](COMPATIBILITY.md). The supported build input is exactly:

```text
SN32F290_CH.bin — 262144 bytes
SHA-256 6e26153a5206bb4b4a001c4634609aee1025f02f84aa7808abe92dc91f60a663
```

Obtain the original separately. The [upstream research project](https://github.com/AuRoN89/AULA-F108-PRO-Reverse-Engineering/tree/main/Files/Firmware) documents its firmware references. Do not substitute the similarly named Intel HEX file: it is a different payload.

The installation wrapper checks for one revision-0107 keyboard. It intentionally stops on another revision rather than assuming a public binary is equivalent to that hardware's factory firmware. The development keyboard originally reported 0108 and was later programmed with a 1.07-based build; that single result does not establish support for all 0108 units.

## 1. Build offline

Use Python 3.12 or later (the reference environment is Python 3.12):

```sh
python -m pip install -r requirements.txt
python tools/build_firmware.py --base /path/to/SN32F290_CH.bin
python -m unittest discover -s tests -v
python tools/check_project.py
```

Outputs:

| File | SHA-256 |
| --- | --- |
| `dist/standby-mcu.bin` | `4383291939280af6d30fc962cdf60cf64d531ae10dcd56c2a99ed7ba9dd4a62b` |
| `dist/standby-graphics.bin` | `5cda49967d090aaeeaf564a47aa47890955ede7e9315165356c61361f7c92c0b` |

The firmware's little-endian 16-bit word sum is `0x2BEF`. Graphics occupy 1,807 4 KiB pages and end at `0x70F000`, before the custom-animation start at `0x740000`.

These exact hashes are pinned in the transport. Artwork changes require a new reviewed allocation, patch and matching transport pins.

## 2. Verify the Windows transport offline

In Windows PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/Install-Standby.ps1 -Mode Verify
```

Verify compiles the C# transport, validates both payload hashes and exercises simulated success/failure transfers. It opens no physical device. The scenarios cover wrong chip, MCU checksum failure, interrupted MCU transfer, graphics page rejection, short write and Apply failure.

## 3. Inspect the connected keyboard

Use a wired USB data connection and close the AULA control application; concurrent vendor traffic previously interfered with updater replies. Keep another input device available during development.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/Install-Standby.ps1 -Mode Inspect
```

Inspect opens matching HID interfaces to check descriptor geometry, without programming. It requires vendor/product `0C45:800A`, revision `0107`, command usage `FF13` and interrupt-data usage `FF68`. Multiple candidate keyboards, another revision, missing interfaces or the running vendor app stop the wrapper.

## 4. Install the matching pair

Review the source and physical compatibility first. Keep power and USB stable during the transfer:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/Install-Standby.ps1 -Mode Install
```

The sequence is MCU programming, full-image word-checksum validation, return to application mode, graphics upload, Apply and Finalize. The screen may look wrong between the two payloads. The MCU transport preserves the identified option bytes. On an incomplete MCU transfer it avoids starting an unverified application.

Local progress/receipts go into ignored `private/`. A graphics ACK verifies a protocol reply; there is no screen-flash readback checksum. A completed transfer is not complete hardware acceptance. The public wrapper is a portable export of the transport and has been verified in mocked mode; it has not itself been installed across a fleet of keyboards.

## 5. Physical acceptance

Check typing, modifier keys, knob turn/press/back and the live blinking clock. Sweep all menu pages and both languages. Leave Connection open while idle, then move through every option. Test all effects, especially LED Off under the keys; side/logo lighting is separate. Try a reactive effect with real key presses. Change a setting, reconnect, and check persistence. Check wireless modes separately.

Final physical acceptance of the latest mapping and flicker correction remains pending in the development record.

## If a transfer fails

Save the local error and stage without publishing raw device paths. Do not repeatedly send arbitrary updater commands. Update-entry commands can suspend normal keyboard operation, even before flash is erased. An unresponsive application was previously restored by a power cycle; this does not establish recovery from an interrupted erase/program operation.

A firmware dump from another region and the vendor app's factory-reset button are not verified full recovery images for every unit. This project does not claim guaranteed recovery.
