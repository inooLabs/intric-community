# Local Development with Self-Hosted Models

This guide covers running intric-community against locally hosted LLM and embedding endpoints instead of cloud providers (OpenAI, Anthropic, etc.).

## Prerequisites

- Docker + Docker Compose
- Poetry (inside the devcontainer)
- A locally served embedding model (e.g. `bge-m3` via llama.cpp)
- A locally served completion model (e.g. any vLLM-compatible endpoint)

---

## Devcontainer setup

The devcontainer exposes two ports on the host:

| Port | Service |
|------|---------|
| 8123 | Backend (uvicorn/gunicorn) |
| 3000 | Frontend (Next.js, started separately) |

Start the stack:

```bash
docker compose -f .devcontainer/docker-compose.yml up -d
```

---

## Backend setup

### 1. Install dependencies

Inside the devcontainer (`docker exec -it intric-community_devcontainer-intric-1 bash`):

```bash
cd /workspace/backend
pip install poetry
pip install --upgrade packaging   # packaging>=24.2 required
poetry install
```

### 2. Configure environment

Copy `.env.example` to `.env` (or edit `.env` directly). Minimum required fields:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_PORT=5432
POSTGRES_HOST=db          # use container name, not localhost
POSTGRES_DB=postgres
REDIS_HOST=redis
REDIS_PORT=6379

JWT_SECRET=change-me
```

Leave `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc. empty if you are not using those providers. The backend handles missing keys gracefully.

### 3. Initialise the database

```bash
cd /workspace/backend
poetry run python init_db.py
```

This runs alembic migrations and seeds a default tenant and admin user:

| Field | Value |
|-------|-------|
| Email | `user@example.com` |
| Password | `Password1!` |

### 4. Start the backend

```bash
poetry run start
```

The API is now reachable at `http://localhost:8123`.

---

## Adding self-hosted models

Models are managed in `backend/src/intric/server/dependencies/ai_models.yml`. The backend syncs the database with this file on every startup — models not present in the YAML are deleted, and new entries are created automatically.

### Embedding models

Add an entry under `embedding_models`. For OpenAI-API-compatible endpoints (llama.cpp, vLLM):

```yaml
embedding_models:
  - name: 'bge-m3-Q4_K_M.gguf'    # must match the model ID returned by /v1/models
    family: 'vllm'
    open_source: true
    max_input: 8192
    dimensions: 1024
    is_deprecated: false
    stability: 'experimental'
    hosting: 'usa'                  # use 'usa' to avoid module-gating
    description: BGE-M3 quantized embedding model served locally via llama.cpp.
    base_url: 'https://your-embed-host/v1'
```

> **Note:** `hosting: 'eu'` and `hosting: 'swe'` require tenant-level modules (`EU_HOSTING`, `SWE_HOSTING`). Use `hosting: 'usa'` for local endpoints to keep them accessible without additional configuration.

Verify the model ID with:

```bash
curl -k https://your-embed-host/v1/models
```

### Completion models

Add an entry under `completion_models`:

```yaml
completion_models:
  - name: 'fast-small'             # must match the model ID returned by /v1/models
    nickname: 'Fast Small (local)'
    family: 'vllm'
    token_limit: 8192
    stability: 'experimental'
    is_deprecated: false
    hosting: 'usa'
    description: Locally hosted vLLM model.
    open_source: true
    reasoning: false
    vision: false
    base_url: 'https://your-llm-host/v1'
```

### SSL certificates

If your local endpoints use self-signed or internally-signed TLS certificates, the backend skips certificate verification automatically for any model with `base_url` set.

---

## Enabling models for a tenant

After restarting the backend (so `init_models` populates the DB), enable the models for your tenant:

```bash
# Embedding model
docker exec intric-community_devcontainer-db-1 psql -U postgres -c "
INSERT INTO embedding_model_settings (embedding_model_id, tenant_id, is_org_enabled, is_org_default)
SELECT em.id, t.id, true, true
FROM embedding_models em, tenants t
WHERE em.name = 'bge-m3-Q4_K_M.gguf' AND t.name = 'ExampleTenant'
ON CONFLICT DO NOTHING;"

# Completion model
docker exec intric-community_devcontainer-db-1 psql -U postgres -c "
INSERT INTO completion_model_settings (completion_model_id, tenant_id, is_org_enabled, is_org_default)
SELECT cm.id, t.id, true, true
FROM completion_models cm, tenants t
WHERE cm.name = 'fast-small' AND t.name = 'ExampleTenant'
ON CONFLICT DO NOTHING;"
```

> **Important:** `init_models` re-creates models by name on every startup, preserving UUIDs. However, if you inserted a model directly into the DB before adding it to the YAML, the UUID will change on the next restart and the `*_settings` row will be orphaned. Always add models to the YAML first, then enable them via the settings INSERT after restart.

---

## Frontend setup

```bash
cd /workspace/frontend
pnpm install
pnpm dev
```

The UI is available at `http://localhost:3000`.

---

## ARQ worker

The worker processes background tasks (file ingestion, embedding). Start it separately:

```bash
cd /workspace/backend
poetry run arq src.intric.worker.arq.WorkerSettings
```

The worker must be restarted whenever backend Python code changes, just like the backend itself.

---

## LLM observability with Langfuse

The backend optionally traces all LLM interactions (chat completions and embeddings) to a [Langfuse](https://langfuse.com) instance. Tracing is inactive unless enabled with real keys.

### Configuration

Add to `backend/.env`:

```env
LANGFUSE_ENABLED=True
LANGFUSE_HOST=https://your-langfuse-host
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...

# Optional
LANGFUSE_DEBUG=False
LANGFUSE_ENVIRONMENT=local-development
LANGFUSE_USER_ID=example-user
```

| Setting | Purpose |
|---------|---------|
| `LANGFUSE_ENABLED` | Master switch; when `False`, all Langfuse code is a no-op |
| `LANGFUSE_HOST` | Base URL of your Langfuse instance |
| `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` | Project API keys (create them in the Langfuse UI under *Settings → API Keys*) |
| `LANGFUSE_DEBUG` | Verbose SDK logging for troubleshooting |
| `LANGFUSE_ENVIRONMENT` | Environment label shown in the Langfuse UI (e.g. `local-development`) |
| `LANGFUSE_USER_ID` | User attribution attached to every traced LLM call |

Restart the backend after changing these. The ARQ worker does not trace (only the API process does).

### How it works

- On startup, `init_langfuse()` (in `backend/src/intric/observability/langfuse_setup.py`) creates the global Langfuse client and switches all OpenAI-compatible adapters to traced client drop-ins.
- Chat completions and embeddings against **any** provider — including local `vllm`-family models with a `base_url` — are exported to Langfuse as OpenTelemetry spans with prompts, completions, token usage, and latency.
- When disabled, the factory returns plain `openai.AsyncOpenAI` clients — zero overhead, no SDK calls.

### Self-signed certificates

Homelab endpoints typically use internally-signed TLS certificates. The observability module handles this automatically:

- **Non-tracing API requests** (auth check, media upload): custom `httpx.Client(verify=False)`
- **OTEL span export**: the `OTLPSpanExporter` is patched to skip verification. Note that newer `opentelemetry-exporter-otlp-proto-http` versions pass `verify=True` explicitly on every POST (overriding the session), so the exporter instance's `certificate_file` is forced to `False`.

### Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `CERTIFICATE_VERIFY_FAILED` on `/api/public/otel/v1/traces` | Exporter TLS patch not applied (stale process) | Restart the backend; check the startup log for `export TLS verify disabled: True` |
| `400 ... Event type not accepted` on ingestion | SDK v2.x against a Langfuse v3+ server (legacy ingestion endpoint) | Use `langfuse>=3` (traces go through the OTEL endpoint) |
| `AttributeError: ... 'instrument_openai_client'` | Stale process running pre-v3 module code | Restart the affected process (worker must be restarted manually) |
| Traces missing user/environment | `LANGFUSE_USER_ID` / `LANGFUSE_ENVIRONMENT` unset | Set them in `backend/.env` and restart |

> **Note:** `backend/.env` is gitignored — never commit real API keys.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Bearer ` illegal header | `OPENAI_API_KEY` is empty and falls through to OpenAI adapter | Backend now falls back to `no-key`; ensure the correct model with `base_url` is selected in the space |
| `No module named 'packaging.licenses'` | `packaging` < 24.2 installed | `poetry run pip install --upgrade packaging` |
| Model shows as **disabled** in UI | `hosting` is `eu`/`swe` and tenant lacks the module, or `is_org_enabled = false` | Set `hosting: 'usa'` in YAML and re-run the enable INSERT |
| Embedding model deleted on restart | Model was inserted directly into DB, not via YAML | Add it to `ai_models.yml` |
| SSL certificate error | Self-signed cert on local endpoint | Handled automatically when `base_url` is set on the model |
