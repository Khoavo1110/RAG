$ErrorActionPreference = 'Continue'
$projectRoot = $PSScriptRoot
$pidFile = Join-Path $projectRoot 'data/nori-run/processes.json'

$stoppedAny = $false

# 1. Dừng theo tệp lưu PID (nếu có)
if (Test-Path -LiteralPath $pidFile) {
    try {
        $record = Get-Content -LiteralPath $pidFile -Raw | ConvertFrom-Json
        if ($record.root -eq $projectRoot) {
            foreach ($kind in @('backend','frontend')) {
                $processId = [int]$record.$kind
                if ($processId -gt 0) {
                    $proc = Get-Process -Id $processId -ErrorAction SilentlyContinue
                    if ($proc) {
                        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
                        Write-Host "Đã dừng $kind (PID: $processId) từ tệp cấu hình." -ForegroundColor Green
                        $stoppedAny = $true
                    }
                }
            }
        }
    } catch {
        Write-Warning "Không đọc được processes.json: $_"
    } finally {
        Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
    }
}

# 2. Quét trực tiếp và giải phóng cổng 8000 (Backend API) và 5173 (Frontend Web)
$targetPorts = @(8000, 5173)
foreach ($port in $targetPorts) {
    $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    foreach ($conn in $connections) {
        $procId = $conn.OwningProcess
        if ($procId -gt 0) {
            $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
            if ($proc) {
                Write-Host "Phát hiện tiến trình $($proc.ProcessName) (PID: $procId) đang lắng nghe trên cổng $port. Đang dừng..." -ForegroundColor Yellow
                Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
                Write-Host "Đã giải phóng cổng $port." -ForegroundColor Green
                $stoppedAny = $true
            }
        }
    }
}

if ($stoppedAny) {
    Write-Host "Tất cả tiến trình Nori trên cổng 8000 và 5173 đã được dừng hoàn tất." -ForegroundColor Green
} else {
    Write-Host "Không có tiến trình nào đang chiếm cổng 8000 hoặc 5173." -ForegroundColor Cyan
}

Write-Host "Các container dữ liệu Docker (PostgreSQL, Neo4j) vẫn được giữ nguyên." -ForegroundColor Gray

