Get-Process | Where-Object { $_.ProcessName -match 'node|vite' } | Select-Object Id, ProcessName, StartTime
