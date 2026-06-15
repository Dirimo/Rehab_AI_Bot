#!/usr/bin/env bash
# Build and start the Docker stack (Ollama must run on the host)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
echo "==> docker compose up --build"
echo "Ensure Ollama is running: ollama serve && ollama pull qwen3.5:9b-q4_K_M"
docker compose up --build
