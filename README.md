# CodeMind AI

CodeMind AI is a Python command-line and FastAPI assistant for inspecting a
local source repository. It indexes supported source files into a local
ChromaDB vector store, retrieves relevant code for a question, and uses a
configured LLM to generate an answer with source file and line metadata.

The project currently provides a CLI and REST API. It does not include a
frontend.

## Implemented features

| Feature | CLI | API | Notes |
|---|---:|---:|---|
| Repository ingestion | Yes | No | Loads supported files, splits them, embeds them, and replaces the `codebase` ChromaDB collection. |
| RAG questions | Yes | Yes | Retrieves relevant chunks, builds context, calls the configured LLM, and returns source metadata. |
| Bug detection | Yes | Yes | Sends a selected file to the LLM and parses a JSON issue list when possible. |
| Function explanation | Yes | Yes | Extracts a Python function and combines it with retrieved usage context. |
| Module documentation | Yes | Yes | Sends the selected file to the LLM for documentation generation. |
| README generation | Yes | Yes | Summarizes a repository and asks the LLM to generate README content. |
| New-file proposal and approval | Yes | Yes | Generates a proposal and writes it only after confirmation. |
| GitHub MCP tool listing | Yes | No | Optional; requires a GitHub MCP token and reachable MCP service. |
| Health check | No | Yes | `GET /health` returns `{"status": "ok"}`. |

Cyclomatic complexity analysis and a frontend are not part of the current
project.

## RAG pipeline

The RAG flow is implemented as follows:

1. `cli.py` calls `load_repository(root_path)`.
2. `repository_loader.py` includes files with these extensions:
   `.py`, `.js`, `.ts`, `.go`, `.java`, and `.md`.
3. Files in `.git`, `node_modules`, `__pycache__`, `venv`, `.venv`, `dist`, and
   `build` are skipped. Files larger than `MAX_FILE_SIZE_KB` are skipped.
4. `splitter.py` uses `RecursiveCharacterTextSplitter`. Code-aware splitters
   are used for Python, JavaScript, TypeScript, Java, and Go.
5. `embedding.py` uses Gemini embeddings. Document requests are batched with a
   maximum batch size of 100 and retry quota errors according to configuration.
6. `retriever.py` stores embeddings, documents, and metadata in a persistent
   ChromaDB collection named `codebase`.
7. `retrieve_relevant_chunks()` embeds the question and queries ChromaDB for
   the top `k` chunks.
8. `rag_chain.py` builds a context containing file paths and estimated line
   ranges, then calls the configured LLM.
9. The result contains:

   ```json
   {
     "answer": "Generated answer",
     "sources": [
       {
         "file_path": "path/to/file.py",
         "language": "python",
         "start_line": 1,
         "end_line": 20
       }
     ]
   }
   ```

Source line ranges are estimates based on the location of each chunk in the
original file. They are metadata for navigation, not compiler-generated
source maps.

## Architecture

```text
CLI or FastAPI request
          |
          v
Repository loader -> code splitter -> Gemini document embeddings
                                              |
                                              v
                                    Persistent ChromaDB
                                              |
Question -> Gemini query embedding -> similarity retrieval
                                              |
                                              v
                                context + source metadata
                                              |
                                              v
                              Groq or Gemini LLM response
```

The repository contains flat implementation modules plus compatibility
packages restored after the original Hugging Face bucket sync:

```text
CodeMind-AI/
├── app.py                  # FastAPI application and health endpoint
├── cli.py                  # Interactive CLI and terminal formatting
├── config.py               # Environment-backed settings
├── llm.py                  # Gemini and Groq clients and prompts
├── embedding.py            # Gemini embedding client and batching
├── repository_loader.py    # Local repository loading and filtering
├── splitter.py             # Code chunking and line metadata
├── retriever.py            # ChromaDB storage and similarity retrieval
├── rag_chain.py            # RAG orchestration
├── code_analysis.py        # Bug detection and function explanation
├── documentation.py        # Documentation and README generation
├── file_creator.py         # AI file proposal and approved writes
├── mcp_client.py           # Optional GitHub MCP client
├── routes.py               # FastAPI route definitions
├── api/                    # Compatibility package exposing routes
├── rag/                    # Compatibility wrappers for RAG modules
├── services/               # Compatibility wrappers for service modules
├── test_runner.py          # Manual checks
├── test_github_mcp.py      # Standalone MCP check
├── requirements.txt        # Python dependencies
└── vector_db/              # Local ChromaDB data, created at runtime
```

## Technology stack

| Area | Technology |
|---|---|
| Language | Python |
| API | FastAPI, Uvicorn |
| Configuration | Pydantic Settings, python-dotenv |
| LLM providers | Groq and Google Gemini |
| Embeddings | `langchain-google-genai` with Gemini embeddings |
| Chunking | `langchain-text-splitters` |
| Vector database | ChromaDB |
| Code parsing | Python `ast` |
| MCP | MCP streamable HTTP client |

Exact dependency versions are listed in
[requirements.txt](./requirements.txt).

## Setup

### 1. Create and activate a virtual environment

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Git Bash:

```bash
python -m venv .venv
source .venv/Scripts/activate
```

### 2. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

If `python` resolves to a global interpreter, use the virtual-environment
interpreter explicitly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root. Do not commit API keys.

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b

GEMINI_API_KEY=your_gemini_api_key
LLM_MODEL=your_gemini_model_when_using_gemini
EMBEDDING_MODEL=models/gemini-embedding-001

VECTOR_DB_PATH=./vector_db
CHUNK_SIZE=1200
CHUNK_OVERLAP=100
EMBEDDING_BATCH_SIZE=100
EMBEDDING_MAX_RETRIES=2
EMBEDDING_RETRY_DELAY_SECONDS=60

GITHUB_MCP_TOKEN=your_github_mcp_token
GITHUB_MCP_URL=https://api.githubcopilot.com/mcp/
```

Required credentials depend on the operation:

| Variable | Required for |
|---|---|
| `GEMINI_API_KEY` | Repository embeddings and query embeddings |
| `GROQ_API_KEY` | LLM calls when `LLM_PROVIDER=groq` |
| `GEMINI_API_KEY` | LLM calls when `LLM_PROVIDER=gemini` |
| `GITHUB_MCP_TOKEN` | GitHub MCP tool listing |

GitHub MCP is optional for API startup. If its token is missing or the service
is unavailable, the application logs a warning and continues starting.

Gemini free-tier embedding quota can prevent ingestion. The CLI reports this
as an embedding quota error; wait for quota reset or use a project with
available quota.

## CLI usage

Start the CLI with the project virtual environment:

```powershell
.\.venv\Scripts\python.exe cli.py
```

At startup, provide a local repository directory. The CLI does not clone
GitHub URLs automatically:

```text
> Enter the path to the repository you want to analyse: E:\Suyog\mdm\AuthIntegrate
```

The current menu is:

```text
1  Ask a question about the codebase
2  Detect bugs in a file
3  Explain a function
4  Generate module documentation
5  Generate README for a repository
6  Propose and create a new file
7  List GitHub MCP tools
8  Re-ingest a repository
0  Exit
```

The repository is ingested automatically before the menu is displayed.
Re-ingestion replaces the existing `codebase` ChromaDB collection.

## FastAPI usage

Start the API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app:app --reload --port 8000
```

The backend and CLI are independent. The CLI can run without Uvicorn. Run
Uvicorn when using the REST API.

Check startup:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/health -UseBasicParsing
```

Expected response:

```json
{"status":"ok"}
```

Interactive API documentation is available at
`http://127.0.0.1:8000/docs`.

### API endpoints

The application prefixes the routes in `routes.py` with `/api`.

| Method | Endpoint | Input | Result |
|---|---|---|---|
| GET | `/health` | None | Health status |
| POST | `/api/query` | JSON: `query`, optional `k` | RAG answer and sources |
| POST | `/api/analyze/bugs` | Query parameter: `file_path` | Detected issues |
| POST | `/api/analyze/explain` | JSON: `file_path`, `function_name` | Function explanation |
| POST | `/api/docs/module` | Query parameter: `file_path` | Module documentation |
| POST | `/api/docs/readme` | Query parameter: `root_path` | Generated README |
| POST | `/api/files/propose` | JSON: `description`, optional `context_query` | File proposal |
| POST | `/api/files/approve` | JSON: `proposal`, `approved` | Rejected or written file |

Example RAG request:

```bash
curl -X POST http://127.0.0.1:8000/api/query \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"How is the RAG pipeline implemented?\",\"k\":5}"
```

The vector store must be populated before `/api/query` can retrieve useful
context. Use the CLI ingestion flow first.

## Checks and manual tests

Compile the project:

```powershell
.\.venv\Scripts\python.exe -m compileall -q .
```

Run the manual test runner:

```powershell
.\.venv\Scripts\python.exe test_runner.py all
```

Individual checks are available:

```powershell
.\.venv\Scripts\python.exe test_runner.py embed
.\.venv\Scripts\python.exe test_runner.py ingest
.\.venv\Scripts\python.exe test_runner.py query
.\.venv\Scripts\python.exe test_runner.py bugs
.\.venv\Scripts\python.exe test_runner.py mcp
```

The embedding, ingestion, and query checks call external services and require
the corresponding API keys and available quota. The MCP check additionally
requires a valid GitHub MCP configuration.
