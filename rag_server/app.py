import os
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from qdrant_client import QdrantClient

app = Flask(__name__)
CORS(app)

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.environ.get("QDRANT_COLLECTION", "clinica_santa_elena")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "nomic-embed-text")
CHAT_MODEL = os.environ.get("CHAT_MODEL", "qwen2.5:7b-instruct-q4_K_M")

qdrant = QdrantClient(url=QDRANT_URL)

SYSTEM_PROMPT = """Eres un asistente especializado en los procedimientos internos de la Clinica Santa Elena.
Responde UNICAMENTE basandote en el contexto proporcionado.
Si la informacion no se encuentra en el contexto, responde exactamente:
'No encuentro esa informacion en los documentos disponibles'
Responde siempre en espanol formal y de manera concisa."""


def embed_text(text):
    resp = requests.post(
        f"{OLLAMA_BASE_URL}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=60
    )
    resp.raise_for_status()
    return resp.json()["embedding"]


def search_qdrant(embedding, top_k=3):
    results = qdrant.search(
        collection_name=QDRANT_COLLECTION,
        query_vector=embedding,
        limit=top_k,
        with_payload=True
    )
    return results


def chat_ollama(context, question):
    prompt = f"""Contexto:
{context}

Pregunta: {question}"""
    resp = requests.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        json={
            "model": CHAT_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "stream": False
        },
        timeout=120
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"]


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "question is required"}), 400

    try:
        embedding = embed_text(question)
        hits = search_qdrant(embedding)

        sources = []
        context_parts = []
        for hit in hits:
            payload = hit.payload
            context_parts.append(payload.get("text", ""))
            sources.append({
                "source": payload.get("source", ""),
                "score": hit.score
            })

        context = "\n\n".join(context_parts)
        answer = chat_ollama(context, question)

        return jsonify({"answer": answer, "sources": sources})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "collection": QDRANT_COLLECTION,
        "ollama_url": OLLAMA_BASE_URL
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
