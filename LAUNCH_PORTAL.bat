@echo off
:: Ensure the script runs from the project directory
cd /d "%~dp0"

echo ==========================================
echo       MERI PANCHAYAT PORTAL
echo ==========================================
echo.

:: Get Local IP Address
for /f "tokens=4" %%a in ('route print ^| find " 0.0.0.0"') do set IP=%%a

echo [1/3] Finding your Network IP...
echo Your Local Network Address is: http://%IP%:5000
echo (Use the address above to open on other phones/computers)
echo.
echo NOTE: If mobile fails, ensure your Computer Wi-Fi is set to 'Private' 
echo and Python is allowed through Windows Firewall.
echo.

echo [2/3] Opening browser on THIS computer...
start "" "http://127.0.0.1:5000"

echo [3/3] Launching server...
echo.
python app.py
pause
