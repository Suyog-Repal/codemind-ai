# pyrefly: ignore [missing-import]
import time

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_genai._common import GoogleGenerativeAIError
from config import get_settings


def get_embedding_client() -> GoogleGenerativeAIEmbeddings:
    settings = get_settings()

    return GoogleGenerativeAIEmbeddings(
        model=settings.embedding_model,
        google_api_key=settings.gemini_api_key,
    )


def embed_document(chunks: list[dict]) -> list[dict]:
    if not chunks:
        return chunks

    settings = get_settings()
    embeddings = get_embedding_client()
    texts = [chunk["content"] for chunk in chunks]
    batch_size = min(max(settings.embedding_batch_size, 1), 100)
    vectors: list[list[float]] = []

    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]
        for attempt in range(settings.embedding_max_retries + 1):
            try:
                vectors.extend(
                    embeddings.embed_documents(batch, batch_size=batch_size)
                )
                break
            except GoogleGenerativeAIError as exc:
                message = str(exc)
                quota_error = "429" in message or "RESOURCE_EXHAUSTED" in message
                if not quota_error or attempt >= settings.embedding_max_retries:
                    raise RuntimeError(
                        "Gemini embedding quota is unavailable. "
                        "Wait for the quota reset or use a project with "
                        "available Gemini embedding quota."
                    ) from exc
                time.sleep(settings.embedding_retry_delay_seconds)

    for chunk, vector in zip(chunks, vectors):
        chunk["embedding"] = vector
    return chunks


def embed_query(query: str) -> list[float]:
    embeddings = get_embedding_client()
    return embeddings.embed_query(query)

