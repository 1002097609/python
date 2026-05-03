$conn = Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue | Where-Object { $_.State -eq 'Listen' }
if ($conn) { Stop-Process -Id $conn.OwningProcess -Force; Start-Sleep -Seconds 2 }
Set-Location "D:\claude_demo\demo2\demo\frontend"
$env:PATH = "D:\nodejs;$env:PATH"
Start-Process -WindowStyle Hidden -FilePath "D:\nodejs\npm.cmd" -ArgumentList "run","dev" -WorkingDirectory "D:\claude_demo\demo2\demo\frontend"
Start-Sleep -Seconds 5
$conn = Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue | Where-Object { $_.State -eq 'Listen' }
if ($conn) { Write-Host "Frontend OK: PID $($conn.OwningProcess)" } else { Write-Host "Frontend FAILED" }
