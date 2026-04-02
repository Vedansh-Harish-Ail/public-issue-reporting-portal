@echo off
:: Ensure the script runs from the project directory
cd /d "%~dp0"

echo ==========================================
echo       MERI PANCHAYAT PORTAL
echo ==========================================
echo.

echo [1/4] Checking and installing requirements...
python -m pip install -q -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo [!] Warning: Failed to install some requirements. The app might not work correctly.
)
echo.

:: Get Local IP Address
for /f "tokens=4" %%a in ('route print ^| find " 0.0.0.0"') do set IP=%%a

echo [2/4] Finding your Network IP...
echo Your Local Network Address is: http://%IP%:5000
echo (Use the address above to open on other phones/computers)
echo.
echo NOTE: If mobile fails, ensure your Computer Wi-Fi is set to 'Private' 
echo and Python is allowed through Windows Firewall.
echo.

echo [3/4] Opening browser on THIS computer...
start "" cmd /c "ping 127.0.0.1 -n 4 > nul & start http://127.0.0.1:5000"

echo [4/4] Launching server...
echo.
python app.py
pause
