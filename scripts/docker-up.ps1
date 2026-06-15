# Build and start the Docker stack (Ollama must run on the host)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Push-Location $Root
try {
    Write-Host "==> docker compose up --build" -ForegroundColor Cyan
    Write-Host "Ensure Ollama is running: ollama serve + ollama pull qwen3.5:9b-q4_K_M" -ForegroundColor Yellow
    docker compose up --build
}
finally {
    Pop-Location
}
