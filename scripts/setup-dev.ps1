# RehabBot — first-time local dev setup (Windows)
# Run from repo root:  .\scripts\setup-dev.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "==> RehabBot dev setup" -ForegroundColor Cyan

# --- Backend venv ---
$BackendVenv = Join-Path $Root "backend\.venv"
if (-not (Test-Path $BackendVenv)) {
    Write-Host "Creating backend virtualenv..."
    python -m venv $BackendVenv
}
& "$BackendVenv\Scripts\pip.exe" install -r (Join-Path $Root "backend\requirements.txt")

# --- MCP venv ---
$McpVenv = Join-Path $Root "mcp-server\.venv"
if (-not (Test-Path $McpVenv)) {
    Write-Host "Creating mcp-server virtualenv..."
    python -m venv $McpVenv
}
& "$McpVenv\Scripts\pip.exe" install -r (Join-Path $Root "mcp-server\requirements.txt")

# --- Frontend deps ---
if (Test-Path (Join-Path $Root "frontend\package.json")) {
    Push-Location (Join-Path $Root "frontend")
    if (-not (Test-Path "node_modules")) {
        Write-Host "Installing frontend npm packages..."
        npm install
    }
    Pop-Location
}

# --- Env files ---
$BackendEnv = Join-Path $Root "backend\.env"
if (-not (Test-Path $BackendEnv)) {
    Copy-Item (Join-Path $Root "backend\.env.example") $BackendEnv -ErrorAction SilentlyContinue
    if (-not (Test-Path $BackendEnv)) {
        @"
DATABASE_URL=postgresql+psycopg://postgres:rehabbot@localhost:5432/rehabbot
SESSION_EXPIRATION_DAYS=21
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3.5:9b-q4_K_M
OLLAMA_THINK=false
OLLAMA_NUM_PREDICT=1024
MCP_BASE_URL=http://localhost:8001
"@ | Set-Content $BackendEnv -Encoding UTF8
    Write-Host "Created backend/.env (adjust DATABASE_URL if Postgres uses another port)."
}

$McpEnv = Join-Path $Root "mcp-server\.env"
if (-not (Test-Path $McpEnv)) {
    @"
MCP_HOST=0.0.0.0
MCP_PORT=8001
SCRAPING_RATE_LIMIT_SECONDS=2
"@ | Set-Content $McpEnv -Encoding UTF8
    Write-Host "Created mcp-server/.env"
}

Write-Host ""
Write-Host "Setup complete. Next: .\scripts\start-dev.ps1" -ForegroundColor Green
