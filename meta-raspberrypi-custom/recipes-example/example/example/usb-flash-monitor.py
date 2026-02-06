#!/usr/bin/env python3
"""
USB flash drive monitor: print 1 every second when a USB flash drive is
detected on Bus 002 Port 001 only, otherwise print 0.
When detected, mounts the drive and validates signature.
"""

import os
import sys
import time
import subprocess
import tempfile
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature

# Bus 002 Port 001 = sysfs port "2-1". Override with env USB_FLASH_PORT if needed.
USB_PORT = os.environ.get("USB_FLASH_PORT", "2-1")

# Public key for validation (replace with actual public key)
PUBLIC_KEY_PEM = b"""-----BEGIN PUBLIC KEY-----
REPLACE_THIS_WITH_YOUR_PUBLIC_KEY_CONTENT
-----END PUBLIC KEY-----"""


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


def get_device_name():
    """Get the device name (e.g., 'sda1') of the USB flash drive on the configured port."""
    try:
        names = os.listdir("/sys/block")
    except OSError:
        return None
    
    for name in names:
        if not name.startswith("sd"):
            continue
        if not block_dev_is_removable(name):
            continue
        port = block_dev_usb_port(name)
        if port_matches(port):
            # Check for partition (e.g., sda1)
            partition_path = f"/sys/block/{name}"
            try:
                partitions = os.listdir(partition_path)
                for partition in partitions:
                    if partition.startswith(name) and partition != name:
                        return partition
            except OSError:
                pass
            # If no partition found, return the device name itself
            return name
    return None


def clean_serial(serial):
    """
    Normalize USB serial number string.
    Must match provisioner's cleaning logic exactly.
    """
    if not serial:
        return ""
    
    serial = serial.strip()
    serial = ''.join(serial.split())
    serial = serial.upper()
    
    return serial


def get_usb_serial_linux(device_name):
    """
    Get USB serial number on Linux using sysfs.
    
    Args:
        device_name: Block device name (e.g., 'sda1')
    
    Returns:
        str: USB serial number or None
    """
    try:
        # Remove partition number to get base device
        base_device = device_name.rstrip('0123456789')
        
        # Try to read serial from sysfs
        serial_path = f"/sys/block/{base_device}/device/serial"
        if os.path.exists(serial_path):
            with open(serial_path, 'r') as f:
                serial = f.read().strip()
                if serial:
                    return clean_serial(serial)
        
        # Alternative: read from udev
        try:
            result = subprocess.run(
                ['udevadm', 'info', '--query=property', f'--name=/dev/{base_device}'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.startswith('ID_SERIAL_SHORT='):
                        serial = line.split('=', 1)[1].strip()
                        if serial:
                            return clean_serial(serial)
        except:
            pass
        
        return None
        
    except Exception:
        return None


def load_public_key(pem_data=None):
    """
    Load public key from PEM data or file.
    
    Args:
        pem_data: PEM bytes (uses embedded key if None)
    
    Returns:
        RSA public key object
    """
    if pem_data is None:
        pem_data = PUBLIC_KEY_PEM
    
    # If key not embedded, try loading from file
    if b"REPLACE_THIS" in pem_data:
        key_file = "/etc/usb-validator/public_key.pem"
        if os.path.exists(key_file):
            try:
                with open(key_file, 'rb') as f:
                    pem_data = f.read()
            except:
                return None
        else:
            return None
    
    try:
        public_key = serialization.load_pem_public_key(
            pem_data,
            backend=default_backend()
        )
        return public_key
    except Exception:
        return None


def verify_signature(serial, signature, public_key, salt_string="manufacture"):
    """
    Verify signature against serial number.
    Combines serial with a salt string, hashes with SHA-256, then verifies.
    
    Args:
        serial: USB serial number string
        signature: Signature bytes
        public_key: RSA public key
        salt_string: Fixed string to combine with serial (default: "manufacture")
    
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        # Combine serial with salt string
        data_to_hash = f"{serial}{salt_string}"
        
        # Hash the combined data with SHA-256
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(data_to_hash.encode('utf-8'))
        hashed_data = digest.finalize()
        
        # Verify the signature against the hash
        public_key.verify(
            signature,
            hashed_data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except InvalidSignature:
        return False
    except Exception:
        return False


def validate_mounted_usb(mount_point, device_name):
    """
    Validate the USB drive by checking signature.
    
    Args:
        mount_point: Path where USB is mounted
        device_name: Device name (e.g., 'sda1')
    
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        # Load public key
        public_key = load_public_key()
        if not public_key:
            return False
        
        # Check for signature file
        sig_file = os.path.join(mount_point, "device.sig")
        if not os.path.exists(sig_file):
            return False
        
        # Read signature
        try:
            with open(sig_file, 'rb') as f:
                signature = f.read()
        except Exception:
            return False
        
        # Get USB serial number
        serial = get_usb_serial_linux(device_name)
        if not serial:
            return False
        
        # Verify signature
        return verify_signature(serial, signature, public_key)
        
    except Exception:
        return False


def mount_and_validate(device_name):
    """
    Mount the USB drive to a temporary folder and validate it.
    
    Args:
        device_name: Device name (e.g., 'sda1')
    
    Returns:
        str: "1" if valid, "3" if invalid
    """
    mount_point = None
    try:
        # Create temporary mount point
        mount_point = tempfile.mkdtemp(prefix="usb_validate_")
        
        # Mount the device
        device_path = f"/dev/{device_name}"
        result = subprocess.run(
            ['mount', '-o', 'ro', device_path, mount_point],
            capture_output=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return "3"
        
        # Validate the USB
        is_valid = validate_mounted_usb(mount_point, device_name)
        
        # Unmount
        subprocess.run(['umount', mount_point], timeout=10)
        
        # Clean up temp directory
        try:
            os.rmdir(mount_point)
        except:
            pass
        
        return "1" if is_valid else "3"
        
    except Exception:
        # Clean up on error
        if mount_point:
            try:
                subprocess.run(['umount', mount_point], timeout=5, capture_output=True)
                os.rmdir(mount_point)
            except:
                pass
        return "3"


def main():
    last_detected = False
    validation_result = None
    
    while True:
        try:
            device_name = get_device_name()
            currently_detected = device_name is not None
            
            if currently_detected:
                # USB is detected on the correct port
                if not last_detected:
                    # Newly detected - mount and validate
                    validation_result = mount_and_validate(device_name)
                
                # Print validation result
                print(validation_result, flush=True)
            else:
                # No USB detected
                print("0", flush=True)
                validation_result = None
            
            last_detected = currently_detected
            
        except Exception:
            print("0", flush=True)
            validation_result = None
            last_detected = False
        
        time.sleep(1)


if __name__ == "__main__":
    main()
    sys.exit(0)
