@echo off
title SecurePixel Launcher
color 0A

echo ========================================
echo   SecurePixel
echo    Windows Launcher
echo ========================================
echo.

:: Check if Docker is installed
echo [1/6] Checking Docker installation...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed!
    echo.
    echo Please install Docker Desktop from:
    echo https://www.docker.com/products/docker-desktop/
    echo.
    echo After installation, restart your computer and run this again.
    pause
    exit /b 1
)
echo ✅ Docker is installed

:: Check if Docker is running
echo [2/6] Checking if Docker is running...
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running!
    echo.
    echo Please start Docker Desktop:
    echo 1. Open Start Menu
    echo 2. Search for "Docker Desktop"
    echo 3. Click to start it
    echo 4. Wait for it to show "Running" in system tray
    echo.
    pause
    exit /b 1
)
echo ✅ Docker is running

:: Create shared folder
echo [3/6] Creating shared folder...
if not exist shared mkdir shared
echo ✅ Shared folder created

:: Get IP address
echo [4/6] Detecting IP address...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do set IP=%%a
set IP=%IP: =%
if "%IP%"=="" (
    echo ⚠ Could not detect IP automatically
    set /p IP="Please enter your IP address manually: "
) else (
    echo ✅ IP detected: %IP%
)

:: Check VcXsrv
echo [5/6] Checking VcXsrv...
tasklist /FI "IMAGENAME eq vcxsrv.exe" 2>NUL | find /I /N "vcxsrv.exe">NUL
if errorlevel 1 (
    echo ⚠ VcXsrv is not running!
    echo.
    echo Please start VcXsrv (XLaunch):
    echo 1. Open Start Menu
    echo 2. Type "XLaunch" and open it
    echo 3. Select:
    echo    - Multiple windows
    echo    - Display number: 0
    echo    - Start no client
    echo    - ✓ Disable access control
    echo 4. Click Finish
    echo.
    pause
) else (
    echo ✅ VcXsrv is running
)

:: Set DISPLAY
set DISPLAY=%IP%:0
echo [6/6] Setting DISPLAY=%DISPLAY%

echo.
echo ========================================
echo    Starting Docker Containers
echo ========================================
echo.
echo This will take a few minutes the first time.
echo Press Ctrl+C to stop the application.
echo.

:: Start the application
docker-compose up

:: When stopped, ask if user wants to clean up
echo.
echo ========================================
echo Application stopped.
echo ========================================
echo.
set /p cleanup="Do you want to stop and remove containers? (y/n): "
if /i "%cleanup%"=="y" (
    echo Stopping containers...
    docker-compose down
    echo ✅ Containers stopped
)

echo.
echo Press any key to exit...
pause >nul
