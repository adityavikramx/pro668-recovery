#!/usr/bin/env python3
"""
PRO-668 Firmware Recovery Tool
==============================

Recovers bricked Radio Shack PRO-668 scanners by transcoding and uploading
Whistler WS1080 firmware using the GRE serial protocol.

CREDITS & ATTRIBUTION:
----------------------
This tool is based on the work of Eric A. Cottrell (WB1HBU) and his GREFwTool:
  - GitHub: https://github.com/philcovington/GREFwTool
  - The XOR transcoding tables used in this tool are derived from GREFwTool
  - The GRE serial protocol implementation is based on GREFwTool source code
  - Firmware files (WS1080e_U3.8.bin) are from the GREFwTool repository

Additional information from RadioReference.com community:
  - https://forums.radioreference.com/
  - https://wiki.radioreference.com/index.php/Pro-668

TECHNICAL BACKGROUND:
--------------------
The PRO-668, WS1080, PSR-800, and Pro-18 are identical hardware with different
platform codes. This tool transcodes WS1080 (0xE6) firmware to PRO-668 (0xE4)
format using a 256-byte XOR transformation table.

LICENSE: GPL-3.0 (to comply with GREFwTool license)
"""

import serial
import sys
import time

# XOR table for transcoding WS1080 (0xE6) to PRO-668 (0xE4)
WS1080_TO_PRO668_TABLE = bytes([
    0x08, 0x40, 0x08, 0x40, 0x08, 0x40, 0x89, 0x48, 0x89, 0x48, 0x89, 0x48, 0x89, 0x48, 0x08, 0x40,
    0x08, 0x40, 0x08, 0x40, 0x08, 0x40, 0xF7, 0xDF, 0xF7, 0xDF, 0xF7, 0xDF, 0xF7, 0xDF, 0x99, 0xC8,
    0x99, 0xC8, 0x99, 0xC8, 0x99, 0xC8, 0x18, 0xC0, 0x18, 0xC0, 0x18, 0xC0, 0x18, 0xC0, 0x99, 0xC8,
    0x99, 0xC8, 0x99, 0xC8, 0x99, 0xC8, 0x0A, 0xF1, 0x0A, 0xF1, 0x0A, 0xF1, 0x0A, 0xF1, 0x99, 0xC8,
    0x99, 0xC8, 0x99, 0xC8, 0x99, 0xC8, 0x18, 0xC0, 0x18, 0xC0, 0x18, 0xC0, 0x18, 0xC0, 0x99, 0xC8,
    0x99, 0xC8, 0x99, 0xC8, 0x99, 0xC8, 0x2E, 0x93, 0x2E, 0x93, 0x2E, 0x93, 0x2E, 0x93, 0x99, 0xC8,
    0x99, 0xC8, 0x99, 0xC8, 0x99, 0xC8, 0x18, 0xC0, 0x18, 0xC0, 0x18, 0xC0, 0x18, 0xC0, 0x99, 0xC8,
    0x99, 0xC8, 0x99, 0xC8, 0x99, 0xC8, 0x0A, 0xF1, 0x0A, 0xF1, 0x0A, 0xF1, 0x0A, 0xF1, 0x99, 0xC8,
    0x99, 0xC8, 0x99, 0xC8, 0x99, 0xC8, 0x18, 0xC0, 0x18, 0xC0, 0x18, 0xC0, 0x18, 0xC0, 0x99, 0xC8,
    0x99, 0xC8, 0x99, 0xC8, 0x99, 0xC8, 0xF7, 0xDF, 0xF7, 0xDF, 0xF7, 0xDF, 0xF7, 0xDF, 0x08, 0x40,
    0x08, 0x40, 0x08, 0x40, 0x08, 0x40, 0x89, 0x48, 0x89, 0x48, 0x89, 0x48, 0x89, 0x48, 0x08, 0x40,
    0x08, 0x40, 0x08, 0x40, 0x08, 0x40, 0x9B, 0x79, 0x9B, 0x79, 0x9B, 0x79, 0x9B, 0x79, 0x08, 0x40,
    0x08, 0x40, 0x08, 0x40, 0x08, 0x40, 0x89, 0x48, 0x89, 0x48, 0x89, 0x48, 0x89, 0x48, 0x08, 0x40,
    0x08, 0x40, 0x08, 0x40, 0x08, 0x40, 0xBF, 0x1B, 0xBF, 0x1B, 0xBF, 0x1B, 0xBF, 0x1B, 0x08, 0x40,
    0x08, 0x40, 0x08, 0x40, 0x08, 0x40, 0x89, 0x48, 0x89, 0x48, 0x89, 0x48, 0x89, 0x48, 0x08, 0x40,
    0x08, 0x40, 0x08, 0x40, 0x08, 0x40, 0x9B, 0x79, 0x9B, 0x79, 0x9B, 0x79, 0x9B, 0x79, 0x08, 0x40,
])

# Protocol constants (GRE scanner protocol)
STX = 0x02  # Start of packet
ETX = 0x03  # End of packet
EOT = 0x04  # End of transmission (update complete)
ENQ = 0x05  # Enquiry (ready for next packet)
ACK = 0x06  # Acknowledgement
DLE = 0x10  # Data link escape (update start)
NAK = 0x15  # Negative acknowledgement
CAN = 0x18  # Cancel (update error)

def transcode_firmware(data, xor_table):
    """Transcode firmware data using XOR table"""
    result = bytearray(data)
    table_size = len(xor_table)
    for i in range(len(result)):
        result[i] ^= xor_table[i % table_size]
    return bytes(result)

def make_packet(data):
    """Create a GRE protocol packet: STX + data + ETX + checksum"""
    checksum = ETX
    for b in data:
        checksum = (checksum + b) & 0xFF
    return bytes([STX]) + data + bytes([ETX, checksum])

def load_and_prepare_firmware(filepath, no_transcode=False):
    """Load WS1080 firmware and prepare for PRO-668"""
    print(f"Loading firmware: {filepath}")

    with open(filepath, 'rb') as f:
        data = f.read()

    # Parse header
    platform = data[0]
    size = (data[1] << 16) | (data[2] << 8) | data[3]
    image_data = bytearray(data[4:])

    print(f"  Original platform: 0x{platform:02X}")
    print(f"  Image size: {size} bytes")

    if no_transcode:
        print("  NO TRANSCODE MODE - sending firmware as-is")
        return platform, size, bytes(image_data)

    if platform == 0xE6:
        print("  Transcoding WS1080 -> PRO-668...")
        transcoded = transcode_firmware(image_data, WS1080_TO_PRO668_TABLE)
        new_platform = 0xE4  # PRO-668
    elif platform == 0xE4:
        print("  Firmware is already PRO-668 format")
        transcoded = bytes(image_data)
        new_platform = 0xE4
    else:
        print(f"  WARNING: Unknown platform 0x{platform:02X}, using as-is")
        transcoded = bytes(image_data)
        new_platform = platform

    return new_platform, size, transcoded

def get_first_packet(platform, size):
    """Create the firmware header packet"""
    # Format: platform byte + 6 ASCII hex chars for size
    size_hex = f"{size:06X}"
    packet_data = bytes([platform]) + size_hex.encode('ascii')
    return packet_data

def get_data_packets(image_data):
    """Generator for 50-byte data packets as hex strings"""
    offset = 0
    while offset < len(image_data):
        chunk = image_data[offset:offset + 50]
        hex_data = chunk.hex().upper().encode('ascii')
        offset += 50
        yield hex_data, offset

def wait_for_ready(port, timeout=30):
    """Wait for bootloader ready signal (C characters)"""
    print("Waiting for bootloader ready signal...")
    start = time.time()
    c_count = 0

    while time.time() - start < timeout:
        if port.in_waiting:
            data = port.read(port.in_waiting)
            for b in data:
                if b == ord('C'):
                    c_count += 1
                    if c_count >= 3:
                        print(f"Bootloader ready! (received {c_count} 'C' characters)")
                        return True
        time.sleep(0.1)

    print("Timeout waiting for bootloader")
    return False

def send_version_query(port):
    """Send version query to bootloader"""
    print("Querying bootloader version...")
    # Version command is 'V' without null byte in bootloader mode
    packet = make_packet(b'V')
    port.write(packet)
    port.flush()

    time.sleep(0.5)
    response = b''
    while port.in_waiting:
        response += port.read(port.in_waiting)
        time.sleep(0.1)

    if response:
        print(f"  Version response: {response.hex()} = {response}")
        # Send ACK after receiving version response
        port.write(bytes([ACK]))
        port.flush()
        time.sleep(0.2)
    return response

def send_packet(port, packet_data):
    """Send a framed packet"""
    packet = make_packet(packet_data)
    port.write(packet)
    port.flush()
    return packet

def wait_for_response(port, timeout=10):
    """Wait for and return a response byte"""
    start = time.time()
    while time.time() - start < timeout:
        if port.in_waiting:
            return port.read(1)[0]
        time.sleep(0.01)
    return None

def upload_firmware(port, platform, size, image_data):
    """Upload firmware to scanner using GRE protocol"""

    # Wait for bootloader
    if not wait_for_ready(port):
        return False

    # Query version first (bootloader expects this)
    send_version_query(port)
    time.sleep(0.5)

    # Clear any pending data
    port.reset_input_buffer()

    # Send header packet
    print("Sending firmware header...")
    header_data = get_first_packet(platform, size)
    print(f"  Header: platform=0x{platform:02X}, size={size} (0x{size:06X})")

    packet = send_packet(port, header_data)
    print(f"  Sent header packet: {packet.hex()}")

    # Wait for DLE (update start) followed by ENQ (ready for data)
    print("Waiting for bootloader to start update...")
    update_started = False
    ready_for_data = False
    timeout = time.time() + 30

    while time.time() < timeout:
        response = wait_for_response(port, timeout=1)
        if response is None:
            continue

        print(f"  Response: 0x{response:02X} ({chr(response) if 32 <= response < 127 else '?'})")

        if response == DLE:
            print("  DLE - Update starting...")
            update_started = True
        elif response == ENQ:
            print("  ENQ - Ready for data!")
            ready_for_data = True
            break
        elif response == ACK:
            print("  ACK - Header acknowledged!")
            ready_for_data = True
            break
        elif response == NAK:
            print("  NAK - Header rejected!")
            return False
        elif response == CAN:
            print("  CAN - Update cancelled by bootloader!")
            return False
        elif response == ord('C'):
            print("  Still receiving 'C' - bootloader waiting...")
            continue

    if not ready_for_data:
        print("Timeout waiting for update to start")
        return False

    # Send data packets
    print(f"Sending firmware data ({size} bytes)...")
    total_packets = (size + 49) // 50
    packet_num = 0
    retry_count = 0
    max_retries = 3

    data_generator = get_data_packets(image_data)

    for hex_data, offset in data_generator:
        packet_num += 1
        progress = min(offset, size) * 100 // size

        while retry_count < max_retries:
            print(f"\rPacket {packet_num}/{total_packets} ({progress}%)", end='', flush=True)

            packet = send_packet(port, hex_data)

            # Wait for response
            response = wait_for_response(port, timeout=5)

            if response is None:
                print(f" - Timeout, retry {retry_count + 1}/{max_retries}")
                retry_count += 1
                continue
            elif response == ACK:
                # Packet accepted, move to next
                retry_count = 0
                break
            elif response == NAK:
                print(f" - NAK, retry {retry_count + 1}/{max_retries}")
                retry_count += 1
                continue
            elif response == ENQ:
                # Ready for next packet (treat as ACK)
                retry_count = 0
                break
            elif response == CAN:
                print(f"\n  CAN received - Update cancelled!")
                return False
            elif response == EOT:
                print(f"\n  EOT received - Update complete!")
                return True
            else:
                print(f" - Unknown response 0x{response:02X}")
                retry_count += 1
                continue

        if retry_count >= max_retries:
            print(f"\nFailed at packet {packet_num} after {max_retries} retries")
            return False

    # Wait for final EOT
    print("\n\nWaiting for completion signal...")
    response = wait_for_response(port, timeout=10)
    if response == EOT:
        print("EOT received - Firmware upload complete!")
        return True
    elif response == ACK:
        print("ACK received - Firmware upload complete!")
        return True
    elif response:
        print(f"Final response: 0x{response:02X}")
        return True

    print("Upload finished (no final response)")
    return True

def main():
    if len(sys.argv) < 3:
        print("PRO-668 Firmware Uploader")
        print("=" * 40)
        print("\nUsage: python upload_firmware.py <COM_PORT> <firmware.bin> [--no-transcode]")
        print("\nOptions:")
        print("  --no-transcode  Send firmware without platform transcoding")
        print("\nExample:")
        print("  python upload_firmware.py COM11 C:\\PRO-668\\firmware\\WS1080e_U4.5.bin")
        print("\nMake sure your scanner is showing 'Waiting for USB' before running!")
        sys.exit(1)

    com_port = sys.argv[1]
    firmware_file = sys.argv[2]
    no_transcode = "--no-transcode" in sys.argv

    print("PRO-668 Firmware Uploader")
    print("=" * 40)

    # Load and prepare firmware
    try:
        platform, size, image_data = load_and_prepare_firmware(firmware_file, no_transcode)
        print(f"  Prepared firmware: {len(image_data)} bytes for platform 0x{platform:02X}")
    except Exception as e:
        print(f"Error loading firmware: {e}")
        sys.exit(1)

    # Open serial port at 115200 (the correct baud rate for GRE scanners)
    print(f"\nOpening {com_port} at 115200 baud...")
    try:
        port = serial.Serial(
            port=com_port,
            baudrate=115200,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1,
            rtscts=False,
            dsrdtr=False,
            xonxoff=False
        )
        port.reset_input_buffer()
        port.reset_output_buffer()
        print("Port opened successfully!")
    except Exception as e:
        print(f"Failed to open port: {e}")
        sys.exit(1)

    # Upload firmware
    try:
        success = upload_firmware(port, platform, size, image_data)
    except KeyboardInterrupt:
        print("\n\nUpload cancelled by user")
        success = False
    except Exception as e:
        print(f"\nError during upload: {e}")
        import traceback
        traceback.print_exc()
        success = False
    finally:
        port.close()

    if success:
        print("\n" + "=" * 40)
        print("*** FIRMWARE UPLOAD SUCCESSFUL! ***")
        print("=" * 40)
        print("\nPlease power cycle your scanner now.")
        print("The scanner should boot with the new firmware.")
    else:
        print("\n" + "=" * 40)
        print("*** FIRMWARE UPLOAD FAILED ***")
        print("=" * 40)
        print("\nTry:")
        print("1. Power cycle the scanner")
        print("2. Make sure it shows 'Waiting for USB'")
        print("3. Run this script again")
        sys.exit(1)

if __name__ == '__main__':
    main()
