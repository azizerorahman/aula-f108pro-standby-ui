# Compatibility

| Item | Current evidence |
| --- | --- |
| Product | AULA F108 Pro with 240 × 135 display |
| MCU family | Sonix SN32F290 / Cortex-M0 research baseline |
| Vendor/product | `0C45:800A` |
| Reference firmware input | Chinese 1.07, exact SHA-256 in `firmware/patches.json` |
| Public installation wrapper | USB revision 0107 only |
| Original development device | Reported 0108 before a 1.07-based update |
| Other regional firmware/hardware | Not verified |
| Host transport | Windows PowerShell and Windows HID APIs |
| Artwork / preview / offline build | Python; no Windows-only dependency |
| Languages | English and Simplified Chinese |

USB revision is identification evidence, not proof of firmware or flash-layout equivalence. The Korean reference graphics and Chinese firmware have different UI arrangements. Firmware patches use absolute addresses; using them on an unrecognized binary is unsupported and the builder rejects it.

The browser can demonstrate connection modes and platform choices without verifying the corresponding physical radio behavior. Windows/macOS/iOS/Android symbols identify key-layout options, not automatic detection of the connected computer.
