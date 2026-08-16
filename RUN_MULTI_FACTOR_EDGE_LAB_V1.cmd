@echo off
setlocal
cd /d "%~dp0"
if not exist "%~dp0scripts\run_multi_factor_edge_lab_v1.ps1" (
  if not exist "%~dp0recovery\v21_impl_payload.zip" (
    echo V21 implementation payload missing.
    exit /b 2
  )
  powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -LiteralPath '%~dp0recovery\v21_impl_payload.zip' -DestinationPath '%~dp0' -Force"
  if errorlevel 1 exit /b %ERRORLEVEL%
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\run_multi_factor_edge_lab_v1.ps1"
set ERR=%ERRORLEVEL%
echo.
if not "%ERR%"=="0" (
  echo MULTI FACTOR EDGE LAB V1 FAILED. Exit code %ERR%.
) else (
  echo MULTI FACTOR EDGE LAB V1 COMPLETE. Upload the single ZIP created on Desktop.
)
pause
exit /b %ERR%
