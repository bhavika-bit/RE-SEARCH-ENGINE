"""
FastAPI backend for ResearchEngine.
Wraps model.py (RAG, ResearchAnalyst, Graph) behind REST endpoints
so the bolt.new / Netlify React frontend can call real logic instead of mocks.
"""

import os
import io
import json
import uuid
from typing import Optional, List

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from langchain_google_genai import ChatGoogleGenerativeAI

from model import (
    RAG,
    ResearchAnalyst,
    Graph,
    save_metadata,
    load_all_projects,
    load_chat_history,
    save_chat_history,
    append_message,
    export_project,
    import_project,
    get_metadata_path,
)

app = FastAPI(title="ResearchEngine API")

# ---- CORS ----
# Allow your Netlify frontend (and localhost for local dev) to call this API.
# Tighten allow_origins to your exact Netlify domain once confirmed working.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: replace with ["https://re-searchengine.netlify.app"] once stable
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== SESSION STORAGE (in-memory, per backend process) ====================
# Each "session" holds the live RAG/agent objects for one active project being worked on.
# Keyed by project_id since the frontend doesn't track a separate session id.

class ProjectSession:
    def __init__(self):
        self.rag: Optional[RAG] = None
        self.agent: Optional[ResearchAnalyst] = None
        self.graph: Optional[Graph] = None
        self.llm = None


SESSIONS: dict[str, ProjectSession] = {}


def get_llm():
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GOOGLE_API_KEY is not set on the server. Add it as an environment variable.",
        )
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.6)


def get_or_create_session(project_id: str) -> ProjectSession:
    if project_id not in SESSIONS:
        SESSIONS[project_id] = ProjectSession()
    return SESSIONS[project_id]


# ==================== SCHEMAS ====================

class CreateProjectRequest(BaseModel):
    topic: str
    problem_statement: str
    timeline: str


class ChatRequest(BaseModel):
    project_id: str
    message: str


class ToolRequest(BaseModel):
    project_id: str


# ==================== PROJECT ENDPOINTS ====================

@app.get("/")
def root():
    return {"status": "ok", "service": "ResearchEngine API"}


@app.get("/projects")
def list_projects():
    return load_all_projects()


@app.post("/projects")
def create_project(req: CreateProjectRequest):
    project_id = str(uuid.uuid4())[:8]
    from datetime import datetime
    metadata = {
        "project_id": project_id,
        "topic": req.topic,
        "problem_statement": req.problem_statement,
        "timeline": req.timeline,
        "created_at": datetime.now().isoformat(),
    }
    save_metadata(project_id, metadata)

    sess = get_or_create_session(project_id)
    sess.rag = RAG()
    loaded = sess.rag.load_vectordb(project_id)
    sess.llm = get_llm()
    sess.agent = ResearchAnalyst(rag_instance=sess.rag, llm_instance=sess.llm)
    sess.agent.set_project(req.topic, req.problem_statement, req.timeline)
    sess.graph = Graph(sess.agent)

    return {"project_id": project_id, "metadata": metadata, "has_index": loaded}


@app.post("/projects/{project_id}/load")
def load_project(project_id: str):
    meta_path = get_metadata_path(project_id)
    if not os.path.exists(meta_path):
        raise HTTPException(status_code=404, detail="Project not found.")
    with open(meta_path) as f:
        metadata = json.load(f)

    sess = get_or_create_session(project_id)
    sess.rag = RAG()
    loaded = sess.rag.load_vectordb(project_id)
    sess.llm = get_llm()
    sess.agent = ResearchAnalyst(rag_instance=sess.rag, llm_instance=sess.llm)
    sess.agent.set_project(
        metadata.get("topic", ""), metadata.get("problem_statement", ""), metadata.get("timeline", "")
    )
    sess.graph = Graph(sess.agent)

    history = load_chat_history(project_id)
    return {"project_id": project_id, "metadata": metadata, "has_index": loaded, "chat_history": history}


@app.post("/projects/{project_id}/documents")
async def upload_documents(project_id: str, files: List[UploadFile] = File(...)):
    sess = SESSIONS.get(project_id)
    if sess is None or sess.agent is None:
        raise HTTPException(status_code=400, detail="Load or create the project before uploading documents.")

    class _FileAdapter:
        def __init__(self, name, content):
            self.name = name
            self._content = content

        def read(self):
            return self._content

    wrapped = []
    for f in files:
        content = await f.read()
        wrapped.append(_FileAdapter(f.filename, content))

    sess.rag = sess.rag or RAG()
    sess.rag.load_data_from_files(wrapped, project_id)

    if not sess.rag.documents:
        return {"status": "no_documents_loaded", "count": 0}

    sess.rag.chunking()
    sess.rag.embedding()
    sess.rag.build_vectordb()
    sess.rag.save_vectordb(project_id)
    sess.agent.rag = sess.rag

    return {"status": "indexed", "count": len(sess.rag.documents)}


@app.get("/projects/{project_id}/export")
def export_project_endpoint(project_id: str):
    data = export_project(project_id)
    return JSONResponse(content=json.loads(data))


@app.post("/projects/import")
async def import_project_endpoint(file: UploadFile = File(...)):
    content = await file.read()
    new_id = import_project(io.StringIO(content.decode("utf-8")))
    meta_path = get_metadata_path(new_id)
    with open(meta_path) as f:
        metadata = json.load(f)

    sess = get_or_create_session(new_id)
    sess.rag = RAG()
    loaded = sess.rag.load_vectordb(new_id)
    sess.llm = get_llm()
    sess.agent = ResearchAnalyst(rag_instance=sess.rag, llm_instance=sess.llm)
    sess.agent.set_project(
        metadata.get("topic", ""), metadata.get("problem_statement", ""), metadata.get("timeline", "")
    )
    sess.graph = Graph(sess.agent)

    return {
        "project_id": new_id,
        "metadata": metadata,
        "has_index": loaded,
        "chat_history": load_chat_history(new_id),
    }


# ==================== CHAT ====================

@app.post("/chat")
def chat(req: ChatRequest):
    sess = SESSIONS.get(req.project_id)
    if sess is None or sess.agent is None:
        raise HTTPException(status_code=400, detail="Load or create the project first.")

    history = load_chat_history(req.project_id)
    answer = sess.agent.chat(req.message, history)

    append_message(req.project_id, "user", req.message)
    append_message(req.project_id, "assistant", answer)

    return {"answer": answer}


@app.post("/chat/clear")
def clear_chat(req: ToolRequest):
    save_chat_history(req.project_id, [])
    return {"status": "cleared"}


@app.get("/chat/{project_id}/history")
def get_chat_history(project_id: str):
    return load_chat_history(project_id)


# ==================== TOOLS ====================

TOOL_NODE_MAP = {
    "roadmap": "roadmap_node",
    "researchgap": "researchgap_node",
    "learning": "learning_node",
    "methodology": "methodology_node",
    "paperintelligence": "paperintelligence_node",
    "researchdiscovery": "researchdiscovery_node",
    "researchmentor": "researchmentor_node",
    "projectsummary": "projectsummary_node",
}


@app.post("/tools/{tool_name}")
def run_tool(tool_name: str, req: ToolRequest):
    if tool_name not in TOOL_NODE_MAP:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {tool_name}")

    sess = SESSIONS.get(req.project_id)
    if sess is None or sess.graph is None:
        raise HTTPException(status_code=400, detail="Load or create the project first.")

    node_fn = getattr(sess.graph, TOOL_NODE_MAP[tool_name])
    state = node_fn({})
    return {"answer": state["answer"]}


# ==================== QUIZ / FLASHCARDS ====================

@app.post("/quiz")
def generate_quiz(req: ToolRequest):
    sess = SESSIONS.get(req.project_id)
    if sess is None or sess.agent is None:
        raise HTTPException(status_code=400, detail="Load or create the project first.")
    return sess.agent.quizgenerator_json()


@app.post("/flashcards")
def generate_flashcards(req: ToolRequest):
    sess = SESSIONS.get(req.project_id)
    if sess is None or sess.agent is None:
        raise HTTPException(status_code=400, detail="Load or create the project first.")
    return sess.agent.flashcards_json()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
