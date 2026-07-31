"""Pipeline RAG : retrieval + génération de réponse."""
from __future__ import annotations

from dataclasses import dataclass

import httpx
from django.conf import settings

from apps.assistant.models import ChatMessage, ChatSession, KnowledgeChunk
from apps.assistant.services.embeddings import cosine_similarity, embed_text


@dataclass
class RetrievedChunk:
    chunk: KnowledgeChunk
    score: float


def retrieve_chunks(question: str, *, top_k: int | None = None) -> list[RetrievedChunk]:
    k = top_k or settings.AI_TOP_K
    query_vec = embed_text(question)
    scored: list[RetrievedChunk] = []
    qs = KnowledgeChunk.objects.filter(source__is_active=True).select_related("source")
    for chunk in qs.iterator(chunk_size=200):
        emb = chunk.embedding or []
        score = cosine_similarity(query_vec, emb)
        if score > 0:
            scored.append(RetrievedChunk(chunk=chunk, score=score))
    scored.sort(key=lambda item: item.score, reverse=True)
    return scored[:k]


def _build_context(chunks: list[RetrievedChunk]) -> str:
    blocks = []
    for i, item in enumerate(chunks, start=1):
        src = item.chunk.source
        blocks.append(
            f"[{i}] ({src.get_source_type_display()} — {src.title})\n{item.chunk.content}"
        )
    return "\n\n".join(blocks)


def _extractive_answer(question: str, chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return (
            "Je n'ai trouvé aucune information pertinente dans le patrimoine APM indexé. "
            "Lancez une réindexation depuis l'assistant, puis reformulez votre question."
        )
    lines = [
        "Voici ce que je trouve dans le patrimoine applicatif Topnet (RAG extractif) :",
        "",
    ]
    for i, item in enumerate(chunks, start=1):
        src = item.chunk.source
        lines.append(
            f"{i}. **{src.title}** ({src.get_source_type_display()}, score {item.score:.2f})"
        )
        lines.append(item.chunk.content[:500])
        lines.append("")
    lines.append(f"Question posée : « {question} »")
    return "\n".join(lines)


def _openai_generate(question: str, context: str) -> str:
    api_key = settings.OPENAI_API_KEY
    response = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": settings.OPENAI_CHAT_MODEL,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Tu es l'assistant APM Topnet pour la DSI. "
                        "Réponds en français, de façon précise et professionnelle. "
                        "Base-toi uniquement sur le contexte fourni. "
                        "Cite les sources entre crochets [n] quand tu t'appuies sur elles. "
                        "Si l'information manque, dis-le clairement."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Contexte:\n{context}\n\nQuestion:\n{question}",
                },
            ],
        },
        timeout=90.0,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def _ollama_generate(question: str, context: str) -> str:
    base = settings.OLLAMA_BASE_URL.rstrip("/")
    prompt = (
        "Tu es l'assistant APM Topnet. Réponds en français à partir du contexte uniquement.\n\n"
        f"Contexte:\n{context}\n\nQuestion:\n{question}\n\nRéponse:"
    )
    response = httpx.post(
        f"{base}/api/generate",
        json={
            "model": settings.OLLAMA_CHAT_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2},
        },
        timeout=180.0,
    )
    response.raise_for_status()
    return response.json().get("response", "").strip()


def generate_answer(question: str, chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return _extractive_answer(question, chunks)
    context = _build_context(chunks)
    provider = (settings.AI_PROVIDER or "local").lower()
    try:
        if provider == "openai" and settings.OPENAI_API_KEY:
            return _openai_generate(question, context)
        if provider == "ollama":
            return _ollama_generate(question, context)
    except Exception:
        # Toujours renvoyer une réponse utile
        pass
    return _extractive_answer(question, chunks)


def ask_question(*, user, question: str, session: ChatSession | None = None) -> dict:
    question = (question or "").strip()
    if not question:
        raise ValueError("La question est obligatoire.")

    if session is None:
        session = ChatSession.objects.create(
            user=user,
            title=question[:80],
        )
    elif not session.title:
        session.title = question[:80]
        session.save(update_fields=["title", "updated_at"])

    ChatMessage.objects.create(
        session=session,
        role=ChatMessage.Role.USER,
        content=question,
    )

    chunks = retrieve_chunks(question)
    answer = generate_answer(question, chunks)
    sources = [
        {
            "title": item.chunk.source.title,
            "type": item.chunk.source.source_type,
            "type_display": item.chunk.source.get_source_type_display(),
            "score": round(item.score, 4),
            "excerpt": item.chunk.content[:280],
            "source_id": item.chunk.source.source_id,
        }
        for item in chunks
    ]

    message = ChatMessage.objects.create(
        session=session,
        role=ChatMessage.Role.ASSISTANT,
        content=answer,
        sources=sources,
    )
    session.save(update_fields=["updated_at"])

    return {
        "session_id": session.pk,
        "question": question,
        "answer": answer,
        "sources": sources,
        "message_id": message.pk,
        "provider": settings.AI_PROVIDER,
    }
