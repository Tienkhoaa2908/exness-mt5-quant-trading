@echo off
setlocal EnableExtensions
cd /d "%~dp0\.."

set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY (
  where python >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo FATAL: Python 3 not found.
  exit /b 2
)

echo === MT5 RESEARCH ONE-RUN ONE-ZIP PACKAGER ===
%PY% scripts\package_mt5_research.py --repo-root "%CD%"
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
  echo Packaging failed rc=%RC%.
  exit /b %RC%
)

echo Packaging PASS. Upload only the ZIP printed above.
exit /b 0
