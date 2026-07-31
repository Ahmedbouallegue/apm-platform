"""Embeddings locaux (hashing) + fournisseurs optionnels OpenAI / Ollama."""
from __future__ import annotations

import hashlib
import math
import re
from typing import Sequence

import httpx
from django.conf import settings


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9àâäéèêëïîôùûüç_]{2,}", (text or "").lower())


def local_embed(text: str, dim: int | None = None) -> list[float]:
    """
    Embedding déterministe léger (feature hashing).
    Permet un RAG offline sans dépendances ML lourdes.
    """
    size = dim or settings.AI_EMBEDDING_DIM
    vec = [0.0] * size
    tokens = _tokenize(text)
    if not tokens:
        return vec
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        idx = int(digest[:8], 16) % size
        sign = 1.0 if int(digest[8:10], 16) % 2 == 0 else -1.0
        vec[idx] += sign
    # L2 normalize
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    return float(sum(x * y for x, y in zip(a, b)))


def openai_embed(text: str) -> list[float]:
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY manquant")
    model = settings.OPENAI_EMBEDDING_MODEL
    response = httpx.post(
        "https://api.openai.com/v1/embeddings",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": model, "input": text},
        timeout=60.0,
    )
    response.raise_for_status()
    return response.json()["data"][0]["embedding"]


def ollama_embed(text: str) -> list[float]:
    base = settings.OLLAMA_BASE_URL.rstrip("/")
    model = settings.OLLAMA_EMBED_MODEL
    response = httpx.post(
        f"{base}/api/embeddings",
        json={"model": model, "prompt": text},
        timeout=120.0,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("embedding") or data["embeddings"][0]


def embed_text(text: str) -> list[float]:
    provider = (settings.AI_PROVIDER or "local").lower()
    if provider == "openai" and settings.OPENAI_API_KEY:
        return openai_embed(text)
    if provider == "ollama":
        try:
            return ollama_embed(text)
        except Exception:
            # Fallback local si Ollama indisponible
            return local_embed(text)
    return local_embed(text)
