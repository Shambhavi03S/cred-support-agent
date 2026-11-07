@echo off
REM Double-click to start everything. Add "-Demos" to also run the tests/demos first.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_all.ps1" %*
