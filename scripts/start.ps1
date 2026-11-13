param([switch]$Seed)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
$nodeCommand = Get-Command node -ErrorAction SilentlyContinue
if ($nodeCommand) { $nodePath = $nodeCommand.Source } else {
  $nodePath = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
}
if (!(Test-Path -LiteralPath $pythonPath) -or !(Test-Path -LiteralPath $nodePath)) {
  throw 'Install Python and Node.js, then follow README.md setup steps first.'
}
$backendPath = Join-Path $projectRoot 'backend'
$frontendPath = Join-Path $projectRoot 'frontend'
if ($Seed) {
  Push-Location $backendPath
  try { & $pythonPath -m app.seed; if ($LASTEXITCODE -ne 0) { throw 'Demo setup failed' } } finally { Pop-Location }
}
$logsPath = Join-Path $projectRoot 'logs'
New-Item -ItemType Directory -Force $logsPath | Out-Null
$api = Start-Process -FilePath $pythonPath -ArgumentList '-m uvicorn app.main:app --host 127.0.0.1 --port 8000' -WorkingDirectory $backendPath -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logsPath 'backend.log') -RedirectStandardError (Join-Path $logsPath 'backend-error.log')
$web = Start-Process -FilePath $nodePath -ArgumentList 'node_modules/next/dist/bin/next dev --hostname 127.0.0.1' -WorkingDirectory $frontendPath -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logsPath 'frontend.log') -RedirectStandardError (Join-Path $logsPath 'frontend-error.log')
Write-Host "IntelliDoc starting at http://127.0.0.1:3000"
Write-Host "API process: $($api.Id); frontend process: $($web.Id). Logs are in the logs folder."
Write-Host "To stop these processes: Stop-Process -Id $($api.Id),$($web.Id)"

