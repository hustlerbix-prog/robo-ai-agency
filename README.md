# AI Demo Lab — Clínica Santa Elena

A self-hosted AI stack demonstrating RAG (Retrieval-Augmented Generation), workflow automation, and synthetic data generation for a fictional Spanish-language medical clinic.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Host machine (Bazzite / Fedora)                    │
│                                                     │
│  Ollama (systemd)  :11434                           │
│    ├─ nomic-embed-text   (embeddings)               │
│    └─ qwen2.5:7b-instruct-q4_K_M  (chat)           │
│                                                     │
│  Podman containers (podman-compose)                 │
│    ├─ demo-qdrant   :6333  (vector DB)              │
│    ├─ demo-n8n      :5678  (workflow automation)    │
│    └─ demo-rag      :8080  (Flask RAG API)          │
└─────────────────────────────────────────────────────┘
```

All containers run on `demo-net` bridge network.  
Ollama is reached by containers via `host.containers.internal:11434`.

---

## Services

### Ollama (host service)
- Runs as a systemd service on the host at `localhost:11434`
- Models: `nomic-embed-text` (768-dim embeddings), `qwen2.5:7b-instruct-q4_K_M` (chat)

### Qdrant `:6333`
- Vector database storing clinic procedure chunks
- Collection: `clinica_santa_elena`
- Data persisted in Docker volume `qdrant_data`

### n8n `:5678`
- Visual workflow automation tool
- Used for orchestrating document ingestion and webhook-based triggers
- Data persisted in volume `n8n_data`
- Config via `.env` variables: `N8N_HOST`, `N8N_PROTOCOL`, `WEBHOOK_URL`, `N8N_ENCRYPTION_KEY`

### RAG Server (Flask) `:8080`
- Custom Python/Flask API: `rag_server/app.py`
- **`GET /health`** — returns service status and collection name
- **`POST /chat`** — accepts `{"question": "..."}`, returns `{"answer": "...", "sources": [...]}`
- Flow: embed question → search Qdrant top-3 → build prompt → Ollama chat → return answer
- System prompt restricts answers strictly to context (Spanish formal responses)

---

## Documents & Data Sets

| ID | File(s) | Description | Generator |
|----|---------|-------------|-----------|
| IS-01 | `documents/is01_emails.json` / `.txt` | Synthetic clinic emails | Claude Haiku via `generate_is01_emails.py` |
| IS-02 | `documents/is02_invoices_manifest.json` + `sample_invoices/*.pdf` | SaaS-style invoice PDFs | fpdf2 via `generate_is02_invoices.py` |
| IS-03 | `documents/is03_chunks/section_*.json` | Clinic procedure manual chunks | Claude Haiku via `generate_is03_procedures.py` → chunked by `generate_is03_chunked.py` |
| IS-04 | `documents/is04_intakes.json` | Patient intake forms | Claude Haiku via `generate_is04_intakes.py` |
| IS-05 | `documents/is05_operations.csv` | Operations log (Faker data) | `generate_is05_operations.py` (locale: `es`) |
| AO-01 | *(optional)* | LoRA fine-tuning training data | `generate_ao01_training_data.py` |

The clinic procedures (IS-03) are the primary RAG corpus — ingested into Qdrant via `scripts/ingest_documents.py`.

---

## Chat UI

`documents/chat.html` — standalone browser UI (no build step).  
Open directly in browser; posts to `http://localhost:8080/chat`.

---

## Scripts

| Script | Purpose |
|--------|---------|
| `generate_all_demo_data.sh` | Runs all generators in order |
| `generate_is01_emails.py` | Emails via Claude Haiku (~2 min) |
| `generate_is02_invoices.py` | Invoice PDFs via fpdf2 (fast) |
| `generate_is03_procedures.py` | Procedure manual via Claude Opus (~5 min) |
| `generate_is03_chunked.py` | Splits procedure manual into JSON chunks |
| `generate_is04_intakes.py` | Intake forms via Claude Haiku (~2 min) |
| `generate_is05_operations.py` | Operations CSV via Faker (fast) |
| `generate_ao01_training_data.py` | LoRA training data (optional, costs API credits) |
| `check_data_quality.py` | Validates all generated datasets |
| `ingest_documents.py` | Embeds PDF chunks → loads into Qdrant |

---

## Lab Status

| Step | Status |
|------|--------|
| Config files & Dockerfile written | ✅ |
| All scripts written | ✅ |
| Docker image built (`gerardk0/demo-rag:latest`) | ✅ |
| Services running (qdrant, n8n, rag-server) | ✅ |
| Ollama models present | ✅ |
| Health checks passed | ✅ |
| **Generate demo data** | ⏳ pending |
| **Validate data quality** | ⏳ pending |
| **Ingest procedures into Qdrant** | ⏳ pending |
| **Test RAG /chat endpoint** | ⏳ pending |
| Generate LoRA training data | optional |
| Connect Google credentials in n8n | optional |
| Push image to Docker Hub | optional |

---

## Quick Start

```bash
cd ~/demo-lab
source ~/demo-env/bin/activate
set -a && source .env && set +a

# Start services
podman-compose --env-file .env up -d

# Generate data (one at a time — VRAM/CPU constrained)
python scripts/generate_is05_operations.py   # Faker, fast
python scripts/generate_is02_invoices.py     # fpdf2, fast
python scripts/generate_is01_emails.py       # Claude Haiku, ~2 min
python scripts/generate_is04_intakes.py      # Claude Haiku, ~2 min
python scripts/generate_is03_procedures.py   # Claude Opus, ~5 min

# Validate
python scripts/check_data_quality.py

# Ingest into Qdrant
python scripts/ingest_documents.py documents/procedimientos_clinica_santa_elena.pdf

# Test
curl -s -X POST http://localhost:8080/chat \
  -H 'Content-Type: application/json' \
  -d '{"question":"Cual es el proceso de admision de pacientes?"}'

# Or open the chat UI
xdg-open documents/chat.html
```

---

## Known Quirks

- `docker` is aliased to `podman` — use `podman-compose` to manage services
- All containers require `security_opt: label=disable` (SELinux on Bazzite)
- Faker locale `es_PE` is invalid — fixed to `es` in IS-05 generator
- Generate scripts one at a time to avoid VRAM/CPU exhaustion
