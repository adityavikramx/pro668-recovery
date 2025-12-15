@echo off
echo ========================================
echo PRO-668 Firmware Recovery Tool
echo ========================================
echo.

REM Check if firmware file exists
if not exist "%~dp0firmware\WS1080e_U3.8.bin" (
    echo ERROR: Firmware file not found!
    echo.
    echo Please download WS1080e_U3.8.bin from:
    echo https://github.com/philcovington/GREFwTool/tree/master/firmware
    echo.
    echo And place it in the firmware folder.
    pause
    exit /b 1
)

echo Firmware file found: WS1080e_U3.8.bin
echo.
echo INSTRUCTIONS:
echo 1. Connect your PRO-668 via USB
echo 2. Scanner should show "Waiting for USB"
echo 3. Check Device Manager for COM port number
echo.
set /p COMPORT="Enter COM port (e.g., COM11): "

echo.
echo Starting firmware upload to %COMPORT%...
echo This will take several minutes. Do not disconnect!
echo.

python "%~dp0upload_firmware.py" %COMPORT% "%~dp0firmware\WS1080e_U3.8.bin"

echo.
if %ERRORLEVEL% EQU 0 (
    echo ========================================
    echo SUCCESS! Your scanner should be working now.
    echo ========================================
) else (
    echo ========================================
    echo Upload failed. Please try again.
    echo ========================================
)

echo.
pause
