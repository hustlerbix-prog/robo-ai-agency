# AI Demo Lab

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

## How to Use Each Feature

### 1. RAG Chat API

The core feature. Ask questions in Spanish and get answers grounded in the clinic's procedure manual.

**Prerequisites:** services running + procedures ingested into Qdrant (see Quick Start).

```bash
# Ask a question via curl
curl -s -X POST http://localhost:8080/chat \
  -H 'Content-Type: application/json' \
  -d '{"question":"Cual es el proceso de admision de pacientes?"}' | jq .

# Check service health
curl http://localhost:8080/health
```

Response format:
```json
{
  "answer": "El proceso de admisión...",
  "sources": [
    {"source": "procedimientos.pdf", "score": 0.91}
  ]
}
```

The server embeds the question, retrieves the top-3 matching chunks from Qdrant, builds a prompt, and calls the local Ollama model. Answers are restricted to what is in the documents.

---

### 2. Chat UI (Browser)

A zero-dependency HTML interface for the RAG chat endpoint.

```bash
xdg-open documents/chat.html
# or just open the file directly in any browser
```

Type a question in Spanish and hit Send. The UI posts to `http://localhost:8080/chat` and displays the answer. No build step or server required.

---

### 3. Synthetic Data Generation

Each script generates a different dataset. Run them one at a time (VRAM/CPU constraint).

```bash
cd ~/demo-lab
source ~/demo-env/bin/activate
set -a && source .env && set +a

# IS-05: Operations log — pure Faker, no API cost, runs in seconds
python scripts/generate_is05_operations.py
# Output: documents/is05_operations.csv

# IS-02: Invoice PDFs — pure fpdf2, no API cost, runs in seconds
python scripts/generate_is02_invoices.py
# Output: documents/sample_invoices/*.pdf + is02_invoices_manifest.json

# IS-01: Clinic emails — uses Claude Haiku, ~2 min, costs API credits
python scripts/generate_is01_emails.py
# Output: documents/is01_emails.json + is01_emails.txt

# IS-04: Patient intake forms — uses Claude Haiku, ~2 min
python scripts/generate_is04_intakes.py
# Output: documents/is04_intakes.json

# IS-03: Procedure manual — uses Claude Opus, ~5 min, higher API cost
python scripts/generate_is03_procedures.py
# Output: documents/procedimientos_clinica_santa_elena.pdf

# IS-03 (chunked): Split procedure PDF into JSON chunks for ingestion
python scripts/generate_is03_chunked.py
# Output: documents/is03_chunks/section_*.json

# AO-01: LoRA training data (optional)
python scripts/generate_ao01_training_data.py
# Output: lora/ directory with JSONL training pairs
```

---

### 4. Data Quality Check

Validates all generated datasets for completeness and schema correctness.

```bash
python scripts/check_data_quality.py
```

Run this after generating data to catch any missing fields, empty files, or malformed records before ingestion.

---

### 5. Document Ingestion into Qdrant

Embeds the procedure manual PDF and loads all chunks into the vector database.

```bash
python scripts/ingest_documents.py documents/procedimientos_clinica_santa_elena.pdf
```

What it does:
1. Reads and chunks the PDF
2. Sends each chunk to Ollama (`nomic-embed-text`) for embedding
3. Upserts vectors into the `clinica_santa_elena` Qdrant collection

After ingestion the RAG `/chat` endpoint is fully operational.

To verify the collection was populated:
```bash
curl http://localhost:6333/collections/clinica_santa_elena | jq .result.points_count
```

---

### 6. n8n Workflow Automation

Visual workflow builder for orchestrating tasks, webhooks, and integrations.

```
http://localhost:5678
```

Use cases in this lab:
- Trigger document ingestion via webhook
- Schedule data generation jobs
- Connect Google Drive / Gmail (requires OAuth credential setup in the UI)

To add Google credentials: n8n UI → Settings → Credentials → New → Google OAuth2.

---

### 7. Qdrant Vector DB (direct access)

Browse or query the vector store directly via its REST API.

```bash
# List collections
curl http://localhost:6333/collections | jq .

# Collection info (point count, vector size)
curl http://localhost:6333/collections/clinica_santa_elena | jq .

# Search by raw vector (advanced)
curl -X POST http://localhost:6333/collections/clinica_santa_elena/points/search \
  -H 'Content-Type: application/json' \
  -d '{"vector": [...768 floats...], "limit": 3, "with_payload": true}'
```

The web dashboard is also available at `http://localhost:6333/dashboard`.

---

### 8. Ollama Models (local LLM)

Two models run locally on the host — no API cost for inference.

```bash
# List installed models
ollama list

# Test embedding model
curl http://localhost:11434/api/embeddings \
  -d '{"model":"nomic-embed-text","prompt":"admision de pacientes"}'

# Test chat model interactively
ollama run qwen2.5:7b-instruct-q4_K_M

# Pull a different model if needed
ollama pull llama3.2:3b
```

---

## Known Quirks

- `docker` is aliased to `podman` — use `podman-compose` to manage services
- All containers require `security_opt: label=disable` (SELinux on Bazzite)
- Faker locale `es_PE` is invalid — fixed to `es` in IS-05 generator
- Generate scripts one at a time to avoid VRAM/CPU exhaustion
