# PRO-668 Recovery Guide

## Step-by-Step Instructions to Recover a Bricked PRO-668

### Symptoms of a Bricked Scanner

Your scanner is "bricked" if it shows:
```
uP BootVer: RF1.1
uP App Ver: NONE
CPU SW Upgrade: Waiting for USB
```

This typically happens when:
- You used the Whistler Update Utility on a Radio Shack PRO-668
- A firmware update was interrupted
- Wrong firmware version was applied

### What You Need

1. **Windows PC** with Python 3.x installed
2. **USB Cable** to connect scanner to PC
3. **This recovery tool** (upload_firmware.py)
4. **WS1080 v3.8 firmware** (included or downloadable)

### Step 1: Install Python (if needed)

1. Download Python from https://www.python.org/downloads/
2. During installation, CHECK "Add Python to PATH"
3. Open Command Prompt and verify:
   ```
   python --version
   ```

### Step 2: Install Required Library

Open Command Prompt and run:
```
pip install pyserial
```

### Step 3: Download Firmware (if not included)

If the `firmware/WS1080e_U3.8.bin` file is not present:

1. Go to: https://github.com/philcovington/GREFwTool/tree/master/firmware
2. Download `WS1080e_U3.8.bin_.7z`
3. Extract with 7-Zip to the `firmware` folder
4. You should have `firmware/WS1080e_U3.8.bin`

### Step 4: Connect Scanner

1. Connect PRO-668 to PC via USB cable
2. Scanner should show "Waiting for USB"
3. Open Device Manager (Win+X, then Device Manager)
4. Look under "Ports (COM & LPT)" for "USB Serial Device (COMxx)"
5. Note the COM port number (e.g., COM11)

### Step 5: Run Recovery

**Option A: Using Batch File (Easy)**
1. Double-click `UPLOAD_FIRMWARE.bat`
2. Enter your COM port when prompted
3. Wait for upload to complete

**Option B: Using Command Line**
1. Open Command Prompt
2. Navigate to the recovery tool folder:
   ```
   cd C:\PRO-668
   ```
3. Run the upload:
   ```
   python upload_firmware.py COM11 firmware\WS1080e_U3.8.bin
   ```
   (Replace COM11 with your actual COM port)

### Step 6: Wait for Upload

The upload process:
1. Detects bootloader (shows "Bootloader ready!")
2. Queries version (shows "11FF" for empty scanner)
3. Sends header packet
4. Uploads ~7,336 data packets (takes several minutes)
5. Scanner automatically reboots when complete

**DO NOT disconnect the USB cable during upload!**

### Step 7: Verify Success

After upload completes:
1. Scanner will disconnect from USB
2. Scanner should reboot automatically
3. Display should show time/date or normal operation
4. Scanner is recovered!

### Troubleshooting

#### "Timeout waiting for bootloader"
- Scanner not showing "Waiting for USB"
- Try unplugging/reconnecting USB
- Power cycle scanner (remove batteries, wait 10 sec, reinstall)

#### "CAN received - Update cancelled"
- Bootloader rejected firmware
- Power cycle scanner and try again
- Make sure you're using v3.8 firmware

#### "Could not open port"
- Wrong COM port number
- Another program using the port
- Try different USB port

#### "No module named 'serial'"
```
pip install pyserial
```

#### Scanner still shows "NONE" after upload
- Upload may have been interrupted
- Power cycle and run upload again
- Watch for "Firmware upload complete!" message

### What Firmware Version Do I Have Now?

After successful recovery with WS1080 v3.8:
- Your scanner runs firmware version 3.8
- This includes DMR digital voice capability
- The firmware was transcoded from WS1080 to PRO-668 format

### Preventing Future Problems

1. **Never use Whistler Update Utility** on PRO-668
2. Use Radio Shack iScan software (if available) or this recovery tool
3. Keep a backup of working firmware
4. Avoid firmware versions 4.6 and later (contain lock code)

### Technical Background

The PRO-668 and WS1080 are identical hardware. The only difference is a "platform code" in the firmware:
- PRO-668 = 0xE4
- WS1080 = 0xE6

This tool automatically transcodes WS1080 firmware to PRO-668 format using a 256-byte XOR transformation table. The bootloader then accepts the firmware as native PRO-668.

### Getting Help

If you encounter issues:
1. Check the troubleshooting section above
2. Visit RadioReference Forums: https://forums.radioreference.com/
3. Search for "PRO-668 firmware" discussions

### Credits

- GREFwTool by Eric A. Cottrell - Original research and transcoding tables
- RadioReference Community - Invaluable knowledge and support
