@echo off
echo ============================================
echo  OpenCaptions - Enable Adobe CEP Debug Mode
echo ============================================
echo.
echo This enables unsigned extensions in Premiere Pro.
echo Adding registry keys for CSXS versions 9-12...
echo.

reg add "HKCU\SOFTWARE\Adobe\CSXS.9" /v PlayerDebugMode /t REG_SZ /d 1 /f >nul 2>&1
reg add "HKCU\SOFTWARE\Adobe\CSXS.10" /v PlayerDebugMode /t REG_SZ /d 1 /f >nul 2>&1
reg add "HKCU\SOFTWARE\Adobe\CSXS.11" /v PlayerDebugMode /t REG_SZ /d 1 /f >nul 2>&1
reg add "HKCU\SOFTWARE\Adobe\CSXS.12" /v PlayerDebugMode /t REG_SZ /d 1 /f >nul 2>&1

echo Done! Debug mode enabled for CSXS 9-12.
echo Restart Premiere Pro for changes to take effect.
echo.
pause
