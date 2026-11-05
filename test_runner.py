"""
Manual test runner for the Codebase Assistant.
Run with: .venv/Scripts/python.exe test_runner.py [test_name]

Available tests:
  mcp        - Test GitHub MCP connection & list tools
  embed      - Test embedding a small text snippet
  ingest     - Index this repo into the local vector store
  query      - Run a RAG query against the vector store
  bugs       - Detect bugs in a given file
  all        - Run embed -> ingest -> query -> bugs (no MCP)
"""

import asyncio
import sys
import os

# ── helpers ──────────────────────────────────────────────────────────────────

def header(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def ok(msg: str):   print(f"  OK  {msg}")
def fail(msg: str): print(f"  FAIL  {msg}")

ROOT = os.path.dirname(__file__)

# ── individual tests ──────────────────────────────────────────────────────────

async def test_mcp():
    """Connect to GitHub MCP and list available tools."""
    header("Test: GitHub MCP Connection")
    from mcp_client import get_github_mcp_client
    client = get_github_mcp_client()
    try:
        await client.connect()
        tools = await client.list_tools()
        ok(f"Connected. {len(tools)} tools found:")
        for t in tools[:5]:
            print(f"       - {t['name']}: {t['description'][:60]}")
        if len(tools) > 5:
            print(f"       ... and {len(tools)-5} more")
    except Exception as e:
        fail(f"MCP connection failed: {e}")
    finally:
        await client.disconnect()


def test_embed():
    """Embed a small text snippet and verify the vector shape."""
    header("Test: Embedding")
    from rag.embedding import embed_query, embed_document
    try:
        vec = embed_query("def hello(): pass")
        assert isinstance(vec, list) and len(vec) > 0, "embed_query returned empty"
        ok(f"embed_query  -> vector of {len(vec)} dims")

        fake_chunks = [{"content": "def add(a, b): return a+b"}]
        chunks = embed_document(fake_chunks)
        assert "embedding" in chunks[0], "embed_document did not add 'embedding' key"
        ok(f"embed_document -> chunk embedding of {len(chunks[0]['embedding'])} dims")
    except Exception as e:
        fail(f"Embedding failed: {e}")


def test_ingest():
    """Load and index this repository into the local ChromaDB."""
    header("Test: Repository Ingest")
    from rag.repository_loader import load_repository
    from rag.splitter import split_code
    from rag.embedding import embed_document
    from rag.retriever import build_vector_store
    try:
        docs = load_repository(ROOT)
        ok(f"Loaded {len(docs)} files from repo")

        all_chunks = []
        for doc in docs:
            all_chunks.extend(split_code(doc))
        ok(f"Split into {len(all_chunks)} chunks")

        embedded = embed_document(all_chunks)
        ok(f"Embedded {len(embedded)} chunks")

        build_vector_store(embedded)
        ok("Vector store built / updated (ChromaDB)")
    except Exception as e:
        fail(f"Ingest failed: {e}")


def test_query():
    """Run a RAG query. Requires the vector store to be populated first."""
    header("Test: RAG Query")
    from rag.rag_chain import run_rag_query
    try:
        result = run_rag_query("How does the embedding module work?", k=3)
        ok(f"Answer received ({len(result['answer'])} chars)")
        ok(f"Sources returned: {len(result['sources'])}")
        for s in result["sources"]:
            print(f"       - {s.get('file_path','?')} lines {s.get('start_line')}-{s.get('end_line')}")
        print(f"\n  Answer preview:\n  {result['answer'][:300]}...")
    except Exception as e:
        fail(f"RAG query failed: {e}")


def test_bugs():
    """Run bug detection on llm.py."""
    header("Test: Bug Detection")
    from services.code_analysis import detect_bugs
    target = os.path.join(ROOT, "llm.py")
    try:
        bugs = detect_bugs(target)
        ok(f"Bug detection returned {len(bugs)} item(s) for llm.py")
        for b in bugs[:3]:
            print(f"       Line {b.get('line','?')}: [{b.get('severity','?')}] {b.get('issue','?')}")
    except Exception as e:
        fail(f"Bug detection failed: {e}")


# ── entry point ───────────────────────────────────────────────────────────────

TESTS = {
    "mcp":        lambda: asyncio.run(test_mcp()),
    "embed":      test_embed,
    "ingest":     test_ingest,
    "query":      test_query,
    "bugs":       test_bugs,
}

def run_all_non_mcp():
    """Run embed -> ingest -> query -> bugs in sequence."""
    test_embed()
    test_ingest()
    test_query()
    test_bugs()

if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    if arg == "all":
        run_all_non_mcp()
    elif arg in TESTS:
        TESTS[arg]()
    else:
        print(f"Unknown test '{arg}'. Choose from: {', '.join(TESTS)} or 'all'")
        sys.exit(1)
