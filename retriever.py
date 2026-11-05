import chromadb
from config import get_settings
from rag.embedding import embed_query


def get_chroma_client():
    settings = get_settings()
    return chromadb.PersistentClient(path=settings.vector_db_path)


def build_vector_store(embedded_chunks: list[dict]):
    client = get_chroma_client()

    # Always start fresh — delete any data from the previously ingested repo
    # so that stale chunks never bleed into the current analysis session.
    try:
        client.delete_collection("codebase")
    except Exception:
        pass  # collection didn't exist yet — that's fine

    collection = client.create_collection("codebase")

    ids        = [f"{c['file_path']}::{c['chunk_index']}" for c in embedded_chunks]
    embeddings = [c["embedding"] for c in embedded_chunks]
    documents  = [c["content"]   for c in embedded_chunks]
    metadatas  = [
        {
            "file_path":  c["file_path"],
            "language":   c["language"],
            "start_line": c["start_line"],
            "end_line":   c["end_line"],
        }
        for c in embedded_chunks
    ]
    collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
    return collection


def load_vector_store():
    client = get_chroma_client()
    return client.get_or_create_collection("codebase")


def retrieve_relevant_chunks(query: str, k: int = 5) -> list[dict]:
    collection   = load_vector_store()
    query_vector = embed_query(query)
    results      = collection.query(query_embeddings=[query_vector], n_results=k)
    return format_results(results)


def format_results(results: dict) -> list[dict]:
    formatted = []
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    for doc_text, meta in zip(documents, metadatas):
        formatted.append({"content": doc_text, "metadata": meta})

    return formatted
