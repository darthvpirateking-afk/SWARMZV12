# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
# filepath: tools/show_mobile_qr.py
"""
Generate a QR code for accessing SWARMZ on mobile.
"""

import socket
import qrcode


def get_local_ip():
    hostname = socket.gethostname()
    return socket.gethostbyname(hostname)


def generate_qr_code():
    try:
        ip = get_local_ip()
        url = f"http://{ip}:8765"
        qr = qrcode.make(url)
        qr.show()
        print(f"Access SWARMZ at: {url}")
    except Exception as e:
        print(f"Failed to generate QR code: {e}")


if __name__ == "__main__":
    generate_qr_code()
