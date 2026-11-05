from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from rag.repository_loader import CodeDocument
from config import get_settings


LANGUAGE_MAP = {
    "python": Language.PYTHON,
    "javascript": Language.JS,
    "typescript": Language.TS,
    "java": Language.JAVA,
    "go": Language.GO,
}


def split_code(doc : CodeDocument) -> list[dict]:

    settings = get_settings()
    lang_enum = LANGUAGE_MAP.get(doc.language.lower())

    if lang_enum:
        splitter = RecursiveCharacterTextSplitter.from_language(
            language=lang_enum,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
    else:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )

    raw_chunks = splitter.split_text(doc.content)
    return [
        attach_metadata(chunk, doc, idx)
        for idx, chunk in enumerate(raw_chunks)
    ]


def attach_metadata(chunk_text: str, doc: CodeDocument, index: int) -> dict:
    start_line, end_line = estimate_line_range(doc.content, chunk_text)
    return {
        "content": chunk_text,
        "file_path": doc.file_path,
        "language": doc.language,
        "chunk_index": index,
        "start_line": start_line,
        "end_line": end_line,
    }


def estimate_line_range(full_text: str, chunk_text: str) -> tuple[int, int]:
    offset = full_text.find(chunk_text)
    if offset == -1:
        return (0, 0)
    start_line = full_text[:offset].count("\n") + 1
    end_line = start_line + chunk_text.count("\n")
    return (start_line, end_line)




