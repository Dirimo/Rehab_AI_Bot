# Quick health checks for local / Docker dev
$ErrorActionPreference = "Continue"

function Test-Http($Url, $Label) {
    try {
        $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
        Write-Host "[OK] $Label ($($r.StatusCode))" -ForegroundColor Green
    }
    catch {
        Write-Host "[FAIL] $Label — $_" -ForegroundColor Red
    }
}

function Test-Tcp($HostName, $Port, $Label) {
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $tcp.Connect($HostName, $Port)
        $tcp.Close()
        Write-Host "[OK] $Label (port $Port open)" -ForegroundColor Green
    }
    catch {
        Write-Host "[FAIL] $Label (port $Port)" -ForegroundColor Red
    }
}

Write-Host "RehabBot health check" -ForegroundColor Cyan
Test-Http "http://localhost:8000/health" "Backend /health"
Test-Tcp "localhost" 8001 "MCP server"
Test-Tcp "localhost" 3000 "Frontend"
Test-Tcp "localhost" 11434 "Ollama"
