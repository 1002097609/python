$ErrorActionPreference = "Stop"
try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:5173" -TimeoutSec 5
    Write-Host "Frontend OK: $($r.StatusCode)"
} catch {
    Write-Host "Frontend: $($_.Exception.Message)"
}
