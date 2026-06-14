# RehabBot — AI Rehabilitation Assistant

> Educational open-source prototype. **Do not use in a real medical context.**

RehabBot is a physiotherapy/rehabilitation chatbot. A user asks a question
(e.g. *"What exercises help with lower back pain?"*) and the system answers using
a **local LLM** that can call **tools** to look up trustworthy public medical sources.

## Architecture (who talks to whom)

```text
[Browser]
   │  WebSocket + REST
   ▼
[Frontend: Nuxt 3]  ── Member 1
   │
   ▼
[Backend: FastAPI orchestrator] ── Member 2   (runs the "Agent Loop")
   │                 │
   ▼                 ▼
[Ollama + LLM]   [MCP server: FastMCP + scraping] ── Member 3
  Member 4           │
                     ▼
              [Public medical sites]

[PostgreSQL] + [Docker] + [docs] ── Member 5 (infrastructure under everything)
```

### The Agent Loop (core idea)
1. Frontend sends a user message to the backend.
2. Backend builds the context (system prompt + history + new message) and sends it to Ollama.
3. The LLM either answers directly, or emits a `tool_call`.
4. If a tool is requested, the backend calls the MCP server (which scrapes data) and re-injects the result.
5. The LLM produces the final answer, which the backend streams back to the frontend.
6. Sessions, messages, and tool calls are persisted in PostgreSQL.

## Repository layout

| Folder              | Owner     | Tech                                  |
| ------------------- | --------- | ------------------------------------- |
| `frontend/`         | Member 1  | Nuxt 3 / Vue.js (TypeScript)          |
| `backend/`          | Member 2  | Python / FastAPI                      |
| `mcp-server/`       | Member 3  | FastMCP + BeautifulSoup / Zendriver   |
| `docs/`, `scripts/` | Member 5  | Architecture & presentation docs      |
| `docker-compose.yml`| Member 5  | PostgreSQL + Docker orchestration     |

LLM configuration (Ollama + Qwen3 1.7B / LLaMA 3.2) is owned by Member 4.

## Getting started

> Detailed instructions are filled in as each module is built.

```bash
# 1. Copy the environment template and adjust values
cp .env.example .env

# 2. (Coming soon) Start everything with Docker
# docker compose up --build
```

## Status

This project is being built incrementally, one module at a time:
Backend → MCP server → LLM → Frontend → DevOps/Docs.
