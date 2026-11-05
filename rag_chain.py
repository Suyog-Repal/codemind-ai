from rag.retriever import retrieve_relevant_chunks
from llm import get_llm_client, build_prompt


def build_context(chunks: list[dict]) -> str:
    parts = []
    for c in chunks:
        meta = c["metadata"]
        header = f"# {meta['file_path']} (lines {meta['start_line']}-{meta['end_line']})"
        parts.append(f"{header}\n{c['content']}")
    return "\n\n---\n\n".join(parts)


def run_rag_query(query: str, k: int = 5) -> dict:
    chunks = retrieve_relevant_chunks(query, k)
    context = build_context(chunks)

    prompt = build_prompt(query, context, task_type="qa")
    llm = get_llm_client()
    answer = llm.generate(prompt)

    return {
        "answer": answer,
        "sources": [c["metadata"] for c in chunks],
    }