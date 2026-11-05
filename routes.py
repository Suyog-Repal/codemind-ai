from fastapi import APIRouter
from pydantic import BaseModel

from rag_chain import run_rag_query
from code_analysis import detect_bugs, explain_function
from documentation import generate_module_docs, generate_readme
from file_creator import propose_new_file, apply_approved_file, FileProposal

router = APIRouter()


class QueryRequest(BaseModel):
    query: str
    k: int = 5


class ExplainRequest(BaseModel):
    file_path: str
    function_name: str


class FileProposalRequest(BaseModel):
    description: str
    context_query: str | None = None


class FileApprovalRequest(BaseModel):
    proposal: dict
    approved: bool


@router.post("/query")
def query(req: QueryRequest):
    return run_rag_query(req.query, req.k)


@router.post("/analyze/bugs")
def bugs(file_path: str):
    return {"bugs": detect_bugs(file_path)}


@router.post("/analyze/explain")
def explain(req: ExplainRequest):
    return {"explanation": explain_function(req.file_path, req.function_name)}


@router.post("/docs/module")
def module_docs(file_path: str):
    return {"docs": generate_module_docs(file_path)}


@router.post("/docs/readme")
def readme(root_path: str):
    return {"readme": generate_readme(root_path)}


@router.post("/files/propose")
def propose(req: FileProposalRequest):
    proposal = propose_new_file(req.description, req.context_query)
    return proposal


@router.post("/files/approve")
async def approve(req: FileApprovalRequest):
    proposal = FileProposal(**req.proposal)
    return await apply_approved_file(proposal, req.approved)