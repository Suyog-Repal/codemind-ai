# codemind-ai

A Python‑based code analysis and documentation generation toolkit.

---

## Project Overview  
codemind-ai provides tools for extracting embeddings, running LLM queries, and generating documentation for Python repositories. The codebase is organized into modular packages (`api`, `rag`, `services`) and a set of command‑line utilities.

---

## Tech Stack  
- **Python** (≥ 3.9)

---

## Directory Structure  

```
codemind-ai/
│
├── README.md                                 # this file
├── api/
│   ├── __init__.py
│   └── routes.py
│
├── cli.py
├── code_analysis.py
├── config.py
├── documentation.py
├── embedding.py
├── example.py
├── file_creator.py
├── llm.py
├── mcp_client.py
├── rag/
│   ├── __init__.py
│   ├── embedding.py
│   ├── rag_chain.py
│   ├── repository_loader.py
│   ├── retriever.py
│   └── splitter.py
│
├── rag_chain.py
├── repository_loader.py
├── retriever.py
├── routes.py
├── services/
│   ├── __init__.py
│   ├── code_analysis.py
│   ├── documentation.py
│   └── file_creator.py
│
├── splitter.py
├── test_github_mcp.py
└── test_runner.py
```

*File paths are listed under the `E:\\Suyog\\mdm\\codemind-ai\\` root.*

---

## Running the Project  

1. **Install dependencies** (requirements are listed in `requirements.txt`, if present).  
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the API**  
   ```bash
   python app.py
   ```
   The API exposes routes defined in `api/routes.py`.

3. **Run the CLI**  
   ```bash
   python cli.py <command> [options]
   ```
   Commands are defined in `cli.py`.

4. **Execute tests**  
   ```bash
   python test_runner.py
   ```
   Or run individual tests:
   ```bash
   python test_github_mcp.py
   ```

---

## Key Modules  

- **`services/`** – core business logic for code analysis, documentation, and file creation.  
- **`rag/`** – Retrieval-Augmented Generation utilities: embeddings, retrievers, and chain orchestration.  
- **`api/`** – FastAPI routes and application entry point (`app.py`).  
- **`cli.py`** – command‑line interface for quick operations.

---

## Contributing  

1. Fork the repository.  
2. Create a feature branch.  
3. Run tests to ensure nothing breaks.  
4. Submit a pull request.  

---

## License  

This project is released under the MIT License.