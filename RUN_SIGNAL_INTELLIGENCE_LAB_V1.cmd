@echo off
setlocal
cd /d "%~dp0"
if not exist "%~dp0scripts\run_signal_intelligence_lab_v1.ps1" (
  if not exist "%~dp0recovery\v22_impl_payload.b64.part01" (
    echo V22 recovery payload missing.
    exit /b 2
  )
  powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
    "$parts = Get-ChildItem -LiteralPath '%~dp0recovery' -Filter 'v22_impl_payload.b64.part*' ^| Sort-Object Name; " ^
    "$b64 = -join ($parts ^| ForEach-Object { Get-Content -LiteralPath $_.FullName -Raw }); " ^
    "$zip = Join-Path $env:TEMP 'v22_impl_payload.zip'; " ^
    "[IO.File]::WriteAllBytes($zip,[Convert]::FromBase64String($b64)); " ^
    "Expand-Archive -LiteralPath $zip -DestinationPath '%~dp0' -Force"
  if errorlevel 1 exit /b %ERRORLEVEL%
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\run_signal_intelligence_lab_v1.ps1"
set ERR=%ERRORLEVEL%
echo.
if not "%ERR%"=="0" (
  echo SIGNAL INTELLIGENCE LAB V1 FAILED. Exit code %ERR%.
) else (
  echo SIGNAL INTELLIGENCE LAB V1 COMPLETE. Upload the single ZIP created on Desktop.
)
pause
exit /b %ERR%
