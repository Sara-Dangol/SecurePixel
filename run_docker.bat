@echo off
title SecurePixel Docker Launcher
color 0A

echo =========================================
echo    🔐 SecurePixel - Docker Launcher
echo =========================================
echo.

:: Check if Docker is installed
echo [1/5] Checking Docker installation...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed!
    echo.
    echo Please install Docker Desktop from:
    echo https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)
echo ✅ Docker is installed

:: Check if Docker is running
echo [2/5] Checking if Docker is running...
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running!
    echo.
    echo Please start Docker Desktop:
    echo 1. Open Start Menu
    echo 2. Search for "Docker Desktop"
    echo 3. Click to start it
    echo 4. Wait for it to show "Running"
    pause
    exit /b 1
)
echo ✅ Docker is running

:: Create shared folder
echo [3/5] Creating shared folder...
if not exist shared mkdir shared
echo ✅ Shared folder created

:: Check VcXsrv for GUI
echo [4/5] Checking VcXsrv...
tasklist /FI "IMAGENAME eq vcxsrv.exe" 2>NUL | find /I /N "vcxsrv.exe">NUL
if errorlevel 1 (
    echo ⚠️ VcXsrv is not running!
    echo.
    echo For GUI to work, please start VcXsrv (XLaunch):
    echo 1. Install from: https://sourceforge.net/projects/vcxsrv/
    echo 2. Run XLaunch with these settings:
    echo    - Multiple windows
    echo    - Display number: 0
    echo    - Start no client
    echo    - ✓ Disable access control
    echo.
    pause
) else (
    echo ✅ VcXsrv is running
)

:: Menu
echo [5/5] Ready
echo.
echo =========================================
echo Select option:
echo  1) 🚀 Run SecurePixel application
echo  2) 🧪 Run tests
echo  3) 🐚 Open shell in container
echo  4) 📊 View logs
echo  5) 🛑 Stop all containers
echo  6) 🗑️  Clean up (remove containers and volumes)
echo  7) 🚪 Exit
echo =========================================
echo.

set /p choice="Enter choice (1-7): "

if "%choice%"=="1" goto run_app
if "%choice%"=="2" goto run_tests
if "%choice%"=="3" goto open_shell
if "%choice%"=="4" goto view_logs
if "%choice%"=="5" goto stop
if "%choice%"=="6" goto cleanup
if "%choice%"=="7" goto exit

echo Invalid choice!
pause
exit /b 1

:run_app
echo.
echo 🚀 Starting SecurePixel...
docker-compose up app
goto end

:run_tests
echo.
echo 🧪 Running tests...
docker-compose --profile tests up test-runner
echo.
echo Test reports saved in .\test-reports\
goto end

:open_shell
echo.
echo 🐚 Opening shell in app container...
docker-compose run --rm app cmd
goto end

:view_logs
echo.
echo 📊 Showing logs...
docker-compose logs -f
goto end

:stop
echo.
echo 🛑 Stopping containers...
docker-compose down
echo ✅ Containers stopped
goto end

:cleanup
echo.
echo ⚠️ This will remove all containers and volumes!
set /p confirm="Are you sure? (y/n): "
if /i "%confirm%"=="y" (
    docker-compose down -v
    echo ✅ Cleanup complete
)
goto end

:exit
echo Goodbye!
exit /b 0

:end
pause
