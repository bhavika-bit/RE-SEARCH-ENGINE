
import warnings
warnings.filterwarnings("ignore")

import os
import json
import uuid
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

import streamlit as st

from langchain_community.document_loaders import PyMuPDFLoader, TextLoader, CSVLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate


# ─────────────────────────────────────────────
# PERSISTENCE HELPERS
# ─────────────────────────────────────────────
PROJECTS_DIR = "projects"
os.makedirs(PROJECTS_DIR, exist_ok=True)


def get_project_path(project_id):
    return os.path.join(PROJECTS_DIR, project_id)

def get_metadata_path(project_id):
    return os.path.join(get_project_path(project_id), "metadata.json")

def get_chat_path(project_id):
    return os.path.join(get_project_path(project_id), "chat_history.json")

def get_faiss_path(project_id):
    return os.path.join(get_project_path(project_id), "faiss")

def save_metadata(project_id, metadata):
    os.makedirs(get_project_path(project_id), exist_ok=True)
    with open(get_metadata_path(project_id), "w") as f:
        json.dump(metadata, f, indent=2)

def load_all_projects():
    projects = []
    if not os.path.exists(PROJECTS_DIR):
        return projects
    for folder in os.listdir(PROJECTS_DIR):
        path = get_metadata_path(folder)
        if os.path.exists(path):
            with open(path) as f:
                try:
                    projects.append(json.load(f))
                except Exception:
                    pass
    return sorted(projects, key=lambda x: x.get("project_name", ""))

def load_chat_history(project_id):
    chat_file = get_chat_path(project_id)
    if os.path.exists(chat_file):
        with open(chat_file) as f:
            return json.load(f)
    return []

def save_chat_history(project_id, messages):
    with open(get_chat_path(project_id), "w") as f:
        json.dump(messages, f, indent=2)

def append_message(project_id, role, content):
    messages = load_chat_history(project_id)
    messages.append({"role": role, "content": content})
    save_chat_history(project_id, messages)
    return messages

def export_project(project_id):
    metadata = {}
    meta_path = get_metadata_path(project_id)
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            metadata = json.load(f)
    export_data = {
        "metadata": metadata,
        "chat_history": load_chat_history(project_id)
    }
    return json.dumps(export_data, indent=2)

def import_project(uploaded_file):
    data = json.load(uploaded_file)
    metadata = data["metadata"]
    chat_history = data.get("chat_history", [])
    new_project_id = str(uuid.uuid4())[:8]
    metadata["project_id"] = new_project_id
    os.makedirs(get_project_path(new_project_id), exist_ok=True)
    save_metadata(new_project_id, metadata)
    save_chat_history(new_project_id, chat_history)
    return new_project_id


# ─────────────────────────────────────────────
# RAG
# ─────────────────────────────────────────────
class RAG:
    def __init__(self):
        self.documents = None
        self.chunks = None
        self.embeddings = None
        self.vectorstore = None

    def load_data_from_files(self, uploaded_files, project_id):
        self.documents = []
        import tempfile
        for uf in uploaded_files:
            ext = os.path.splitext(uf.name)[1].lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                tmp.write(uf.read())
                tmp_path = tmp.name
            try:
                if ext == ".pdf":
                    loader = PyMuPDFLoader(tmp_path)
                elif ext == ".txt":
                    loader = TextLoader(tmp_path)
                elif ext == ".csv":
                    loader = CSVLoader(tmp_path)
                elif ext == ".docx":
                    loader = Docx2txtLoader(tmp_path)
                else:
                    st.warning(f"Unsupported file: {uf.name}")
                    continue
                docs = loader.load()
                self.documents.extend(docs)
            except Exception as e:
                st.warning(f"Skipped {uf.name}: {e}")
            finally:
                os.unlink(tmp_path)

    def chunking(self):
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        self.chunks = splitter.split_documents(self.documents)

    def embedding(self):
        self.embeddings = get_embeddings()

    def build_vectordb(self):
        self.vectorstore = FAISS.from_documents(self.chunks, self.embeddings)

    def save_vectordb(self, project_id):
        faiss_path = get_faiss_path(project_id)
        os.makedirs(faiss_path, exist_ok=True)
        self.vectorstore.save_local(faiss_path)

    def load_vectordb(self, project_id):
        faiss_path = get_faiss_path(project_id)
        if os.path.exists(faiss_path):
            self.embeddings = get_embeddings()
            self.vectorstore = FAISS.load_local(
                faiss_path, self.embeddings, allow_dangerous_deserialization=True
            )
            return True
        return False


# ─────────────────────────────────────────────
# RESEARCH ANALYST
# ─────────────────────────────────────────────
class ResearchAnalyst:

    def __init__(self, rag_instance, llm_instance):
        self.rag = rag_instance
        self.llm = llm_instance
        self.topic = None
        self.problem_statement = None
        self.timeline = None

    def set_project(self, topic, problem_statement, timeline):
        self.topic = topic
        self.problem_statement = problem_statement
        self.timeline = timeline

    def _get_context(self, k=5):
        if self.rag is None or self.rag.vectorstore is None:
            return "No research context available."
        query = f"Topic: {self.topic}\nProblem Statement: {self.problem_statement}"
        results = self.rag.vectorstore.similarity_search(query, k=k)
        return "\n\n".join([doc.page_content for doc in results])

    def roadmap_generation(self):
        context = self._get_context()
        prompt = f"""You are an expert research mentor.
Topic: {self.topic}
Problem Statement: {self.problem_statement}
Timeline: {self.timeline}
Relevant Research Context: {context}

Generate:
1. Week-wise roadmap
2. Suggested methodologies
3. Datasets
4. Learning resources
5. Project pre-requisites
6. Milestones
7. Risks and challenges
8. Expected final deliverables
9. Feasibility of project in the timeline

Be detailed and practical."""
        return self.llm.invoke(prompt).content

    def researchgap(self):
        context = self._get_context()
        prompt = f"""You are an expert research mentor.
Topic: {self.topic}
Problem Statement: {self.problem_statement}
Relevant Research Context: {context}

Generate:
1. Research gaps
2. Methodology drawbacks
3. Missing datasets
4. Learning resources
5. Weaknesses in existing work
6. Risks and challenges
7. Literature review

Be detailed and practical."""
        return self.llm.invoke(prompt).content

    def learning(self):
        context = self._get_context()
        prompt = f"""You are an expert research mentor.
Topic: {self.topic}
Problem Statement: {self.problem_statement}
Relevant Research Context: {context}

Generate:
1. Core concepts
2. Guided learning skeleton
3. Learning sources
4. Applications of the concept
5. Suggestions to study
6. Generate learning resources (ArXiv, GitHub, HuggingFace, Kaggle — only if confident they exist).

Be detailed and practical."""
        return self.llm.invoke(prompt).content

    def quizgenerator(self):
        context = self._get_context()
        prompt = f"""You are an expert research mentor.
Topic: {self.topic}
Problem Statement: {self.problem_statement}
Relevant Research Context: {context}

Generate:
1. MCQ quizzes — don't reveal answers before user responds
2. Flashcards with keywords and definitions
3. Presentation points
4. Topics to focus on based on quiz answers

Be detailed and practical."""
        return self.llm.invoke(prompt).content

    def methodology(self):
        context = self._get_context()
        prompt = f"""You are an expert research mentor.
Topic: {self.topic}
Problem Statement: {self.problem_statement}
Timeline: {self.timeline}
Relevant Research Context: {context}

Generate:
1. Current research solutions
2. Novelty idea generator
3. Tech stack
4. Proposed solution
5. Proposed workflow

Be detailed and practical."""
        return self.llm.invoke(prompt).content

    def paperintelligence(self):
        context = self._get_context()
        prompt = f"""You are an expert research mentor.
Topic: {self.topic}
Problem Statement: {self.problem_statement}
Relevant Research Context: {context}

Generate:
1. Research objective
2. Paper summary
3. Methodology used
4. Datasets used
5. Results obtained
6. Key findings
7. Limitations
8. Future work
9. Important concepts explained

Be detailed and practical."""
        return self.llm.invoke(prompt).content

    def researchdiscovery(self):
        context = self._get_context()
        prompt = f"""You are an expert research mentor.
Topic: {self.topic}
Problem Statement: {self.problem_statement}
Relevant Research Context: {context}

Generate:
1. Recommended research papers
2. Recommended datasets
3. Emerging trends
4. Current state of research
5. Important authors and researchers
6. Conferences and journals to follow
7. Useful resources and repositories (ArXiv, GitHub, HuggingFace, Kaggle — only if confident)
8. Future directions

Be detailed and practical."""
        return self.llm.invoke(prompt).content

    def researchmentor(self):
        context = self._get_context()
        prompt = f"""You are an expert research mentor and thesis supervisor.
Topic: {self.topic}
Problem Statement: {self.problem_statement}
Relevant Research Context: {context}

Generate:
1. Feedback on current direction
2. Progress evaluation
3. Strengths of the project
4. Weaknesses of the project
5. Suggested next steps
6. Potential challenges
7. Questions a reviewer may ask
8. Suggestions for improvement
9. Advice for successful completion

Be detailed and practical."""
        return self.llm.invoke(prompt).content

    def projectsummary(self):
        context = self._get_context()
        prompt = f"""You are an expert research mentor.
Topic: {self.topic}
Problem Statement: {self.problem_statement}
Relevant Research Context: {context}

Generate:
1. Project summary
2. Project scope
3. Idea feasibility
4. Key resources (ArXiv, GitHub, HuggingFace, Kaggle — only if confident)

Be detailed and practical."""
        return self.llm.invoke(prompt).content

    def chat(self, user_message, history):
        context = self._get_context()
        history_text = ""
        for msg in history[-10:]:
            role = "User" if msg["role"] == "user" else "Assistant"
            history_text += f"{role}: {msg['content']}\n"
        prompt = f"""You are an expert research mentor and assistant.
Project Topic: {self.topic}
Problem Statement: {self.problem_statement}
Timeline: {self.timeline}
Relevant Research Context: {context}

Conversation History:
{history_text}

User: {user_message}

Respond as a knowledgeable, helpful research mentor. Be concise yet thorough."""
        return self.llm.invoke(prompt).content


# ─────────────────────────────────────────────
# GRAPH
# ─────────────────────────────────────────────
class Graph:
    def __init__(self, agent):
        self.agent = agent

    def roadmap_node(self, state):
        state["answer"] = self.agent.roadmap_generation(); return state
    def researchgap_node(self, state):
        state["answer"] = self.agent.researchgap(); return state
    def learning_node(self, state):
        state["answer"] = self.agent.learning(); return state
    def quizgenerator_node(self, state):
        state["answer"] = self.agent.quizgenerator(); return state
    def methodology_node(self, state):
        state["answer"] = self.agent.methodology(); return state
    def paperintelligence_node(self, state):
        state["answer"] = self.agent.paperintelligence(); return state
    def researchdiscovery_node(self, state):
        state["answer"] = self.agent.researchdiscovery(); return state
    def researchmentor_node(self, state):
        state["answer"] = self.agent.researchmentor(); return state
    def projectsummary_node(self, state):
        state["answer"] = self.agent.projectsummary(); return state


# ─────────────────────────────────────────────
# CACHED RESOURCES
# ─────────────────────────────────────────────
@st.cache_resource
def get_llm():
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.6)

@st.cache_resource
def get_embeddings():
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

@st.cache_resource
def load_cached_faiss(project_id):
    rag = RAG()
    rag.load_vectordb(project_id)
    return rag


# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="ResearchEngine",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────────
# GLOBAL CSS  — 3-panel layout
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=Space+Mono:wght@400;700&display=swap');

/* ══════════════════════════════════════════════
   CSS VARIABLES — LIGHT MODE (pastels + bright borders)
══════════════════════════════════════════════ */
:root {
  --bg-primary:     #f7f3ff;
  --bg-secondary:   #eef2ff;
  --bg-tertiary:    #f0fdf4;
  --bg-panel:       #ffffff;
  --bg-chat-user:   #ede9fe;
  --bg-chat-ai:     #fef3c7;

  --border-main:    #a78bfa;
  --border-accent:  #34d399;
  --border-soft:    #c4b5fd;

  --text-primary:   #1e1b4b;
  --text-secondary: #4c1d95;
  --text-muted:     #7c3aed;
  --text-label:     #059669;

  --btn-primary:    linear-gradient(135deg, #a78bfa, #60a5fa);
  --btn-secondary:  linear-gradient(135deg, #6ee7b7, #34d399);
  --btn-action:     linear-gradient(135deg, #fde68a, #fb923c);
  --btn-text:       #1e1b4b;

  --tag-bg:         #ddd6fe;
  --tag-text:       #4c1d95;

  --shadow-soft:    0 2px 12px rgba(167,139,250,0.18);
  --shadow-panel:   0 4px 24px rgba(167,139,250,0.12);

  --font-main:      'DM Sans', sans-serif;
  --font-mono:      'Space Mono', monospace;

  --radius-sm:      6px;
  --radius-md:      12px;
  --radius-lg:      18px;
}

/* ══════════════════════════════════════════════
   DARK MODE — neon on deep backgrounds
══════════════════════════════════════════════ */
@media (prefers-color-scheme: dark) {
  :root {
    --bg-primary:     #0a0a14;
    --bg-secondary:   #0f0f1f;
    --bg-tertiary:    #0a1a0f;
    --bg-panel:       #111122;
    --bg-chat-user:   #1a0a2e;
    --bg-chat-ai:     #0a1a2e;

    --border-main:    #9d4edd;
    --border-accent:  #00ff88;
    --border-soft:    #7209b7;

    --text-primary:   #e0e0ff;
    --text-secondary: #c77dff;
    --text-muted:     #9d4edd;
    --text-label:     #00ff88;

    --btn-primary:    linear-gradient(135deg, #7209b7, #3a0ca3);
    --btn-secondary:  linear-gradient(135deg, #00ff88, #0077b6);
    --btn-action:     linear-gradient(135deg, #f72585, #7209b7);
    --btn-text:       #ffffff;

    --tag-bg:         #1a0a2e;
    --tag-text:       #c77dff;

    --shadow-soft:    0 2px 12px rgba(157,78,221,0.35);
    --shadow-panel:   0 4px 24px rgba(157,78,221,0.25);
  }
}

/* ══════════════════════════════════════════════
   RESET & BASE
══════════════════════════════════════════════ */
* { box-sizing: border-box; margin: 0; padding: 0; }

html, body, .stApp {
  background: var(--bg-primary) !important;
  font-family: var(--font-main) !important;
  color: var(--text-primary) !important;
  height: 100%;
}

/* hide Streamlit chrome */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"]  { display: none !important; }

[data-testid="stSidebar"]       { display: none !important; }

/* full-bleed block container */
[data-testid="stAppViewContainer"] > .main > .block-container {
  padding: 0 !important;
  max-width: 100% !important;
}

/* ══════════════════════════════════════════════
   3-PANEL SHELL
══════════════════════════════════════════════ */
.re-shell {
  display: grid;
  grid-template-columns: 240px 1fr 220px;
  grid-template-rows: 100vh;
  height: 100vh;
  overflow: hidden;
  background: var(--bg-primary);
}

/* ── LEFT PANEL ── */
.re-left {
  grid-column: 1;
  background: var(--bg-panel);
  border-right: 2px solid var(--border-main);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: var(--shadow-panel);
}

.re-left-header {
  padding: 18px 16px 12px;
  border-bottom: 1.5px solid var(--border-soft);
  flex-shrink: 0;
}

.re-logo {
  font-family: var(--font-mono);
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-secondary);
  letter-spacing: 0.04em;
  margin-bottom: 10px;
}

.re-left-actions {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px 16px;
  border-bottom: 1.5px solid var(--border-soft);
  flex-shrink: 0;
}

.re-left-projects-label {
  font-size: 0.65rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--text-muted);
  padding: 10px 16px 4px;
  flex-shrink: 0;
}

.re-project-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 4px 10px 12px;
}

.re-project-scroll::-webkit-scrollbar { width: 3px; }
.re-project-scroll::-webkit-scrollbar-track { background: transparent; }
.re-project-scroll::-webkit-scrollbar-thumb { background: var(--border-soft); border-radius: 4px; }

.re-proj-item {
  padding: 8px 10px;
  border-radius: var(--radius-sm);
  border-left: 3px solid transparent;
  font-size: 0.78rem;
  color: var(--text-primary);
  cursor: pointer;
  margin-bottom: 3px;
  transition: all 0.15s ease;
  line-height: 1.3;
}
.re-proj-item:hover {
  background: var(--bg-secondary);
  border-left-color: var(--border-main);
}
.re-proj-item.active {
  background: var(--bg-secondary);
  border-left-color: var(--border-accent);
  color: var(--text-secondary);
  font-weight: 600;
}
.re-proj-name { font-weight: 500; }
.re-proj-sub  { font-size: 0.65rem; color: var(--text-muted); margin-top: 1px; }

/* ── MIDDLE PANEL ── */
.re-middle {
  grid-column: 2;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg-primary);
}

.re-middle-header {
  padding: 16px 24px 12px;
  background: var(--bg-panel);
  border-bottom: 2px solid var(--border-main);
  flex-shrink: 0;
  box-shadow: var(--shadow-soft);
}

.re-project-title {
  font-family: var(--font-mono);
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.re-meta-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
}

.re-tag {
  background: var(--tag-bg);
  color: var(--tag-text);
  font-size: 0.68rem;
  font-weight: 600;
  padding: 3px 9px;
  border-radius: 999px;
  letter-spacing: 0.04em;
  border: 1px solid var(--border-soft);
  white-space: nowrap;
}

.re-chat-area {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.re-chat-area::-webkit-scrollbar { width: 4px; }
.re-chat-area::-webkit-scrollbar-track { background: transparent; }
.re-chat-area::-webkit-scrollbar-thumb { background: var(--border-soft); border-radius: 4px; }

.re-msg {
  max-width: 82%;
  padding: 12px 16px;
  border-radius: var(--radius-md);
  font-size: 0.84rem;
  line-height: 1.6;
  position: relative;
}
.re-msg-user {
  background: var(--bg-chat-user);
  border: 1.5px solid var(--border-main);
  align-self: flex-end;
  border-bottom-right-radius: 4px;
}
.re-msg-ai {
  background: var(--bg-chat-ai);
  border: 1.5px solid var(--border-accent);
  align-self: flex-start;
  border-bottom-left-radius: 4px;
}
.re-msg-role {
  font-size: 0.62rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: 5px;
  color: var(--text-muted);
}
.re-msg-content {
  color: var(--text-primary);
  white-space: pre-wrap;
}

.re-chat-input-wrap {
  padding: 14px 24px 16px;
  background: var(--bg-panel);
  border-top: 2px solid var(--border-main);
  flex-shrink: 0;
}

/* ── RIGHT PANEL ── */
.re-right {
  grid-column: 3;
  background: var(--bg-panel);
  border-left: 2px solid var(--border-main);
  overflow-y: auto;
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  box-shadow: var(--shadow-panel);
}

.re-right::-webkit-scrollbar { width: 3px; }
.re-right::-webkit-scrollbar-track { background: transparent; }
.re-right::-webkit-scrollbar-thumb { background: var(--border-soft); border-radius: 4px; }

.re-right-label {
  font-size: 0.62rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--text-muted);
  margin-bottom: 4px;
  margin-top: 8px;
  padding-left: 2px;
}
.re-right-label:first-child { margin-top: 0; }

/* ══════════════════════════════════════════════
   BUTTONS — Streamlit overrides
══════════════════════════════════════════════ */
.stButton > button {
  font-family: var(--font-main) !important;
  font-size: 0.78rem !important;
  font-weight: 600 !important;
  border-radius: var(--radius-sm) !important;
  border: none !important;
  cursor: pointer !important;
  transition: all 0.15s ease !important;
  width: 100% !important;
  text-align: left !important;
  padding: 7px 12px !important;
  line-height: 1.3 !important;
}

/* New project / primary */
div[data-testid="stButton"]:has(button[kind="primary"]) > button {
  background: var(--btn-primary) !important;
  color: var(--btn-text) !important;
  border: 1.5px solid var(--border-main) !important;
  box-shadow: var(--shadow-soft) !important;
  text-align: center !important;
}
div[data-testid="stButton"]:has(button[kind="primary"]) > button:hover {
  filter: brightness(1.1) !important;
  box-shadow: 0 4px 16px rgba(167,139,250,0.4) !important;
  transform: translateY(-1px) !important;
}

/* Secondary / export / import */
div[data-testid="stButton"]:has(button[kind="secondary"]) > button {
  background: var(--bg-secondary) !important;
  color: var(--text-primary) !important;
  border: 1.5px solid var(--border-soft) !important;
  text-align: center !important;
}
div[data-testid="stButton"]:has(button[kind="secondary"]) > button:hover {
  border-color: var(--border-main) !important;
  background: var(--tag-bg) !important;
}

/* Quick action buttons — all other buttons */
div[data-testid="stButton"]:not(:has(button[kind="primary"])):not(:has(button[kind="secondary"])) > button {
  background: var(--bg-secondary) !important;
  color: var(--text-primary) !important;
  border: 1.5px solid var(--border-soft) !important;
  text-align: left !important;
  padding: 8px 10px !important;
  font-size: 0.76rem !important;
}
div[data-testid="stButton"]:not(:has(button[kind="primary"])):not(:has(button[kind="secondary"])) > button:hover {
  border-color: var(--border-accent) !important;
  background: var(--tag-bg) !important;
  color: var(--text-secondary) !important;
}

/* Chat input */
.stChatInput > div {
  border: 2px solid var(--border-main) !important;
  border-radius: var(--radius-md) !important;
  background: var(--bg-secondary) !important;
  font-family: var(--font-main) !important;
  font-size: 0.85rem !important;
}
.stChatInput textarea {
  color: var(--text-primary) !important;
  font-family: var(--font-main) !important;
}

/* st.chat_message bubbles */
[data-testid="stChatMessage"] {
  background: transparent !important;
  padding: 0 !important;
}

/* st.spinner */
.stSpinner > div { border-top-color: var(--border-main) !important; }

/* st.success / st.error */
.stAlert { border-radius: var(--radius-md) !important; font-size: 0.8rem !important; }

/* file uploader */
[data-testid="stFileUploader"] {
  border: 1.5px dashed var(--border-soft) !important;
  border-radius: var(--radius-md) !important;
  padding: 8px !important;
  font-size: 0.76rem !important;
}

/* st.form */
[data-testid="stForm"] {
  border: 2px solid var(--border-main) !important;
  border-radius: var(--radius-lg) !important;
  padding: 20px !important;
  background: var(--bg-panel) !important;
  box-shadow: var(--shadow-panel) !important;
}
[data-testid="stForm"] label {
  font-size: 0.78rem !important;
  font-weight: 600 !important;
  color: var(--text-secondary) !important;
  letter-spacing: 0.03em !important;
}
[data-testid="stForm"] input,
[data-testid="stForm"] textarea {
  font-family: var(--font-main) !important;
  font-size: 0.82rem !important;
  border: 1.5px solid var(--border-soft) !important;
  border-radius: var(--radius-sm) !important;
  background: var(--bg-secondary) !important;
  color: var(--text-primary) !important;
}
[data-testid="stForm"] input:focus,
[data-testid="stForm"] textarea:focus {
  border-color: var(--border-main) !important;
  outline: none !important;
  box-shadow: 0 0 0 3px rgba(167,139,250,0.15) !important;
}

/* download button */
[data-testid="stDownloadButton"] > button {
  background: var(--btn-secondary) !important;
  color: var(--btn-text) !important;
  border: 1.5px solid var(--border-accent) !important;
  font-size: 0.76rem !important;
  font-weight: 600 !important;
  border-radius: var(--radius-sm) !important;
  width: 100% !important;
  padding: 7px 12px !important;
}
[data-testid="stDownloadButton"] > button:hover {
  filter: brightness(1.08) !important;
}

/* Empty landing */
.re-landing {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 14px;
  padding: 40px;
}
.re-landing h1 {
  font-family: var(--font-mono);
  font-size: 2rem;
  color: var(--text-secondary);
  text-align: center;
}
.re-landing p {
  font-size: 0.9rem;
  color: var(--text-muted);
  text-align: center;
  max-width: 360px;
  line-height: 1.6;
}

/* section divider */
.re-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--border-soft), transparent);
  margin: 4px 0;
}

/* scrollable wrapper used in middle column */
.re-scroll-middle {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
}
.re-scroll-middle::-webkit-scrollbar { width: 4px; }
.re-scroll-middle::-webkit-scrollbar-thumb { background: var(--border-soft); border-radius: 4px; }

/* form container inside middle scroll */
.re-form-wrap {
  max-width: 560px;
  margin: 0 auto;
}
.re-form-wrap h2 {
  font-family: var(--font-mono);
  font-size: 1.1rem;
  color: var(--text-secondary);
  margin-bottom: 16px;
  text-align: center;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
if "active_project_id" not in st.session_state:
    st.session_state.active_project_id = None
if "agent" not in st.session_state:
    st.session_state.agent = None
if "graph" not in st.session_state:
    st.session_state.graph = None
if "show_new_project_form" not in st.session_state:
    st.session_state.show_new_project_form = False
if "active_meta" not in st.session_state:
    st.session_state.active_meta = None


def load_project(project_id):
    meta_path = get_metadata_path(project_id)
    if not os.path.exists(meta_path):
        st.error("Project not found.")
        return
    with open(meta_path) as f:
        meta = json.load(f)
    faiss_path = get_faiss_path(project_id)
    rag = load_cached_faiss(project_id) if os.path.exists(faiss_path) else None
    llm = get_llm()
    agent = ResearchAnalyst(rag_instance=rag, llm_instance=llm)
    agent.set_project(
        topic=meta["topic"],
        problem_statement=meta["problem_statement"],
        timeline=meta["timeline"]
    )
    st.session_state.active_project_id = project_id
    st.session_state.agent = agent
    st.session_state.graph = Graph(agent)
    st.session_state.active_meta = meta


# ─────────────────────────────────────────────
# 3-PANEL LAYOUT
# left_col | middle_col | right_col
# ─────────────────────────────────────────────
left_col, middle_col, right_col = st.columns([2, 5.5, 2], gap="small")

# ══════════════════════════════════════════════
# LEFT PANEL
# ══════════════════════════════════════════════
with left_col:
    st.markdown("""
    <div class="re-left-header">
      <div class="re-logo">🔬 ResearchEngine</div>
    </div>
    """, unsafe_allow_html=True)

    # ── New project button
    if st.button("＋ New Project", key="btn_new", type="primary", use_container_width=True):
        st.session_state.show_new_project_form = True
        st.session_state.active_project_id = None
        st.rerun()

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # ── Export / Import
    pid_active = st.session_state.active_project_id
    if pid_active and st.session_state.active_meta:
        export_data = export_project(pid_active)
        st.download_button(
            label="📤 Export Project",
            data=export_data,
            file_name=f"{st.session_state.active_meta.get('project_name','project')}.json",
            mime="application/json",
            use_container_width=True,
            key="btn_export"
        )

    uploaded_project_file = st.file_uploader(
        "📥 Import Project",
        type=["json"],
        key="import_uploader",
        label_visibility="collapsed"
    )
    if st.button("📥 Import Project", key="btn_import_label", type="secondary", use_container_width=True):
        pass  # trigger shows above uploader

    if uploaded_project_file is not None:
        try:
            imported_id = import_project(uploaded_project_file)
            st.success("Imported ✓")
            load_project(imported_id)
            st.rerun()
        except Exception as e:
            st.error(f"Import failed: {e}")

    st.markdown("<div class='re-divider'></div>", unsafe_allow_html=True)
    st.markdown("<div class='re-left-projects-label'>📁 My Projects</div>", unsafe_allow_html=True)

    # ── Project list (scrollable via st native overflow)
    all_projects = load_all_projects()
    if not all_projects:
        st.markdown(
            "<p style='font-size:0.72rem;color:var(--text-muted);padding:8px 10px;'>"
            "No projects yet.</p>",
            unsafe_allow_html=True
        )
    else:
        for proj in all_projects:
            pid = proj["project_id"]
            label = proj.get("project_name", "Untitled")
            timeline = proj.get("timeline", "")
            is_active = (pid == st.session_state.active_project_id)
            prefix = "▶ " if is_active else "   "
            btn_label = f"{prefix}{label}"
            if st.button(btn_label, key=f"proj_{pid}", use_container_width=True):
                st.session_state.show_new_project_form = False
                load_project(pid)
                st.rerun()


# ══════════════════════════════════════════════
# MIDDLE PANEL
# ══════════════════════════════════════════════
with middle_col:

    # ── NEW PROJECT FORM ──
    if st.session_state.show_new_project_form:
        st.markdown(
            "<div style='padding:24px 8px 0;'><h2 style='font-family:var(--font-mono,monospace);"
            "font-size:1.1rem;color:var(--text-secondary,#4c1d95);margin-bottom:16px;"
            "text-align:center;'>✨ Create New Project</h2></div>",
            unsafe_allow_html=True
        )

        with st.form("new_project_form"):
            project_name = st.text_input("Project Name 🏷️", placeholder="e.g. Crime Hotspot Analysis")
            topic        = st.text_input("Research Topic 🔍", placeholder="e.g. Urban Crime Prediction using ML")
            problem_stmt = st.text_area("Problem Statement 📝", placeholder="Describe what you're solving...", height=100)
            timeline     = st.text_input("Timeline ⏱️", placeholder="e.g. 8 weeks")
            uploaded_files = st.file_uploader(
                "📎 Upload Research Documents (optional)",
                type=["pdf", "txt", "csv", "docx"],
                accept_multiple_files=True
            )
            submitted = st.form_submit_button("🚀 Create Project", type="primary", use_container_width=True)

        if submitted:
            if not project_name or not topic or not problem_stmt:
                st.error("Please fill in Project Name, Topic, and Problem Statement.")
            else:
                project_id = str(uuid.uuid4())[:8]
                os.makedirs(get_project_path(project_id), exist_ok=True)
                rag = None
                if uploaded_files:
                    with st.spinner("🔄 Processing documents..."):
                        rag = RAG()
                        rag.load_data_from_files(uploaded_files, project_id)
                        rag.chunking()
                        rag.embedding()
                        rag.build_vectordb()
                        rag.save_vectordb(project_id)
                    st.success(f"✅ Loaded {len(rag.documents)} document pages.")

                created_at = datetime.now().strftime("%d %b %Y, %H:%M")
                metadata = {
                    "project_id":       project_id,
                    "project_name":     project_name,
                    "topic":            topic,
                    "problem_statement": problem_stmt,
                    "timeline":         timeline,
                    "has_docs":         rag is not None,
                    "created_at":       created_at,
                }
                save_metadata(project_id, metadata)

                llm   = get_llm()
                agent = ResearchAnalyst(rag_instance=rag, llm_instance=llm)
                agent.set_project(topic=topic, problem_statement=problem_stmt, timeline=timeline)

                st.session_state.active_project_id = project_id
                st.session_state.agent = agent
                st.session_state.graph = Graph(agent)
                st.session_state.active_meta = metadata
                st.session_state.show_new_project_form = False

                with st.spinner("🧠 Generating project summary..."):
                    summary = agent.projectsummary()
                append_message(project_id, "assistant", f"**📋 Project Summary**\n\n{summary}")
                st.success("🎉 Project created!")
                st.rerun()

    # ── ACTIVE PROJECT ──
    elif st.session_state.active_project_id and st.session_state.agent:
        pid   = st.session_state.active_project_id
        meta  = st.session_state.active_meta or {}
        agent = st.session_state.agent

        # Header
        proj_title   = meta.get("project_name", "Untitled Project")
        proj_timeline = meta.get("timeline", "—")
        proj_created  = meta.get("created_at", "—")
        proj_docs     = "📎 Docs attached" if meta.get("has_docs") else "📄 No docs"
        proj_topic    = meta.get("topic", "")

        st.markdown(f"""
        <div style="padding: 16px 8px 8px;">
          <div style="
            font-family: var(--font-mono, monospace);
            font-size: 1.05rem;
            font-weight: 700;
            color: var(--text-secondary, #4c1d95);
            margin-bottom: 8px;
            line-height: 1.3;
          ">🔬 {proj_title}</div>
          <div style="display:flex;flex-wrap:wrap;gap:7px;align-items:center;">
            <span class="re-tag">🕐 {proj_timeline}</span>
            <span class="re-tag">📅 {proj_created}</span>
            <span class="re-tag">{proj_docs}</span>
            {f'<span class="re-tag" style="max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="{proj_topic}">🔍 {proj_topic[:38]}{"…" if len(proj_topic)>38 else ""}</span>' if proj_topic else ""}
          </div>
        </div>
        <hr style="border:none;border-top:1.5px solid var(--border-soft,#c4b5fd);margin:4px 8px 0;" />
        """, unsafe_allow_html=True)

        # Chat history (scrollable naturally in Streamlit)
        messages = load_chat_history(pid)
        chat_container = st.container()
        with chat_container:
            for msg in messages:
                role = msg["role"]
                content = msg["content"]
                if role == "user":
                    with st.chat_message("user"):
                        st.markdown(
                            f"<div style='font-size:0.84rem;line-height:1.6;'>{content}</div>",
                            unsafe_allow_html=True
                        )
                else:
                    with st.chat_message("assistant"):
                        st.markdown(
                            f"<div style='font-size:0.84rem;line-height:1.6;'>{content}</div>",
                            unsafe_allow_html=True
                        )

        # Chat input
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        prompt_input = st.chat_input("💬 Ask your research mentor anything...")
        if prompt_input:
            with st.chat_message("user"):
                st.markdown(
                    f"<div style='font-size:0.84rem;'>{prompt_input}</div>",
                    unsafe_allow_html=True
                )
            messages = append_message(pid, "user", prompt_input)
            with st.chat_message("assistant"):
                with st.spinner("🤔 Thinking..."):
                    response = agent.chat(prompt_input, messages)
                st.markdown(
                    f"<div style='font-size:0.84rem;line-height:1.6;'>{response}</div>",
                    unsafe_allow_html=True
                )
            append_message(pid, "assistant", response)
            st.rerun()

    # ── LANDING ──
    else:
        st.markdown("""
        <div class="re-landing">
          <div style="font-size:3rem;">🔬</div>
          <h1>ResearchEngine</h1>
          <p>Your AI-powered research mentor.<br>
             Create a new project from the left panel to get started.</p>
          <p style="font-size:0.75rem;opacity:0.55;">
            Powered by Gemini · FAISS · HuggingFace
          </p>
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════
# RIGHT PANEL — Quick Actions (always visible)
# ══════════════════════════════════════════════
with right_col:
    st.markdown(
        "<div style='font-size:0.62rem;font-weight:700;text-transform:uppercase;"
        "letter-spacing:0.12em;color:var(--text-muted,#7c3aed);margin-bottom:8px;"
        "padding-top:16px;'>⚡ Quick Actions</div>",
        unsafe_allow_html=True
    )

    pid_r  = st.session_state.active_project_id
    agent_r = st.session_state.agent
    graph_r = st.session_state.graph

    features = [
        ("📅 Roadmap",        "roadmap"),
        ("🔍 Research Gap",   "gap"),
        ("📚 Learning Path",  "learning"),
        ("🧠 Methodology",    "methodology"),
        ("📄 Paper Intel",    "paper"),
        ("🌐 Discovery",      "discovery"),
        ("🎓 Mentor Review",  "mentor"),
        ("❓ Quiz Me",        "quiz"),
    ]

    if pid_r and agent_r and graph_r:
        for label, key in features:
            if st.button(label, key=f"qa_{key}", use_container_width=True):
                with st.spinner(f"Generating {label}..."):
                    state = {}
                    if   key == "roadmap":    state = graph_r.roadmap_node(state)
                    elif key == "gap":        state = graph_r.researchgap_node(state)
                    elif key == "learning":   state = graph_r.learning_node(state)
                    elif key == "methodology":state = graph_r.methodology_node(state)
                    elif key == "paper":      state = graph_r.paperintelligence_node(state)
                    elif key == "discovery":  state = graph_r.researchdiscovery_node(state)
                    elif key == "mentor":     state = graph_r.researchmentor_node(state)
                    elif key == "quiz":       state = graph_r.quizgenerator_node(state)
                    answer = state.get("answer", "")
                append_message(pid_r, "user",      f"Generate: {label}")
                append_message(pid_r, "assistant", answer)
                st.rerun()
    else:
        st.markdown(
            "<p style='font-size:0.72rem;color:var(--text-muted,#7c3aed);line-height:1.5;"
            "padding:4px 2px;'>Open or create a project to unlock quick actions.</p>",
            unsafe_allow_html=True
        )

    st.markdown("<div class='re-divider' style='margin:12px 0;'></div>", unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:0.62rem;font-weight:700;text-transform:uppercase;"
        "letter-spacing:0.12em;color:var(--text-muted,#7c3aed);margin-bottom:6px;'>ℹ️ Info</div>",
        unsafe_allow_html=True
    )
    if st.session_state.active_meta:
        m = st.session_state.active_meta
        topic_full = m.get("topic", "—")
        ps_full    = m.get("problem_statement", "—")
        st.markdown(
            f"<div style='font-size:0.7rem;color:var(--text-primary,#1e1b4b);line-height:1.5;"
            f"padding:4px 2px;'>"
            f"<b style='color:var(--text-secondary,#4c1d95);'>Topic</b><br>{topic_full}<br><br>"
            f"<b style='color:var(--text-secondary,#4c1d95);'>Problem</b><br>"
            f"{ps_full[:200]}{'…' if len(ps_full)>200 else ''}"
            f"</div>",
            unsafe_allow_html=True
        )





