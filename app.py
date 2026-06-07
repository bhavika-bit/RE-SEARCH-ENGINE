import warnings
warnings.filterwarnings("ignore")

import os
import json
import uuid

from dotenv import load_dotenv
import os

load_dotenv()

import streamlit as st

from langchain_community.document_loaders import PyMuPDFLoader, TextLoader, CSVLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate


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
                projects.append(json.load(f))
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
        with open(meta_path, "r") as f:
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
            self.vectorstore = FAISS.load_local(faiss_path, self.embeddings, allow_dangerous_deserialization=True)
            return True
        return False


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
        prompt = f"""
You are an expert research mentor.
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

Be detailed and practical.
"""
        return self.llm.invoke(prompt).content

    def researchgap(self):
        context = self._get_context()
        prompt = f"""
You are an expert research mentor.
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

Be detailed and practical.
"""
        return self.llm.invoke(prompt).content

    def learning(self):
        context = self._get_context()
        prompt = f"""
You are an expert research mentor.
Topic: {self.topic}
Problem Statement: {self.problem_statement}
Relevant Research Context: {context}

Generate:
1. Core concepts
2. Guided learning skeleton
3. Learning sources
4. Applications of the concept
5. Suggestions to study
6.Generate learning resources.

Prefer:
- Official documentation
- Official GitHub repositories
- ArXiv papers
- Hugging Face model pages
- Kaggle datasets

Only provide links if reasonably confident they exist.
Be detailed and practical.
"""
        return self.llm.invoke(prompt).content

    def quizgenerator(self):
        context = self._get_context()
        prompt = f"""
You are an expert research mentor.
Topic: {self.topic}
Problem Statement: {self.problem_statement}
Relevant Research Context: {context}

Generate:
1. MCQ quizzes to practice the concept — don't reveal the answers before the user gives an
answer, show options and then check user answers with the correct answer
2. Flashcards with keywords and definitions
3. Presentation points and practice
4. Topics to focus more on and topics that are already well understood based on the quiz answers
given by the user. Do not guess this, use users answers to tell the topics.

Be detailed and practical.
"""
        return self.llm.invoke(prompt).content

    def methodology(self):
        context = self._get_context()
        prompt = f"""
You are an expert research mentor.
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

Be detailed and practical.
"""
        return self.llm.invoke(prompt).content

    def paperintelligence(self):
        context = self._get_context()
        prompt = f"""
You are an expert research mentor.
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

Be detailed and practical.
"""
        return self.llm.invoke(prompt).content

    def researchdiscovery(self):
        context = self._get_context()
        prompt = f"""
You are an expert research mentor.
Topic: {self.topic}
Problem Statement: {self.problem_statement}
Relevant Research Context: {context}

Generate:
1. Recommended research papers
2. Recommended datasets
3. Emerging trends in this field
4. Current state of research
5. Important authors and researchers
6. Conferences and journals to follow
7. Useful resources and repositories
8. Future directions in the field
9.Generate learning resources.

Prefer:
- Official documentation
- Official GitHub repositories
- ArXiv papers
- Hugging Face model pages
- Kaggle datasets

Only provide links if reasonably confident they exist.

Be detailed and practical.
"""
        return self.llm.invoke(prompt).content

    def researchmentor(self):
        context = self._get_context()
        prompt = f"""
You are an expert research mentor and thesis supervisor.
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
10.Generate learning resources.

Prefer:
- Official documentation
- Official GitHub repositories
- ArXiv papers
- Hugging Face model pages
- Kaggle datasets

Only provide links if reasonably confident they exist.

Be detailed and practical.
"""
        return self.llm.invoke(prompt).content

    def projectsummary(self):
        context = self._get_context()
        prompt = f"""
You are an expert research mentor and thesis supervisor.
Topic: {self.topic}
Problem Statement: {self.problem_statement}
Relevant Research Context: {context}

Generate:
1. Project summary
2. Project scope
4. Idea feasibility
5.Generate learning resources.

Prefer:
- Official documentation
- Official GitHub repositories
- ArXiv papers
- Hugging Face model pages
- Kaggle datasets

Only provide links if reasonably confident they exist.
Be detailed and practical.
"""
        return self.llm.invoke(prompt).content

    def chat(self, user_message, history):
        context = self._get_context()
        history_text = ""
        for msg in history[-10:]:
            role = "User" if msg["role"] == "user" else "Assistant"
            history_text += f"{role}: {msg['content']}\n"
        prompt = f"""
You are an expert research mentor and assistant.
Project Topic: {self.topic}
Problem Statement: {self.problem_statement}
Timeline: {self.timeline}
Relevant Research Context: {context}

Conversation History:
{history_text}

User: {user_message}

Respond as a knowledgeable, helpful research mentor. Be concise yet thorough.
"""
        return self.llm.invoke(prompt).content


class Graph:

    def __init__(self, agent):
        self.agent = agent

    def roadmap_node(self, state):
        state["answer"] = self.agent.roadmap_generation()
        return state

    def researchgap_node(self, state):
        state["answer"] = self.agent.researchgap()
        return state

    def learning_node(self, state):
        state["answer"] = self.agent.learning()
        return state

    def quizgenerator_node(self, state):
        state["answer"] = self.agent.quizgenerator()
        return state

    def methodology_node(self, state):
        state["answer"] = self.agent.methodology()
        return state

    def paperintelligence_node(self, state):
        state["answer"] = self.agent.paperintelligence()
        return state

    def researchdiscovery_node(self, state):
        state["answer"] = self.agent.researchdiscovery()
        return state

    def researchmentor_node(self, state):
        state["answer"] = self.agent.researchmentor()
        return state

    def projectsummary_node(self, state):
        state["answer"] = self.agent.projectsummary()
        return state


st.set_page_config(
    page_title="ResearchEngine",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600;9..40,700&family=DM+Serif+Display:ital@0;1&display=swap');

:root { --radius-sm:8px; --radius-md:12px; --radius-lg:16px; --t:0.16s ease; }

/* ── LIGHT ── */
[data-theme="light"], .stApp[data-theme="light"] {
    --bg-app:#f4f2fb; --bg-sb:#edeaf8; --bg-card:#ffffff;
    --bg-hover:#ede9fe; --border:#ddd6fe; --accent:#6d28d9;
    --accent-soft:#ede9fe; --txt:#1e1b4b; --txt2:#5b5488; --txt3:#9d96cc;
    --qa1:#fce7f3; --qa1f:#831843; --qa2:#fef3c7; --qa2f:#78350f;
    --qa3:#d1fae5; --qa3f:#064e3b; --qa4:#dbeafe; --qa4f:#1e3a5f;
    --qa5:#ede9fe; --qa5f:#3b0764; --qa6:#cffafe; --qa6f:#0c4a6e;
    --qa7:#fef9c3; --qa7f:#713f12; --qa8:#fce7f3; --qa8f:#500724;
}
/* ── DARK ── */
[data-theme="dark"], .stApp[data-theme="dark"] {
    --bg-app:#0d0f17; --bg-sb:#11131e; --bg-card:#181b29;
    --bg-hover:#1f2235; --border:#2a2d45; --accent:#818cf8;
    --accent-soft:#1e2040; --txt:#e8e6ff; --txt2:#9d99cc; --txt3:#5c5888;
    --qa1:#ff1a6b; --qa1f:#fff; --qa2:#ff6d00; --qa2f:#fff;
    --qa3:#00c853; --qa3f:#001a09; --qa4:#2979ff; --qa4f:#fff;
    --qa5:#9c27b0; --qa5f:#fff; --qa6:#00bcd4; --qa6f:#001a1f;
    --qa7:#ffd600; --qa7f:#1a1400; --qa8:#e91e63; --qa8f:#fff;
}

/* ── APP SHELL: full height, no overflow ── */
html, body, .stApp { height: 100vh; overflow: hidden !important; }
.stApp { background: var(--bg-app) !important; font-family: 'DM Sans', sans-serif; }

/* kill default streamlit top padding */
.block-container {
    padding: 0 !important;
    max-width: 100% !important;
    height: 100vh !important;
    overflow: hidden !important;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: var(--bg-sb) !important;
    border-right: 1px solid var(--border) !important;
    height: 100vh !important;
    overflow-y: auto !important;
}
[data-testid="stSidebar"] > div:first-child { padding-top: 1.25rem; }

.sb-brand {
    font-family: 'DM Serif Display', serif;
    font-size: 1.15rem;
    color: var(--accent);
    display: flex; align-items: center; gap: 7px;
    padding-bottom: 0.75rem;
}
.sb-label {
    font-size: 0.65rem; font-weight: 700; letter-spacing: 0.1em;
    text-transform: uppercase; color: var(--txt3);
    margin: 1rem 0 0.4rem 0;
}

/* sidebar new project button */
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] button {
    background: var(--accent) !important; color: #fff !important;
    border: none !important; border-radius: var(--radius-sm) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.85rem !important; font-weight: 600 !important;
}
/* sidebar project list buttons */
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] button {
    background: transparent !important; color: var(--txt2) !important;
    border: 1px solid transparent !important;
    border-radius: var(--radius-sm) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.82rem !important; font-weight: 400 !important;
    text-align: left !important; padding: 8px 10px !important;
    transition: all var(--t) !important;
}
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] button:hover {
    background: var(--bg-hover) !important; color: var(--txt) !important;
    border-color: var(--border) !important;
}

/* ── MAIN 3-COLUMN WRAPPER ── */
/* The columns row must fill viewport height minus nothing (we removed all padding) */
[data-testid="stHorizontalBlock"] {
    height: calc(100vh - 0px) !important;
    align-items: stretch !important;
    gap: 0 !important;
}

/* Each column fills full height */
[data-testid="column"] {
    height: 100vh !important;
    overflow: hidden !important;
    padding: 0 !important;
}

/* ── LEFT COL: scrollable ── */
[data-testid="column"]:nth-child(1) {
    overflow-y: auto !important;
    border-right: 1px solid var(--border);
    padding: 1.25rem 1rem !important;
    background: var(--bg-app);
}

/* ── CENTER COL: scrollable chat ── */
[data-testid="column"]:nth-child(2) {
    overflow-y: auto !important;
    padding: 1.25rem 1.25rem 6rem 1.25rem !important;
    background: var(--bg-app);
}

/* ── RIGHT COL: fixed, no scroll ── */
[data-testid="column"]:nth-child(3) {
    overflow: hidden !important;
    border-left: 1px solid var(--border);
    padding: 1.25rem 0.85rem !important;
    background: var(--bg-card);
    position: sticky !important;
    top: 0 !important;
}

/* ── PROJECT HEADER (compact horizontal strip) ── */
.proj-header {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    margin-bottom: 1rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid var(--border);
}
.proj-header-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1.1rem;
    font-weight: 400;
    color: var(--txt);
    margin: 0;
    line-height: 1.25;
    flex: 1;
    min-width: 120px;
}
.proj-pill {
    background: var(--accent-soft);
    border: 1px solid var(--border);
    border-radius: 100px;
    padding: 2px 10px;
    font-size: 0.72rem;
    font-weight: 500;
    color: var(--txt2);
    white-space: nowrap;
}
.proj-pill b { color: var(--txt3); font-weight: 400; margin-right: 3px; }

/* ── SECTION LABELS ── */
.sec-label {
    font-size: 0.65rem; font-weight: 700; letter-spacing: 0.09em;
    text-transform: uppercase; color: var(--txt3); margin: 0 0 0.6rem 0;
}

/* ── CHAT MESSAGES ── */
[data-testid="stChatMessage"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    margin-bottom: 0.5rem !important;
    font-family: 'DM Sans', sans-serif !important;
}
[data-testid="stChatInputContainer"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    background: var(--bg-card) !important;
}

/* ── QUICK ACTION BUTTONS ── */
.studio-wrap [data-testid="stVerticalBlock"] > div button {
    border-radius: var(--radius-md) !important;
    min-height: 68px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.76rem !important; font-weight: 600 !important;
    border: none !important; white-space: pre-wrap !important;
    line-height: 1.35 !important; width: 100% !important;
    transition: transform var(--t), filter var(--t) !important;
}
.studio-wrap [data-testid="stVerticalBlock"] > div button:hover {
    transform: translateY(-2px) !important;
    filter: brightness(1.08) !important;
    box-shadow: 0 4px 14px rgba(0,0,0,0.18) !important;
}
.studio-wrap [data-testid="stVerticalBlock"] > div:nth-child(1) button { background:var(--qa1)!important; color:var(--qa1f)!important; border:none!important; }
.studio-wrap [data-testid="stVerticalBlock"] > div:nth-child(2) button { background:var(--qa2)!important; color:var(--qa2f)!important; border:none!important; }
.studio-wrap [data-testid="stVerticalBlock"] > div:nth-child(3) button { background:var(--qa3)!important; color:var(--qa3f)!important; border:none!important; }
.studio-wrap [data-testid="stVerticalBlock"] > div:nth-child(4) button { background:var(--qa4)!important; color:var(--qa4f)!important; border:none!important; }
.studio-wrap [data-testid="stVerticalBlock"] > div:nth-child(5) button { background:var(--qa5)!important; color:var(--qa5f)!important; border:none!important; }
.studio-wrap [data-testid="stVerticalBlock"] > div:nth-child(6) button { background:var(--qa6)!important; color:var(--qa6f)!important; border:none!important; }
.studio-wrap [data-testid="stVerticalBlock"] > div:nth-child(7) button { background:var(--qa7)!important; color:var(--qa7f)!important; border:none!important; }
.studio-wrap [data-testid="stVerticalBlock"] > div:nth-child(8) button { background:var(--qa8)!important; color:var(--qa8f)!important; border:none!important; }

/* ── DOWNLOAD BUTTON ── */
[data-testid="stDownloadButton"] button {
    background: var(--accent-soft) !important; color: var(--accent) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.8rem !important; font-weight: 600 !important;
}
[data-testid="stDownloadButton"] button:hover {
    background: var(--accent) !important; color: #fff !important;
}

/* ── RECENT SNIPPETS ── */
.recent-item {
    font-size: 0.74rem; color: var(--txt3); padding: 5px 0;
    border-bottom: 1px solid var(--border); line-height: 1.4;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}

/* ── FORM INPUTS ── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    font-family: 'DM Sans', sans-serif !important;
    border-radius: var(--radius-sm) !important;
    border: 1px solid var(--border) !important;
    background: var(--bg-card) !important;
    color: var(--txt) !important;
}
h1 {
    font-family: 'DM Serif Display', serif !important;
    font-weight: 400 !important; color: var(--txt) !important;
}
hr { border-color: var(--border) !important; margin: 0.6rem 0 !important; }

/* hide streamlit default menu clutter in columns */
[data-testid="stToolbar"] { display: none !important; }
</style>
""", unsafe_allow_html=True)


# ── LLM (shared, cached) ──
@st.cache_resource
def get_llm():
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.6)


@st.cache_resource
def load_cached_faiss(project_id):
    rag = RAG()
    rag.load_vectordb(project_id)
    return rag


@st.cache_resource
def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )


# ── Session state defaults ──
if "active_project_id" not in st.session_state:
    st.session_state.active_project_id = None
if "agent" not in st.session_state:
    st.session_state.agent = None
if "graph" not in st.session_state:
    st.session_state.graph = None
if "show_new_project_form" not in st.session_state:
    st.session_state.show_new_project_form = False
if "triggered_feature" not in st.session_state:
    st.session_state.triggered_feature = None


def load_project(project_id):
    meta_path = get_metadata_path(project_id)
    if not os.path.exists(meta_path):
        st.error("Project not found.")
        return
    with open(meta_path) as f:
        meta = json.load(f)
    faiss_path = get_faiss_path(project_id)
    if os.path.exists(faiss_path):
        rag = load_cached_faiss(project_id)
    else:
        rag = None
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


# ── Feature definitions ──
FEATURES = [
    ("📅 Roadmap",       "roadmap",      "Roadmap"),
    ("🔍 Research Gap",  "gap",          "Research Gap"),
    ("📚 Learning Path", "learning",     "Learning Path"),
    ("🧠 Methodology",   "methodology",  "Methodology"),
    ("📄 Paper Intel",   "paper",        "Paper Intel"),
    ("🌐 Discovery",     "discovery",    "Discovery"),
    ("🎓 Mentor",        "mentor",       "Mentor"),
    ("❓ Quiz",          "quiz",         "Quiz"),
]


# ════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div class="sidebar-brand">🔬 ResearchEngine</div>', unsafe_allow_html=True)
    st.markdown("---")

    if st.button("＋ New Project", use_container_width=True, type="primary"):
        st.session_state.show_new_project_form = True
        st.session_state.active_project_id = None

    # ── Project list ──
    st.markdown('<div class="sidebar-section-label">My Projects</div>', unsafe_allow_html=True)
    all_projects = load_all_projects()
    if not all_projects:
        st.caption("No projects yet.")
    else:
        for proj in all_projects:
            pid = proj["project_id"]
            label = proj["project_name"]
            is_active = (pid == st.session_state.active_project_id)
            btn_label = f"{'▶  ' if is_active else ''}{label}"
            if st.button(btn_label, key=f"proj_{pid}", use_container_width=True):
                st.session_state.show_new_project_form = False
                load_project(pid)
                st.rerun()

    # ── Import ──
    st.markdown("---")
    st.markdown('<div class="sidebar-section-label">Import / Export</div>', unsafe_allow_html=True)
    uploaded_project_file = st.file_uploader("Import project (.json)", type=["json"], label_visibility="collapsed")
    if uploaded_project_file is not None:
        try:
            imported_project_id = import_project(uploaded_project_file)
            st.success("Project imported!")
            load_project(imported_project_id)
            st.rerun()
        except Exception as e:
            st.error(f"Import failed: {str(e)}")


# ════════════════════════════════════════════
# TRIGGERED FEATURE HANDLER
# ════════════════════════════════════════════
if st.session_state.triggered_feature and st.session_state.active_project_id and st.session_state.agent:
    key   = st.session_state.triggered_feature
    pid   = st.session_state.active_project_id
    graph = st.session_state.graph
    feature_label = next((lbl for lbl, k, *_ in FEATURES if k == key), key)

    with st.spinner(f"Generating {feature_label}..."):
        state = {}
        if key == "roadmap":
            state = graph.roadmap_node(state)
        elif key == "gap":
            state = graph.researchgap_node(state)
        elif key == "learning":
            state = graph.learning_node(state)
        elif key == "methodology":
            state = graph.methodology_node(state)
        elif key == "paper":
            state = graph.paperintelligence_node(state)
        elif key == "discovery":
            state = graph.researchdiscovery_node(state)
        elif key == "mentor":
            state = graph.researchmentor_node(state)
        elif key == "quiz":
            state = graph.quizgenerator_node(state)
        answer = state.get("answer", "")

    append_message(pid, "user", f"Generate: {feature_label}")
    append_message(pid, "assistant", answer)
    st.session_state.triggered_feature = None
    st.rerun()


# ════════════════════════════════════════════
# NEW PROJECT FORM
# ════════════════════════════════════════════
if st.session_state.show_new_project_form:
    st.title("Create New Project")

    with st.form("new_project_form"):
        project_name   = st.text_input("Project Name", placeholder="e.g. Crime Hotspot Analysis")
        topic          = st.text_input("Research Topic", placeholder="e.g. Urban Crime Prediction using ML")
        problem_stmt   = st.text_area("Problem Statement", placeholder="Describe what you're solving...")
        timeline       = st.text_input("Timeline", placeholder="e.g. 8 weeks")
        uploaded_files = st.file_uploader(
            "Upload Research Documents (optional)",
            type=["pdf", "txt", "csv", "docx"],
            accept_multiple_files=True
        )
        submitted = st.form_submit_button("🚀 Create Project", type="primary")

    if submitted:
        if not project_name or not topic or not problem_stmt:
            st.error("Please fill in Project Name, Topic, and Problem Statement.")
        else:
            project_id = str(uuid.uuid4())[:8]
            os.makedirs(get_project_path(project_id), exist_ok=True)
            rag = None
            if uploaded_files:
                with st.spinner("Processing documents..."):
                    rag = RAG()
                    rag.load_data_from_files(uploaded_files, project_id)
                    rag.chunking()
                    rag.embedding()
                    rag.build_vectordb()
                    rag.save_vectordb(project_id)
                st.success(f"Loaded {len(rag.documents)} document pages.")
            metadata = {
                "project_id": project_id,
                "project_name": project_name,
                "topic": topic,
                "problem_statement": problem_stmt,
                "timeline": timeline,
                "has_docs": rag is not None
            }
            save_metadata(project_id, metadata)
            llm = get_llm()
            agent = ResearchAnalyst(rag_instance=rag, llm_instance=llm)
            agent.set_project(topic=topic, problem_statement=problem_stmt, timeline=timeline)
            st.session_state.active_project_id = project_id
            st.session_state.agent = agent
            st.session_state.graph = Graph(agent)
            st.session_state.active_meta = metadata
            st.session_state.show_new_project_form = False
            with st.spinner("Generating project summary..."):
                summary = agent.projectsummary()
            append_message(project_id, "assistant", f"**Project Summary**\n\n{summary}")
            st.success("Project created!")
            st.rerun()


# ════════════════════════════════════════════
# ACTIVE PROJECT VIEW
# ════════════════════════════════════════════
elif st.session_state.active_project_id and st.session_state.agent:
    pid   = st.session_state.active_project_id
    meta  = st.session_state.active_meta
    agent = st.session_state.agent
    graph = st.session_state.graph

    # columns: left info | center chat | right actions
    left_col, mid_col, right_col = st.columns([0.95, 2.6, 1.05])

    # ════════════════════════════
    # LEFT — compact project info + export + recents
    # ════════════════════════════
    with left_col:
        topic_short = meta['topic'][:34] + ('…' if len(meta['topic']) > 34 else '')
        docs_badge  = '✅ Docs attached' if meta.get('has_docs') else '📄 No docs'
        st.markdown(
            f"""
            <div class="proj-header">
                <p class="proj-header-title">🔬 {meta['project_name']}</p>
            </div>
            <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:1rem;">
                <span class="proj-pill"><b>Topic</b>{topic_short}</span>
                <span class="proj-pill"><b>Timeline</b>{meta['timeline']}</span>
                <span class="proj-pill">{docs_badge}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown('<div class="sb-label">Export</div>', unsafe_allow_html=True)
        export_data = export_project(pid)
        st.download_button(
            label="📤 Export Project",
            data=export_data,
            file_name=f"{meta['project_name']}.json",
            mime="application/json",
            use_container_width=True
        )

        messages_all = load_chat_history(pid)
        if messages_all:
            st.markdown('<div class="sb-label" style="margin-top:1rem;">Recent</div>', unsafe_allow_html=True)
            for msg in messages_all[-5:]:
                icon = "🧑" if msg["role"] == "user" else "🤖"
                snippet = msg["content"][:55].replace("\n", " ") + "…"
                st.markdown(f'<div class="recent-item">{icon} {snippet}</div>', unsafe_allow_html=True)

    # ════════════════════════════
    # CENTER — scrollable chat
    # ════════════════════════════
    with mid_col:
        st.markdown('<div class="sec-label">Research Chat</div>', unsafe_allow_html=True)
        messages = load_chat_history(pid)
        for msg in messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # ════════════════════════════
    # RIGHT — sticky quick actions
    # ════════════════════════════
    with right_col:
        st.markdown('<div class="sec-label">Quick Actions</div>', unsafe_allow_html=True)
        st.markdown('<div class="studio-wrap">', unsafe_allow_html=True)

        STUDIO = [
            ("📅\nRoadmap",      "roadmap"),
            ("🔍\nResearch Gap", "gap"),
            ("📚\nLearning",     "learning"),
            ("🧠\nMethodology",  "methodology"),
            ("📄\nPaper Intel",  "paper"),
            ("🌐\nDiscovery",    "discovery"),
            ("🎓\nMentor",       "mentor"),
            ("❓\nQuiz",         "quiz"),
        ]
        for i in range(0, len(STUDIO), 2):
            c1, c2 = st.columns(2)
            for col, (label, key) in zip([c1, c2], STUDIO[i:i+2]):
                with col:
                    if st.button(label, key=f"qa_{key}", use_container_width=True):
                        st.session_state.triggered_feature = key
                        st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    # ── CHAT INPUT ──
    prompt = st.chat_input("Ask your research mentor anything...")
    if prompt:
        with mid_col:
            with st.chat_message("user"):
                st.markdown(prompt)
        messages = append_message(pid, "user", prompt)
        with mid_col:
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = agent.chat(prompt, messages)
                st.markdown(response)
        append_message(pid, "assistant", response)
        st.rerun()


# ════════════════════════════════════════════
# LANDING / EMPTY STATE
# ════════════════════════════════════════════
else:
    st.markdown("""
    <div style="text-align:center; padding: 100px 40px;">
        <p style="font-family:'DM Serif Display',serif; font-size:2.5rem; font-weight:400; color:var(--text-primary); margin:0 0 0.5rem 0; letter-spacing:-0.02em;">
            🔬 ResearchEngine
        </p>
        <p style="font-family:'DM Sans',sans-serif; font-size:1.05rem; color:var(--text-muted); margin:0 0 2rem 0;">
            Your AI-powered research mentor.
        </p>
        <p style="font-family:'DM Sans',sans-serif; font-size:0.9rem; color:var(--text-secondary);">
            ← Click <strong>＋ New Project</strong> in the sidebar to get started.
        </p>
    </div>
    """, unsafe_allow_html=True)
