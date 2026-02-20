# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
from pathlib import Path
import zlib
import struct


def write_png(path: Path, size=(192, 192), color=(124, 58, 237, 255)) -> None:
    w, h = size
    raw = b"".join(b"\x00" + bytes(color) * w for _ in range(h))

    def chunk(t: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + t + data + struct.pack(">I", zlib.crc32(t + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9))
    png += chunk(b"IEND", b"")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)


def main():
    root = Path(__file__).resolve().parent.parent / "web_ui" / "icons"
    write_png(root / "icon-192.png", (192, 192), (124, 58, 237, 255))
    write_png(root / "icon-512.png", (512, 512), (6, 182, 212, 255))
    print(f"Wrote icons to {root}")


if __name__ == "__main__":
    main()

