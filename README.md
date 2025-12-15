# PRO-668 Firmware Recovery Tool

A Python tool to recover bricked Radio Shack PRO-668 scanners by uploading transcoded Whistler WS1080 firmware.

## Background

### Compatible Hardware

The following scanners are **identical hardware** with different branding by GRE (General Research of Electronics):

| Scanner | Manufacturer | Platform Code | USB VID:PID |
|---------|--------------|---------------|-------------|
| **PRO-668** | RadioShack | 0xE4 | 08B9:000F |
| **WS1080** | Whistler | 0xE6 | 08B9:000F |
| **WS1088** | Whistler | 0xE6 | 08B9:000F |
| **PSR-800** | GRE | 0xEE | 08B9:000F |
| **Pro-18** | RadioShack | 0xEC | 08B9:000F |

### How to Identify Your Scanner

1. **Model number** - Check the label on back of scanner
2. **USB detection** - All models show as "USB Serial Device" with VID 08B9
3. **Bootloader version** - PRO-668 shows "RF1.1", Whistler shows "Boot 2.0"

### Key Differences

| Feature | RadioShack (PRO-668) | Whistler (WS1080) |
|---------|---------------------|-------------------|
| Bootloader | RF1.1 | Boot 2.0 |
| Update servers | OFFLINE (defunct) | Active |
| Official support | None | $59.99 Legacy Upgrade |
| Firmware source | This tool | Whistler website |

When firmware for one platform is uploaded to a different platform without proper transcoding, the bootloader rejects it and erases the existing firmware, leaving the scanner in a "bricked" state showing:

```
uP BootVer: RF1.1
uP App Ver: NONE
CPU SW Upgrade: Waiting for USB
```

## The Problem This Solves

If you attempted to update your PRO-668 using the Whistler Update Utility (designed for WS1080), your scanner may have been bricked. The original Radio Shack update servers are permanently offline, making official recovery impossible.

This tool:
1. Downloads WS1080 firmware from archived sources
2. Transcodes it to PRO-668 format using XOR transformation
3. Uploads it to the scanner using the GRE serial protocol

## Requirements

- Python 3.x
- pyserial library (`pip install pyserial`)
- USB cable connected to scanner
- Scanner in bootloader mode ("Waiting for USB")

## Installation

```bash
# Clone or download this repository
git clone https://github.com/yourusername/pro668-recovery.git
cd pro668-recovery

# Install dependencies
pip install pyserial
```

## Usage

### Quick Start (Windows)

1. Connect your PRO-668 via USB
2. Ensure scanner shows "Waiting for USB"
3. Note which COM port it's on (check Device Manager)
4. Run:

```bash
python upload_firmware.py COM11 firmware/WS1080e_U3.8.bin
```

### Command Line Options

```
Usage: python upload_firmware.py <COM_PORT> <firmware.bin> [--no-transcode]

Options:
  --no-transcode  Send firmware without platform transcoding (for testing)

Example:
  python upload_firmware.py COM11 firmware/WS1080e_U3.8.bin
```

## Firmware Files

### Recommended: WS1080 v3.8
- **File:** `WS1080e_U3.8.bin`
- **Size:** 366,768 bytes
- **Platform:** 0xE6 (WS1080) - automatically transcoded to 0xE4 (PRO-668)
- **Source:** [GREFwTool GitHub Repository](https://github.com/philcovington/GREFwTool/tree/master/firmware)

This version was known as the "winning combination" for PRO-668 DMR upgrades and is safe to use.

### Versions to Avoid
- **v4.6 and later:** Contains "lock" code that may brick non-Whistler scanners
- These versions check the bootloader version and may refuse to run

### Downloading Firmware

```bash
# Download WS1080 v3.8 (recommended)
curl -L -o firmware/WS1080e_U3.8.bin_.7z \
  "https://github.com/philcovington/GREFwTool/raw/master/firmware/WS1080e_U3.8.bin_.7z"

# Extract with 7-Zip
7z e firmware/WS1080e_U3.8.bin_.7z -ofirmware/
```

## How It Works

### 1. Bootloader Detection
The scanner's bootloader sends 'C' characters (XMODEM-CRC ready signal) when waiting for firmware.

### 2. Version Query
The tool queries the bootloader version to confirm communication:
- Response `11FF` = Boot 1.1, no firmware (RF1.1 bootloader)

### 3. Firmware Transcoding
WS1080 firmware (platform 0xE6) is XOR'd with a 256-byte transformation table to convert it to PRO-668 format (platform 0xE4).

### 4. Header Packet
Sends: `STX + platform_byte + size_hex(6 chars) + ETX + checksum`

Example: `02 E4 30 35 39 38 41 43 03 41` for 366,764 bytes

### 5. Data Packets
- 50 bytes of binary data per packet
- Encoded as 100 ASCII hex characters
- Framed with STX/ETX/checksum
- ~7,336 packets for v3.8 firmware

### 6. Protocol Signals
| Signal | Hex | Meaning |
|--------|-----|---------|
| STX | 0x02 | Start of packet |
| ETX | 0x03 | End of packet |
| EOT | 0x04 | End of transmission |
| ENQ | 0x05 | Ready for next packet |
| ACK | 0x06 | Acknowledged |
| DLE | 0x10 | Update starting |
| NAK | 0x15 | Retry requested |
| CAN | 0x18 | Cancel/error |

## Troubleshooting

### "Timeout waiting for bootloader"
- Ensure scanner shows "Waiting for USB" on display
- Try unplugging and reconnecting USB cable
- Check correct COM port in Device Manager

### "CAN received - Update cancelled"
- Bootloader rejected the firmware
- Try power cycling the scanner and running again
- Ensure using compatible firmware version (v3.8 recommended)

### COM Port Not Found
- On Windows, use format `COM11` (not `/dev/ttyS11`)
- Check Device Manager for actual port number

### pyserial Not Found
```bash
pip install pyserial
```

## Technical Details

### XOR Transcoding Table

The 256-byte XOR table transforms WS1080 (0xE6) firmware to PRO-668 (0xE4) format. Each byte of the firmware image is XOR'd with the corresponding byte in the table (cycling through the 256 bytes).

```python
WS1080_TO_PRO668_TABLE = bytes([
    0x08, 0x40, 0x08, 0x40, 0x08, 0x40, 0x89, 0x48, ...
    # (256 bytes total - see upload_firmware.py for full table)
])
```

### Packet Checksum Calculation

```python
def make_packet(data):
    checksum = 0x03  # Initialize with ETX value
    for b in data:
        checksum = (checksum + b) & 0xFF
    return bytes([0x02]) + data + bytes([0x03, checksum])
```

### Firmware File Format

```
Byte 0:     Platform code (0xE6 for WS1080)
Bytes 1-3:  Image size (big-endian, 24-bit)
Bytes 4+:   Firmware image data
```

## Credits & Attribution

This tool would not be possible without the work of others:

### GREFwTool by Eric A. Cottrell
- **GitHub:** [philcovington/GREFwTool](https://github.com/philcovington/GREFwTool)
- **Original Author:** Eric A. Cottrell (WB1HBU)
- **What we used:**
  - XOR transcoding tables for platform conversion (WS1080 ↔ PRO-668)
  - GRE serial protocol documentation and implementation
  - Firmware binary files (WS1080e_U3.8.bin)
- **License:** The original GREFwTool is open source

### RadioReference Community
- **Website:** [RadioReference.com](https://www.radioreference.com/)
- **Forums:** [RadioReference Forums](https://forums.radioreference.com/)
- **What we used:**
  - Community knowledge about GRE/Whistler/RadioShack scanner compatibility
  - Troubleshooting information and recovery procedures
  - Historical documentation about firmware versions and "lock" code issues

### Technical References
- **PRO-668 Wiki:** [RadioReference Wiki - Pro-668](https://wiki.radioreference.com/index.php/Pro-668)
- **WS1080 Wiki:** [RadioReference Wiki - WS1080](https://wiki.radioreference.com/index.php/WS1080)
- **Key Forum Thread:** [PRO-668 loaded with Whistler DMR firmware](https://forums.radioreference.com/threads/radio-shack-pro-668-loaded-with-whistler-dmr-firmware.339155/)

### Original Hardware Manufacturers
- **GRE (General Research of Electronics)** - Original hardware design
- **Whistler Group** - WS1080 branding and continued support
- **RadioShack** - PRO-668 branding

## Disclaimer

This tool is provided for educational and recovery purposes. Use at your own risk. The authors are not responsible for any damage to your scanner. Always ensure you have the correct firmware version for your device.

## License

**GPL-3.0 License** - See LICENSE file for details.

This project is licensed under GPL-3.0 to comply with the license of GREFwTool,
from which the transcoding tables and protocol implementation are derived.

**Note on Firmware Files:** The .bin firmware files are proprietary to Whistler/GRE
and are included for repair/recovery purposes under fair use principles.

## Related Links

- [GREFwTool GitHub](https://github.com/philcovington/GREFwTool)
- [RadioReference PRO-668 Wiki](https://wiki.radioreference.com/index.php/Pro-668)
- [RadioReference Forums - PRO-668 Discussion](https://forums.radioreference.com/threads/radio-shack-pro-668-loaded-with-whistler-dmr-firmware.339155/)
#   p r o 6 6 8 - r e c o v e r y  
 #   p r o 6 6 8 - r e c o v e r y  
 