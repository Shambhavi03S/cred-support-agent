# Starts backend, frontend and MCP server, each in its own window.
# Usage:  .\start_all.ps1            (just start services)
#         .\start_all.ps1 -Demos     (run all demos/tests first, then start services)
param([switch]$Demos)
$root = $PSScriptRoot
Set-Location $root

if ($Demos) { & "$root\run_all_demos.ps1" }

foreach ($s in "start_backend.ps1", "start_mcp_server.ps1", "start_frontend.ps1") {
  Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "`"$root\$s`"" -WorkingDirectory $root
}

Write-Host "Starting services in 3 windows..."
Write-Host "  API / Swagger : http://127.0.0.1:8000/docs"
Write-Host "  UI            : http://127.0.0.1:5173"
Write-Host "  MCP           : http://127.0.0.1:8001/mcp"
# The API loads the embedding model on startup (can take 30-60 s) - wait until it answers.
Write-Host "Waiting for the API to be ready..."
$ready = $false
for ($i = 0; $i -lt 90 -and -not $ready; $i++) {
  try { Invoke-RestMethod http://127.0.0.1:8000/health -TimeoutSec 2 | Out-Null; $ready = $true } catch { Start-Sleep -Seconds 2 }
}
if ($ready) { Write-Host "API ready."; Start-Process "http://127.0.0.1:5173" }
else { Write-Host "API did not start - check the backend window for errors." }
