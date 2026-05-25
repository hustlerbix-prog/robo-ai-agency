import os
import sys
import uuid
import requests
import PyPDF2
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.environ.get("QDRANT_COLLECTION", "clinica_santa_elena")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "nomic-embed-text")

CHUNK_SIZE = 500
CHUNK_OVERLAP = 80


def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text


def chunk_text(text):
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end])
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return [c for c in chunks if c.strip()]


def embed(text):
    resp = requests.post(
        f"{OLLAMA_BASE_URL}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=60
    )
    resp.raise_for_status()
    return resp.json()["embedding"]


def ensure_collection(client, dim):
    collections = [c.name for c in client.get_collections().collections]
    if QDRANT_COLLECTION not in collections:
        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE)
        )
        print(f"Created collection: {QDRANT_COLLECTION}")
    else:
        print(f"Collection exists: {QDRANT_COLLECTION}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python ingest_documents.py <pdf_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    print(f"Extracting text from {pdf_path}...")
    text = extract_text_from_pdf(pdf_path)
    chunks = chunk_text(text)
    print(f"Created {len(chunks)} chunks")

    print("Embedding first chunk to get dimensions...")
    first_embedding = embed(chunks[0])
    dim = len(first_embedding)

    client = QdrantClient(url=QDRANT_URL)
    ensure_collection(client, dim)

    points = []
    for idx, chunk in enumerate(chunks):
        print(f"Embedding chunk {idx+1}/{len(chunks)}...")
        embedding = embed(chunk) if idx > 0 else first_embedding
        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={"text": chunk, "source": os.path.basename(pdf_path), "idx": idx}
        ))

    client.upsert(collection_name=QDRANT_COLLECTION, points=points)
    print(f"Upserted {len(points)} chunks into {QDRANT_COLLECTION}")


if __name__ == "__main__":
    main()
