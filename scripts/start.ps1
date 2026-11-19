param(
  [switch]$Seed,
  [ValidateRange(1,65535)][int]$WebPort = 3000,
  [ValidateRange(1,65535)][int]$ApiPort = 8000
)
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
if ($WebPort -eq $ApiPort) { throw 'Choose separate ports for the frontend and the API.' }
$busy = [Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties().GetActiveTcpListeners().Port
foreach ($port in @($WebPort, $ApiPort)) {
  if ($busy -contains $port) { throw "Port $port is already in use. Open the existing app or choose free -WebPort and -ApiPort values." }
}
& $pythonPath -c "import importlib.util,sys; sys.exit(0 if importlib.util.find_spec('alembic') else 1)"
if ($LASTEXITCODE -ne 0) { throw 'Alembic is missing from this .venv. Use Python 3.12 and run .\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt first.' }
if (!(Test-Path -LiteralPath (Join-Path $frontendPath 'node_modules/next/dist/bin/next'))) { throw 'Install frontend dependencies with npm ci in the frontend folder.' }
Push-Location $backendPath
try {
  & $pythonPath -m alembic upgrade head
  if ($LASTEXITCODE -ne 0) { throw 'Database migration failed. Check the backend configuration.' }
} finally { Pop-Location }
if ($Seed) {
  Push-Location $backendPath
  try { & $pythonPath -m app.seed; if ($LASTEXITCODE -ne 0) { throw 'Demo setup failed' } } finally { Pop-Location }
}
$logsPath = Join-Path $projectRoot 'logs'
New-Item -ItemType Directory -Force $logsPath | Out-Null
$api = Start-Process -FilePath $pythonPath -ArgumentList "-m uvicorn app.main:app --host 127.0.0.1 --port $ApiPort" -WorkingDirectory $backendPath -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logsPath 'backend.log') -RedirectStandardError (Join-Path $logsPath 'backend-error.log')
$previousBackendUrl = $env:BACKEND_URL
try {
  $env:BACKEND_URL = "http://127.0.0.1:$ApiPort"
  $web = Start-Process -FilePath $nodePath -ArgumentList "node_modules/next/dist/bin/next dev --hostname 127.0.0.1 --port $WebPort" -WorkingDirectory $frontendPath -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logsPath 'frontend.log') -RedirectStandardError (Join-Path $logsPath 'frontend-error.log')
} catch {
  $api.Kill()
  throw
} finally { $env:BACKEND_URL = $previousBackendUrl }
Write-Host "IntelliDoc starting at http://127.0.0.1:$WebPort"
Write-Host "API process: $($api.Id); frontend process: $($web.Id). Logs are in the logs folder."
Write-Host "To stop these processes: Stop-Process -Id $($api.Id),$($web.Id)"

