"""Lossless conversions for the keyboard's little-endian RGB565 format."""
import numpy as np
from PIL import Image

def encode(image):
    a = np.asarray(image.convert("RGB"), dtype=np.uint16)
    words = (((a[..., 0] * 31 + 127) // 255 << 11)
             | ((a[..., 1] * 63 + 127) // 255 << 5)
             | ((a[..., 2] * 31 + 127) // 255))
    return words.astype("<u2").tobytes()

def decode(data, width, height):
    a = np.frombuffer(data, dtype="<u2").reshape(height, width).astype(np.uint32)
    r, g, b = (a >> 11) & 31, (a >> 5) & 63, a & 31
    return Image.fromarray(np.stack([(r << 3) | (r >> 2),
                                    (g << 2) | (g >> 4),
                                    (b << 3) | (b >> 2)], -1).astype(np.uint8))
