from typing import List
from config import get_settings
import os
from dataclasses import dataclass


@dataclass
class CodeDocument:
    content: str
    file_path: str
    language: str
    size_bytes: int


IGNORE_DIRS = {".git", "node_modules", "__pycache__", "venv", ".venv", "dist", "build"}
LANGUAGE_BY_EXT = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".java": "java",
    ".go": "go",
    ".md": "markdown",
}


def load_repository(root_path: str) -> List[CodeDocument]:
    documents: List[CodeDocument] = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        for filename in filenames:
            fpath = os.path.join(dirpath, filename)
            if should_include(fpath):
                documents.append(read_file_with_metadata(fpath))
    return documents


def should_include(fpath: str) -> bool:
    settings = get_settings()
    _, ext = os.path.splitext(fpath)
    if ext not in settings.allowed_extensions:
        return False
    try:
        size_kb = os.path.getsize(fpath)/1024
    except OSError:
        return False
    return size_kb <= settings.max_file_size_kb


def read_file_with_metadata(filepath: str) -> CodeDocument:
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    return CodeDocument(
        content=content,
        file_path=filepath,
        language=detect_language(filepath),
        size_bytes=len(content.encode("utf-8")),
    )


def detect_language(filepath: str) -> str:
    _, ext = os.path.splitext(filepath)
    return LANGUAGE_BY_EXT.get(ext, "unknown")





"""
import os
from dataclasses import dataclass
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from config import get_settings


@dataclass
class CodeDocument:
    content: str
    file_path: str
    language: str
    size_bytes: int

LANGUAGE_BY_EXT = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".java": "java",
    ".go": "go",
    ".cpp": "cpp",
    ".c": "c",
    ".cs": "csharp",
    ".html": "html",
    ".css": "css",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".md": "markdown",
}
def detect_language(filepath: str) -> str:
    _, ext = os.path.splitext(filepath)
    return LANGUAGE_BY_EXT.get(ext.lower(), "unknown")

def load_repository(root_path: str) -> list[CodeDocument]:
    settings = get_settings()
    loader = DirectoryLoader(
        path=root_path,
        glob="**/*",
        recursive=True,
        silent_errors=True,
        loader_cls=TextLoader,
        loader_kwargs={
            "encoding": "utf-8",
            "autodetect_encoding": True,
        },
        exclude=[
            "**/.git/**",
            "**/.venv/**",
            "**/venv/**",
            "**/__pycache__/**",
            "**/node_modules/**",
            "**/dist/**",
            "**/build/**",
        ],
    )
    documents = loader.load()
    code_documents: list[CodeDocument] = []

    for doc in documents:
        filepath = doc.metadata["source"]
        _, ext = os.path.splitext(filepath)

        if ext.lower() not in settings.allowed_extensions:
            continue

        try:
            size_bytes = os.path.getsize(filepath)
        except OSError:
            continue

        if size_bytes > settings.max_file_size_kb * 1024:
            continue

        code_documents.append(
            CodeDocument(
                content=doc.page_content,
                file_path=filepath,
                language=detect_language(filepath),
                size_bytes=size_bytes,
            )
        )

    return code_documents
"""