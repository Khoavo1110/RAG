param([switch]$OpenBrowser)
$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$runDir = Join-Path $projectRoot 'data/nori-run'
New-Item -ItemType Directory -Force -Path $runDir | Out-Null
$pythonExe = Join-Path $projectRoot '.venv/Scripts/python.exe'
$viteScript = Join-Path $projectRoot 'frontend/node_modules/vite/bin/vite.js'
if (!(Test-Path -LiteralPath $pythonExe)) { throw 'Chưa có .venv. Hãy cài thư viện Python theo README_NORI.md.' }
if (!(Test-Path -LiteralPath $viteScript)) { throw 'Chưa có thư viện frontend. Chạy npm ci trong frontend.' }
Push-Location $projectRoot
try {
    docker compose up -d
    if ($LASTEXITCODE -ne 0) { throw 'Không khởi động được Docker. Hãy mở Docker Desktop.' }
    $ports = @(8000, 5173)
    foreach ($port in $ports) {
        if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) {
            throw "Cổng $port đang được sử dụng. Dừng ứng dụng đang chạy trước khi khởi động Nori."
        }
    }
    $api = Start-Process -FilePath $pythonExe -ArgumentList @('-m','uvicorn','backend.app.main:app','--host','127.0.0.1','--port','8000') -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runDir 'backend.log') -RedirectStandardError (Join-Path $runDir 'backend-error.log')
    $web = Start-Process -FilePath 'node' -ArgumentList @($viteScript,'--host','127.0.0.1','--port','5173') -WorkingDirectory (Join-Path $projectRoot 'frontend') -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runDir 'frontend.log') -RedirectStandardError (Join-Path $runDir 'frontend-error.log')
    @{ backend = $api.Id; frontend = $web.Id; root = $projectRoot } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runDir 'processes.json') -Encoding UTF8
    $ready = $false
    for ($attempt = 0; $attempt -lt 40; $attempt++) {
        try {
            $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/health' -TimeoutSec 5
            $null = Invoke-WebRequest -Uri 'http://127.0.0.1:5173' -UseBasicParsing -TimeoutSec 3
            $ready = $true
            break
        } catch { Start-Sleep -Milliseconds 500 }
    }
    if (!$ready) { throw "Chưa khởi động được Nori. Xem log trong $runDir; dừng bằng stop-nori.ps1." }
    Write-Host 'Nori: http://127.0.0.1:5173' -ForegroundColor Green
    Write-Host 'API:  http://127.0.0.1:8000/docs'
    Write-Host "Trạng thái: $($health.status) | Mô hình: $($health.model)"
    if ($OpenBrowser) { Start-Process 'http://127.0.0.1:5173' }
} finally { Pop-Location }
