# Starts the React UI at http://127.0.0.1:5173 (backend must be running on :8000)
Set-Location "$PSScriptRoot\frontend"
if (-not (Test-Path node_modules)) { npm install }
npm run dev
