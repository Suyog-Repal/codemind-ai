import ast
from llm import get_llm_client, build_prompt
from rag.rag_chain import build_context
from rag.retriever import retrieve_relevant_chunks


def explain_function(file_path: str, function_name: str) -> str:
    function_code = extract_function_source(file_path, function_name)
    related_chunks = retrieve_relevant_chunks(f"usages of {function_name}", k=3)
    context = build_context(related_chunks)

    prompt = build_prompt(function_code, context, task_type="qa")
    return get_llm_client().generate(prompt)


def extract_function_source(file_path: str, function_name: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            return ast.get_source_segment(source, node)

    raise ValueError(f"Function '{function_name}' not found in {file_path}")


def detect_bugs(file_path: str) -> list[dict]:
    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()

    prompt = build_prompt("", code, task_type="bug_finding")
    raw_response = get_llm_client().generate(prompt)

    import json
    try:
        return json.loads(raw_response)
    except json.JSONDecodeError:
        return [{"line": 0, "issue": "Could not parse model output", "severity": "unknown", "suggestion": raw_response}]

