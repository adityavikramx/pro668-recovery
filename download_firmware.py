#!/usr/bin/env python3
"""
PRO-668 Firmware Downloader
===========================

Downloads WS1080 firmware files from the GREFwTool GitHub repository
for use with the PRO-668 Firmware Recovery Tool.

CREDITS & ATTRIBUTION:
----------------------
Firmware files are hosted by and credited to:
  - GREFwTool by Eric A. Cottrell (WB1HBU)
  - GitHub: https://github.com/philcovington/GREFwTool

LICENSE: GPL-3.0 (to comply with GREFwTool license)

NOTE: The firmware files themselves are proprietary to Whistler/GRE
and are downloaded for repair/recovery purposes only.
"""

import urllib.request
import os
import sys

FIRMWARE_BASE_URL = "https://github.com/philcovington/GREFwTool/raw/master/firmware/"

AVAILABLE_FIRMWARE = {
    "3.8": "WS1080e_U3.8.bin_.7z",
    "4.5": "WS1080e_U4.5.bin_.7z",
    "2.0": "0602902e_U2.0.bin_.7z",  # PSR-800
}

def download_file(url, destination):
    """Download a file with progress indicator"""
    print(f"Downloading: {url}")
    print(f"Destination: {destination}")

    try:
        # Create directory if needed
        os.makedirs(os.path.dirname(destination), exist_ok=True)

        # Download with progress
        def progress_hook(block_num, block_size, total_size):
            downloaded = block_num * block_size
            if total_size > 0:
                percent = min(100, downloaded * 100 // total_size)
                print(f"\rProgress: {percent}% ({downloaded:,} / {total_size:,} bytes)", end='', flush=True)

        urllib.request.urlretrieve(url, destination, progress_hook)
        print("\nDownload complete!")
        return True

    except Exception as e:
        print(f"\nError downloading: {e}")
        return False

def main():
    print("PRO-668 Firmware Downloader")
    print("=" * 40)
    print()
    print("Available firmware versions:")
    print("  3.8 - WS1080 v3.8 (RECOMMENDED for PRO-668)")
    print("  4.5 - WS1080 v4.5")
    print("  2.0 - PSR-800 v2.0")
    print()

    if len(sys.argv) > 1:
        version = sys.argv[1]
    else:
        version = input("Enter version to download (default: 3.8): ").strip() or "3.8"

    if version not in AVAILABLE_FIRMWARE:
        print(f"Unknown version: {version}")
        print(f"Available: {', '.join(AVAILABLE_FIRMWARE.keys())}")
        sys.exit(1)

    filename = AVAILABLE_FIRMWARE[version]
    url = FIRMWARE_BASE_URL + filename

    # Determine script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    firmware_dir = os.path.join(script_dir, "firmware")
    destination = os.path.join(firmware_dir, filename)

    print()
    if download_file(url, destination):
        print()
        print(f"Downloaded to: {destination}")
        print()
        print("NOTE: The file is a .7z archive. Extract it with 7-Zip:")
        print(f'  7z e "{destination}" -o"{firmware_dir}"')
        print()
        print("Or on Windows, right-click the file and select 7-Zip > Extract Here")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
