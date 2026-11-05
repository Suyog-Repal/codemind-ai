import os
from llm import get_llm_client, build_prompt
from rag.repository_loader import load_repository


def generate_docstring(function_code: str) -> str:
    prompt = build_prompt(function_code, "", task_type="docstring")
    return get_llm_client().generate(prompt)


def generate_module_docs(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()

    prompt = build_prompt(
        f"Generate documentation for this module: {file_path}",
        code,
        task_type="qa",
    )
    return get_llm_client().generate(prompt)


def summarize_repo_structure(root_path: str) -> dict:
    documents = load_repository(root_path)

    tech_stack = detect_tech_stack(root_path)
    file_tree = build_file_tree(documents)

    return {
        "total_files": len(documents),
        "tech_stack": tech_stack,
        "file_tree": file_tree,
    }


def detect_tech_stack(root_path: str) -> list[str]:
    markers = {
        "requirements.txt": "Python",
        "package.json": "Node.js",
        "go.mod": "Go",
        "pom.xml": "Java (Maven)",
    }
    found = []
    for marker_file, tech_name in markers.items():
        if os.path.exists(os.path.join(root_path, marker_file)):
            found.append(tech_name)
    return found


def build_file_tree(documents: list) -> list[str]:
    return sorted(doc.file_path for doc in documents)


def generate_readme(root_path: str) -> str:
    summary = summarize_repo_structure(root_path)
    prompt = build_prompt(
        f"Generate a README.md for a project with this structure: {summary}",
        "",
        task_type="qa",
    )
    return get_llm_client().generate(prompt)