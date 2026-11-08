"""Reproduce the reference payloads from a separately obtained stock binary. No USB."""
from pathlib import Path
import argparse, hashlib, json, struct, sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from PIL import Image
from standby_ui.rgb565 import encode

sha = lambda b: hashlib.sha256(b).hexdigest()

def build(base, output):
    spec = json.loads((ROOT / "firmware/patches.json").read_text())
    original = base.read_bytes()
    if len(original) != spec["base"]["size"] or sha(original) != spec["base"]["sha256"]:
        raise ValueError("Unsupported stock firmware. Expected the exact CH 1.07 .bin SHA-256 in firmware/patches.json.")
    fw = bytearray(original)
    last = 0
    for patch in spec["patches"]:
        offset = patch["offset"]
        expected, data = bytes.fromhex(patch["expected_hex"]), bytes.fromhex(patch["data_hex"])
        if offset < last or len(data) != len(expected) or offset + len(data) > len(fw):
            raise ValueError("Invalid or overlapping patch region")
        if original[offset:offset + len(expected)] != expected:
            raise ValueError("Patch preimage mismatch")
        fw[offset:offset + len(data)] = data
        last = offset + len(data)
    if sha(fw) != spec["output"]["sha256"]:
        raise ValueError("Patched firmware hash mismatch")
    checksum = sum(struct.unpack("<%dH" % (len(fw) // 2), fw)) & 65535
    if checksum != spec["output"]["sum16_le"]:
        raise ValueError("Firmware word checksum mismatch")
    layout = json.loads((ROOT / "assets/graphics/layout.json").read_text())
    spi = encode(Image.open(ROOT / layout["atlas"]))[:layout["bytes"]]
    if sha(spi) != layout["sha256"]:
        raise ValueError("Graphics atlas hash mismatch")
    if len(spi) % 4096 or len(spi) >= layout["custom_animation_start"]:
        raise ValueError("Graphics cross the custom animation boundary")
    catalog = json.loads((ROOT / "assets/manifest.json").read_text())
    lookup = {m["id"]: m for m in catalog["screens"]}
    for entry in layout["screens"]:
        m = lookup[entry["id"]]
        p = ROOT / m["file"]
        if sha(p.read_bytes()) != m["sha256"]:
            raise ValueError("Screen changed; update the reviewed graphics allocation before building: " + m["id"])
        x, y, w, h = entry["rect"]
        raw = encode(Image.open(p).crop((x, y, x + w, y + h)))
        address = entry["address"]
        if spi[address:address + len(raw)] != raw:
            raise ValueError("Graphics allocation mismatch: " + m["id"])
    output.mkdir(parents=True, exist_ok=True)
    (output / "standby-mcu.bin").write_bytes(fw)
    (output / "standby-graphics.bin").write_bytes(spi)
    record = {"firmware_sha256": sha(fw), "graphics_sha256": sha(spi),
              "sum16_le": checksum, "graphics_pages": len(spi) // 4096,
              "device_opened": False}
    (output / "build.json").write_text(json.dumps(record, indent=2) + "\n")
    return record

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base", type=Path, required=True, help="Exact stock SN32F290_CH.bin, obtained separately")
    p.add_argument("--out", type=Path, default=ROOT / "dist")
    a = p.parse_args()
    print(json.dumps(build(a.base, a.out), indent=2))
