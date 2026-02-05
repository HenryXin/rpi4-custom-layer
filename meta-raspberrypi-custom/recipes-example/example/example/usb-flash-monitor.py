#!/usr/bin/env python3
"""
USB flash drive monitor: print 1 every second when a USB flash drive is
detected on Bus 002 Port 001 only, otherwise print 0.
"""

import os
import sys
import time

# Bus 002 Port 001 = sysfs port "2-1". Override with env USB_FLASH_PORT if needed.
USB_PORT = os.environ.get("USB_FLASH_PORT", "2-1")


def block_dev_is_removable(block_name):
    """Return True if /sys/block/<name> is removable."""
    path = os.path.join("/sys/block", block_name, "removable")
    try:
        with open(path) as f:
            return f.read().strip() == "1"
    except (OSError, IOError):
        return False


def block_dev_usb_port(block_name):
    """
    Return the USB port string (e.g. '1-1' or '1-1.2') for this block device,
    or None if not USB.
    """
    device_link = os.path.join("/sys/block", block_name, "device")
    try:
        target = os.path.realpath(device_link)
    except OSError:
        return None
    # Path looks like .../usb1/1-1.2/1-1.2:1.0/... or .../usb2/2-1/...
    parts = target.split(os.sep)
    for i, part in enumerate(parts):
        if part.startswith("usb") and i + 1 < len(parts):
            port = parts[i + 1]
            # Port is typically "1-1", "1-1.2", "2-1", etc.
            if "-" in port and port[0].isdigit():
                return port
    return None


def port_matches(device_port):
    """Check if device port matches our target (e.g. 1-1 matches 1-1.2)."""
    if not device_port:
        return False
    # Exact match
    if device_port == USB_PORT:
        return True
    # Target is a parent port: e.g. USB_PORT=1-1, device_port=1-1.2
    if device_port.startswith(USB_PORT + ".") or device_port.startswith(USB_PORT + ":"):
        return True
    return False


def usb_flash_detected():
    """Return True if a USB flash drive is present on the configured port."""
    try:
        names = os.listdir("/sys/block")
    except OSError:
        return False
    for name in names:
        if not name.startswith("sd"):
            continue
        if not block_dev_is_removable(name):
            continue
        port = block_dev_usb_port(name)
        if port_matches(port):
            return True
    return False


def main():
    while True:
        try:
            if usb_flash_detected():
                print("1", flush=True)
            else:
                print("0", flush=True)
        except Exception:
            print("0", flush=True)
        time.sleep(1)


if __name__ == "__main__":
    main()
    sys.exit(0)
