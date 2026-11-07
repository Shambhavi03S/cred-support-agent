# Regenerates every evaluation artifact + transcript from scratch (MOCK_LLM, no keys).
$ErrorActionPreference = "Continue"
$env:LLM_MODE = "MOCK_LLM"; $env:PYTHONIOENCODING = "utf-8"
$py = "$PSScriptRoot\.venv\Scripts\python.exe"
Set-Location $PSScriptRoot
$jobs = @(
  @("dataset.py", "dataset_report"), @("scripts\calibrate_threshold.py", "threshold_calibration"),
  @("scripts\demo_grounded.py", "grounded_demo"), @("scripts\eval_chunking.py", "chunking_eval"),
  @("scripts\demo_agent.py", "agent_demo"), @("scripts\eval_triad.py", "triad_eval"),
  @("scripts\demo_mcp.py", "mcp_demo"), @("scripts\demo_checkpoint.py", "checkpoint_demo"),
  @("scripts\demo_resilience.py", "resilience_demo"))
foreach ($j in $jobs) {
  Write-Host "== $($j[0])"
  & $py $j[0] 2>&1 | Where-Object { $_ -notmatch "Loading weights|HF_TOKEN" } | Out-File -Encoding utf8 "transcripts\$($j[1]).txt"
}
& $py -m pytest tests -v 2>&1 | Out-File -Encoding utf8 docs\pytest_output.txt
Get-Content docs\pytest_output.txt -Tail 3
