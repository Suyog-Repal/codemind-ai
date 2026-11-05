"""
Codebase Assistant — Interactive CLI
Run with: .venv/Scripts/python.exe cli.py
"""

import os
import re
import sys
import asyncio
from textwrap import shorten

# ── styling ───────────────────────────────────────────────────────────────────

CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

# ── session state ─────────────────────────────────────────────────────────────
# Tracks the repo path provided at startup (or via re-ingest) so that option 7
# can save generated files directly into that directory without asking again.
_current_repo: str = "."

def banner():
    print(f"""
{CYAN}{BOLD}
  +------------------------------------------+
  |       AI  Codebase  Assistant  CLI       |
  +------------------------------------------+
{RESET}""")

def section(title: str):
    fill = max(4, 42 - len(title))
    print(f"\n{CYAN}{BOLD}-- {title} {'-' * fill}{RESET}")

def ok(msg: str):
    print(f"  {GREEN}[OK]{RESET}  {msg}")

def err(msg: str):
    print(f"  {RED}[ERROR]  {msg}{RESET}")

def info(msg: str):
    print(f"  {DIM}{msg}{RESET}")

def ask(prompt: str) -> str:
    return input(f"\n{YELLOW}> {prompt}{RESET} ").strip()


def _strip_inline_markdown(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"(```?)([^`]*)\1", r"\2", text)
    text = re.sub(r"(\*\*|__|\*|_)(.*?)\1", r"\2", text)
    return text


def _print_table(rows: list[str]) -> None:
    parsed = []
    for row in rows:
        cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
        if cells and not all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            parsed.append([_strip_inline_markdown(cell) for cell in cells])
    if not parsed:
        return

    width = max(len(row) for row in parsed)
    for row in parsed:
        row.extend([""] * (width - len(row)))
    widths = [max(len(row[index]) for row in parsed) for index in range(width)]
    separator = "  " + "-+-".join("-" * size for size in widths)
    print("  " + " | ".join(parsed[0][i].ljust(widths[i]) for i in range(width)))
    print(separator)
    for row in parsed[1:]:
        print("  " + " | ".join(row[i].ljust(widths[i]) for i in range(width)))


def print_ai_text(text: str) -> None:
    """Render common Markdown constructs as readable plain terminal text."""
    lines = text.replace("\r\n", "\n").splitlines()
    index = 0
    table_rows = []
    in_code = False

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            if not in_code:
                print()
            index += 1
            continue
        if in_code:
            print(line)
            index += 1
            continue
        if "|" in line and index + 1 < len(lines) and "|" in lines[index + 1]:
            table_rows = []
            while index < len(lines) and "|" in lines[index]:
                table_rows.append(lines[index])
                index += 1
            _print_table(table_rows)
            print()
            continue
        heading = re.match(r"^\s{0,3}#{1,6}\s+(.*)$", line)
        if heading:
            section(_strip_inline_markdown(heading.group(1)).strip())
            index += 1
            continue
        bullet = re.match(r"^(\s*)[-*+]\s+(.*)$", line)
        numbered = re.match(r"^(\s*)\d+[.)]\s+(.*)$", line)
        if bullet:
            print(f"  {bullet.group(1)}- {_strip_inline_markdown(bullet.group(2))}")
        elif numbered:
            print(f"  {numbered.group(1)}{numbered.group(0).lstrip().split()[0]} "
                  f"{_strip_inline_markdown(numbered.group(2))}")
        else:
            print(_strip_inline_markdown(line))
        index += 1


def print_code_preview(content: str, limit: int = 1000) -> None:
    preview = content[:limit]
    if len(content) > limit:
        preview += "\n..."
    print(preview)


# ── ingest ────────────────────────────────────────────────────────────────────

def ingest_repository(root_path: str):
    global _current_repo
    section("Ingesting Repository")
    from rag.repository_loader import load_repository
    from rag.splitter import split_code
    from rag.embedding import embed_document
    from rag.retriever import build_vector_store

    print(f"  {DIM}Loading files from: {root_path}{RESET}")
    docs = load_repository(root_path)
    if not docs:
        err("No supported files found. Check allowed_extensions in config.py.")
        return False
    ok(f"Loaded {len(docs)} files")

    all_chunks = []
    for doc in docs:
        all_chunks.extend(split_code(doc))
    ok(f"Split into {len(all_chunks)} chunks")

    print(f"  {DIM}Embedding chunks (this may take a moment)...{RESET}")
    try:
        embedded = embed_document(all_chunks)
    except RuntimeError as exc:
        err(str(exc))
        return False
    ok(f"Embedded {len(embedded)} chunks")

    build_vector_store(embedded)
    ok("Vector store ready (ChromaDB)\n")
    _current_repo = root_path   # remember for option 7
    return True

# ── feature handlers ──────────────────────────────────────────────────────────

def feature_query():
    section("Ask a Question  [RAG Query]")
    query = ask("Your question:")
    if not query:
        return
    k_str = ask("Number of source chunks to retrieve? [default: 5]")
    k = max(1, min(int(k_str), 20)) if k_str.isdigit() else 5

    from rag.rag_chain import run_rag_query
    print(f"\n  {DIM}Thinking...{RESET}")
    try:
        result = run_rag_query(query, k=k)
        section("Answer")
        print()
        print_ai_text(result["answer"])
        section("Sources")
        seen = set()
        source_rows = []
        for s in result["sources"]:
            source = (
                s.get("file_path"),
                s.get("start_line"),
                s.get("end_line"),
            )
            if source in seen:
                continue
            seen.add(source)
            source_rows.append([
                str(len(source_rows) + 1),
                str(s.get("file_path", "")),
                f"{s.get('start_line', '?')}-{s.get('end_line', '?')}",
            ])
        if source_rows:
            widths = [max(len(row[i]) for row in source_rows) for i in range(3)]
            print(f"  {'#':>{widths[0]}}  {'File':<{widths[1]}}  Lines")
            print(f"  {'-' * widths[0]}  {'-' * widths[1]}  {'-' * 5}")
            for row in source_rows:
                print(f"  {row[0]:>{widths[0]}}  {row[1]:<{widths[1]}}  {row[2]}")
        else:
            info("No source chunks were returned.")
    except Exception as e:
        err(str(e))


def feature_bugs():
    section("Detect Bugs  [LLM Code Review]")
    file_path = ask("File path to analyse:")
    if not os.path.isfile(file_path):
        err(f"File not found: {file_path}")
        return

    from services.code_analysis import detect_bugs
    print(f"\n  {DIM}Analysing...{RESET}")
    try:
        bugs = detect_bugs(file_path)
        if not bugs:
            ok("No issues found.")
            return
        section(f"Found {len(bugs)} issue(s)")
        for b in bugs:
            sev = b.get("severity", "?").upper()
            color = RED if sev in ("HIGH", "CRITICAL") else YELLOW
            print(f"\n  {color}[{sev}]{RESET}  Line {b.get('line', '?')}: "
                  f"{_strip_inline_markdown(b.get('issue', ''))}")
            print(f"    Suggestion: {_strip_inline_markdown(b.get('suggestion', ''))}")
    except Exception as e:
        err(str(e))


def feature_explain():
    section("Explain a Function")
    file_path = ask("File path:")
    if not os.path.isfile(file_path):
        err(f"File not found: {file_path}")
        return
    func_name = ask("Function name:")
    if not func_name:
        return

    from services.code_analysis import explain_function
    print(f"\n  {DIM}Thinking...{RESET}")
    try:
        explanation = explain_function(file_path, func_name)
        section("Explanation")
        print()
        print_ai_text(explanation)
    except Exception as e:
        err(str(e))


def feature_module_docs():
    section("Generate Module Documentation")
    file_path = ask("Python file path (for example: E:\\project\\module.py):")
    if os.path.isdir(file_path):
        err("Please provide a file path, not a directory.")
        return
    if not os.path.isfile(file_path):
        err(f"File not found: {file_path}")
        return

    from services.documentation import generate_module_docs
    print(f"\n  {DIM}Generating docs...{RESET}")
    try:
        docs = generate_module_docs(file_path)
        section("Documentation")
        print()
        print_ai_text(docs)
    except Exception as e:
        err(str(e))


def feature_readme():
    section("Generate README.md")
    root = ask("Repository root path:")
    if not os.path.isdir(root):
        err(f"Directory not found: {root}")
        return

    from services.documentation import generate_readme
    print(f"\n  {DIM}Generating README...{RESET}")
    try:
        readme = generate_readme(root)
        section("README Preview")
        print()
        print_ai_text(readme[:1500] + ("\n..." if len(readme) > 1500 else ""))
        save = ask("Save to README.md in that directory? [y/N]")
        if save.lower() == "y":
            out = os.path.join(root, "README.md")
            with open(out, "w", encoding="utf-8") as f:
                f.write(readme)
            ok(f"Saved to {out}")
    except Exception as e:
        err(str(e))


def feature_propose_file():
    section("Propose a New File  [AI File Creator]")
    description = ask("Describe the file you want to create:")
    if not description:
        return
    context_query = ask("Optional context query (or press Enter to skip):")

    from services.file_creator import propose_new_file
    print(f"\n  {DIM}Generating...{RESET}")
    try:
        proposal = propose_new_file(description, context_query or None)
        section("Proposed File")
        print(f"\n  Path:  {proposal.path}")
        print(f"\n{DIM}{'-'*50}{RESET}")
        print_code_preview(proposal.content)
        print(f"{DIM}{'-'*50}{RESET}")

        confirm = ask("Write this file to disk? [y/N]")
        if confirm.lower() == "y":
            default_dir = _current_repo
            typed = ask(f"Save under which directory? [default: {default_dir}]").strip()
            base_dir = typed if typed else default_dir
            if not os.path.isdir(base_dir):
                err(f"Directory not found: {base_dir}")
                return
            async def _write():
                from services.file_creator import apply_approved_file
                proposal.approved = True
                return await apply_approved_file(proposal, True, base_dir=base_dir)
            result = asyncio.run(_write())
            if result.get("status") == "written":
                ok(f"File written: {result.get('path', proposal.path)}")
            else:
                err(f"Write failed: {result}")
    except Exception as e:
        err(str(e))


def feature_mcp_tools():
    section("List GitHub MCP Tools")
    async def _list():
        from mcp_client import get_github_mcp_client
        async with get_github_mcp_client() as client:
            return await client.list_tools()
    try:
        tools = asyncio.run(_list())
        ok(f"{len(tools)} tools available:")
        name_width = max((len(t["name"]) for t in tools), default=4)
        for t in tools:
            description = shorten(t.get("description", ""), width=80, placeholder="...")
            print(f"  {t['name']:<{name_width}}  {description}")
    except Exception as e:
        err(str(e))


def feature_reingest():
    root = ask("New repository path to ingest:")
    if os.path.isdir(root):
        ingest_repository(root)
    else:
        err(f"Directory not found: {root}")

# ── menu ──────────────────────────────────────────────────────────────────────

MENU = [
    ("Ask a question about the codebase",    feature_query),
    ("Detect bugs in a file",                feature_bugs),
    ("Explain a function",                   feature_explain),
    ("Generate module documentation",        feature_module_docs),
    ("Generate README for a repository",     feature_readme),
    ("Propose & create a new file (AI)",     feature_propose_file),
    ("List GitHub MCP tools",                feature_mcp_tools),
    ("Re-ingest a repository",               feature_reingest),
]

def show_menu():
    section("What would you like to do?")
    for i, (label, _) in enumerate(MENU, 1):
        print(f"  {CYAN}{i:>2}{RESET}  {label}")
    print(f"  {DIM}  0  Exit{RESET}")

# ── main ──────────────────────────────────────────────────────────────────────

def main():
    # Enable ANSI colours on Windows
    os.system("")

    banner()

    # Step 1 — ask for repo path
    while True:
        root = ask("Enter the path to the repository you want to analyse:")
        if os.path.isdir(root):
            break
        err(f"Directory not found: {root}")

    # Step 2 — ingest
    if not ingest_repository(root):
        sys.exit(1)

    # Step 3 — interactive menu loop
    while True:
        show_menu()
        choice = ask("Choose an option [0-9]:")
        if choice == "0" or choice.lower() in ("exit", "quit", "q"):
            print(f"\n{DIM}Goodbye!{RESET}\n")
            break
        if choice.isdigit() and 1 <= int(choice) <= len(MENU):
            MENU[int(choice) - 1][1]()
        else:
            err("Invalid choice. Enter a number from the menu.")


if __name__ == "__main__":
    main()
