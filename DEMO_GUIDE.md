# Demo Deployment & Execution Guide — AI Demo Lab

Full walkthrough to deploy the stack from scratch and run a live demo covering all features.
Estimated total time: **30–45 minutes** (mostly waiting on data generation).

---

## Prerequisites

| Requirement | Version | Check |
|-------------|---------|-------|
| Podman | 4.x+ | `podman --version` |
| podman-compose | any | `podman-compose --version` |
| Python | 3.11+ | `python --version` |
| Ollama | any | `ollama --version` |
| curl + jq | any | `curl --version && jq --version` |
| Anthropic API key | — | needed for IS-01, IS-03, IS-04 data generation |

---

## Step 1 — Clone the Repository

```bash
git clone https://github.com/hustlerbix-prog/robo-ai-agency.git demo-lab
cd demo-lab
```

---

## Step 2 — Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

```
ANTHROPIC_API_KEY=sk-ant-...       # required for data generation
N8N_ENCRYPTION_KEY=<random-32-chars>
N8N_HOST=localhost
N8N_PROTOCOL=http
WEBHOOK_URL=http://localhost:5678/
QDRANT_COLLECTION=clinica_santa_elena
EMBED_MODEL=nomic-embed-text
CHAT_MODEL=qwen2.5:7b-instruct-q4_K_M
```

---

## Step 3 — Install Ollama and Pull Models

```bash
# Install Ollama if not present
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
ollama serve &   # or: systemctl --user start ollama

# Pull required models (one at a time — ~5 GB total)
ollama pull nomic-embed-text
ollama pull qwen2.5:7b-instruct-q4_K_M

# Verify
ollama list
```

---

## Step 4 — Set Up Python Environment

```bash
python -m venv ~/demo-env
source ~/demo-env/bin/activate
pip install faker fpdf2 PyPDF2 anthropic
```

---

## Step 5 — Start Services

**Option A — Pull pre-built image from Docker Hub (recommended)**

```bash
# Edit docker-compose.yml: replace the rag-server build section with:
#   image: docker.io/hustlerbixprog/robo-ai-agency:test_v1

podman-compose --env-file .env up -d
```

**Option B — Build image locally**

```bash
podman build -t demo-rag:latest -f Dockerfile.rag .
podman-compose --env-file .env up -d
```

Verify all three containers are running:

```bash
podman ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

Expected output:
```
demo-qdrant   Up   0.0.0.0:6333->6333/tcp
demo-n8n      Up   0.0.0.0:5678->5678/tcp
demo-rag      Up   0.0.0.0:8080->8080/tcp
```

---

## Step 6 — Health Checks

```bash
# Ollama
curl -s http://localhost:11434/api/tags | jq '.models[].name'

# Qdrant
curl -s http://localhost:6333/healthz

# RAG server
curl -s http://localhost:8080/health | jq .

# n8n
curl -s -o /dev/null -w "%{http_code}" http://localhost:5678
```

All should return 200 / OK before proceeding.

---

## Step 7 — Generate Demo Data

Activate the venv and load env vars first:

```bash
source ~/demo-env/bin/activate
set -a && source .env && set +a
```

Run each script **one at a time** (VRAM/CPU constraint — wait for each to finish):

```bash
# 1. Operations log — Faker only, ~10 seconds
python scripts/generate_is05_operations.py

# 2. Invoice PDFs — fpdf2 only, ~10 seconds
python scripts/generate_is02_invoices.py

# 3. Clinic emails — Claude Haiku, ~2 minutes
python scripts/generate_is01_emails.py

# 4. Patient intake forms — Claude Haiku, ~2 minutes
python scripts/generate_is04_intakes.py

# 5. Procedure manual PDF — Claude Opus, ~5 minutes
python scripts/generate_is03_procedures.py

# 6. Chunk the procedure manual into JSON sections
python scripts/generate_is03_chunked.py
```

Validate all datasets:

```bash
python scripts/check_data_quality.py
```

---

## Step 8 — Ingest Procedures into Qdrant

```bash
python scripts/ingest_documents.py documents/procedimientos_clinica_santa_elena.pdf
```

Confirm vectors were loaded:

```bash
curl -s http://localhost:6333/collections/clinica_santa_elena | jq '.result.points_count'
# Should return a number > 0
```

---

## Step 9 — Run the Demo

At this point all features are live. Walk through each one:

---

### Feature 1 — RAG Chat API

```bash
curl -s -X POST http://localhost:8080/chat \
  -H 'Content-Type: application/json' \
  -d '{"question":"Cual es el proceso de admision de pacientes?"}' | jq .
```

Try more questions:

```bash
curl -s -X POST http://localhost:8080/chat \
  -H 'Content-Type: application/json' \
  -d '{"question":"Cuales son los protocolos de emergencia?"}' | jq .

curl -s -X POST http://localhost:8080/chat \
  -H 'Content-Type: application/json' \
  -d '{"question":"Como se gestionan las citas medicas?"}' | jq .
```

The response includes the answer and the source chunks with relevance scores.

---

### Feature 2 — Chat UI (Browser)

```bash
xdg-open documents/chat.html
```

Or open `documents/chat.html` in any browser. Type questions in Spanish and get live responses from the RAG backend.

---

### Feature 3 — Qdrant Dashboard

Open in browser:
```
http://localhost:6333/dashboard
```

Navigate to the `clinica_santa_elena` collection to browse stored vectors, view payloads, and run test searches visually.

---

### Feature 4 — n8n Workflow Automation

Open in browser:
```
http://localhost:5678
```

- Create a new workflow
- Add an HTTP Request node pointing to `http://demo-rag:8080/chat`
- Trigger it via webhook or manually to send questions to the RAG API from within n8n
- Optionally connect Google credentials: Settings → Credentials → New → Google OAuth2

---

### Feature 5 — Ollama Local LLM (interactive)

```bash
ollama run qwen2.5:7b-instruct-q4_K_M
```

Chat with the model directly — no RAG, no context, just the base model. Useful to contrast with the RAG-grounded answers.

---

### Feature 6 — Generated Documents

| File | How to view |
|------|------------|
| `documents/is01_emails.txt` | `cat documents/is01_emails.txt` |
| `documents/is02_invoices_manifest.json` | `jq . documents/is02_invoices_manifest.json` |
| `documents/sample_invoices/*.pdf` | `xdg-open documents/sample_invoices/invoice_01_saas_minimalist.pdf` |
| `documents/is04_intakes.json` | `jq . documents/is04_intakes.json` |
| `documents/is05_operations.csv` | `column -t -s, documents/is05_operations.csv | head -20` |
| `documents/is03_chunks/` | `ls documents/is03_chunks/ && jq . documents/is03_chunks/section_01.json` |

---

### Feature 7 — LoRA Training Data (optional)

```bash
python scripts/generate_ao01_training_data.py
```

Generates question/answer pairs in JSONL format for fine-tuning a model on clinic-specific knowledge. Output goes to `lora/`.

---

## Step 10 — Tear Down

```bash
podman-compose down          # stop and remove containers
podman-compose down -v       # also delete volumes (qdrant data, n8n data)
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| RAG returns "No encuentro esa información" | Procedures not ingested — re-run Step 8 |
| `podman push` denied | Re-login: `podman login docker.io` |
| Container can't reach Ollama | Check `host.containers.internal` resolves — SELinux may block; add `--network=host` to test |
| Qdrant collection missing | Run ingest script again; check `points_count > 0` |
| Script crashes mid-generation | VRAM exhausted — wait 2 min, re-run the same script |
| n8n blank page | Wait 30s after `podman-compose up`; n8n is slow to start |

---

## Ports Summary

| Service | URL |
|---------|-----|
| Ollama | http://localhost:11434 |
| Qdrant API | http://localhost:6333 |
| Qdrant Dashboard | http://localhost:6333/dashboard |
| n8n | http://localhost:5678 |
| RAG API | http://localhost:8080 |
| Chat UI | open `documents/chat.html` in browser |
