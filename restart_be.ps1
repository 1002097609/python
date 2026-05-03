$conn = Get-NetTCPConnection -LocalPort 8081 -ErrorAction SilentlyContinue
if ($conn) { Stop-Process -Id $conn.OwningProcess -Force; Start-Sleep -Seconds 2 }
Start-Process -WindowStyle Hidden -FilePath "python" -ArgumentList "server.py" -WorkingDirectory "D:\claude_demo\demo2\demo"
Start-Sleep -Seconds 5
$conn = Get-NetTCPConnection -LocalPort 8081 -ErrorAction SilentlyContinue
if ($conn) { Write-Host "Backend OK: PID $($conn.OwningProcess)" } else { Write-Host "Backend FAILED" }
