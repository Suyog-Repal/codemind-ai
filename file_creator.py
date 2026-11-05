from dataclasses import dataclass, asdict
from llm import get_llm_client, build_prompt
from rag.rag_chain import build_context
from rag.retriever import retrieve_relevant_chunks


@dataclass
class FileProposal:
    path: str
    content: str
    reason: str
    approved: bool = False


def propose_new_file(description: str, context_query: str | None = None) -> FileProposal:
    context = ""
    if context_query:
        related_chunks = retrieve_relevant_chunks(context_query, k=5)
        context = build_context(related_chunks)

    prompt = build_prompt(description, context, task_type="file_creation")
    content = get_llm_client().generate(prompt)

    proposed_path = infer_file_path(description)

    return FileProposal(path=proposed_path, content=content, reason=description)


def infer_file_path(description: str) -> str:
    prompt = f"Given this file creation request: '{description}', respond with ONLY a suitable relative file path, nothing else."
    path = get_llm_client().generate(prompt).strip()
    return path


async def apply_approved_file(proposal: FileProposal, user_confirmed: bool, base_dir: str = ".") -> dict:
    """Write the proposed file to local disk under *base_dir*.

    The LLM-suggested path (e.g. /src/geometry/rectangle.js) is treated as
    relative to *base_dir*, so leading slashes/backslashes are stripped before
    joining to avoid accidental absolute-path writes.
    """
    if not user_confirmed:
        return {"status": "rejected", "proposal": asdict(proposal)}

    import os

    # Strip any leading separators so the path is always relative to base_dir
    relative_path = proposal.path.lstrip("/\\")
    abs_path = os.path.join(base_dir, relative_path)

    # Create parent directories if they don't exist
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)

    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(proposal.content)

    proposal.path = abs_path  # update so the caller can display the real path
    return {"status": "written", "path": abs_path}