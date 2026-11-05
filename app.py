from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from api.routes import router
from mcp_client import get_github_mcp_client

logger = logging.getLogger(__name__)

app = FastAPI(title="AI Codebase Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

mcp_client_instance = get_github_mcp_client()


@app.on_event("startup")
async def startup_event():
    try:
        await mcp_client_instance.connect()
    except Exception as exc:
        # GitHub MCP is an optional integration; the REST API remains usable
        # when credentials or the remote service are unavailable.
        logger.warning("GitHub MCP unavailable during startup: %s", exc)


@app.on_event("shutdown")
async def shutdown_event():
    await mcp_client_instance.disconnect()


@app.get("/health")
def health_check():
    return {"status": "ok"}