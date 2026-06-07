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
/* ─── GOOGLE FONT ─── */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Serif+Display:ital@0;1&display=swap');

/* ─── ROOT TOKENS ─── */
:root {
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 18px;
    --transition: 0.18s ease;
}

/* ════════════════════════════
   LIGHT MODE  (pastel palette)
   ════════════════════════════ */
[data-theme="light"],
.stApp[data-theme="light"] {
    --bg-app:        #f5f3ff;
    --bg-sidebar:    #ede9fe;
    --bg-card:       #ffffff;
    --bg-card-hover: #f3f0ff;
    --bg-info:       #ffffff;
    --bg-chat:       #faf9ff;
    --border:        #ddd6fe;
    --accent:        #7c3aed;
    --accent-soft:   #ede9fe;
    --text-primary:  #1e1b4b;
    --text-secondary:#5b5488;
    --text-muted:    #8b7fc7;

    /* quick-action button palette — pastels */
    --qa1-bg:#fce7f3; --qa1-fg:#831843;
    --qa2-bg:#fef3c7; --qa2-fg:#78350f;
    --qa3-bg:#d1fae5; --qa3-fg:#064e3b;
    --qa4-bg:#dbeafe; --qa4-fg:#1e3a5f;
    --qa5-bg:#ede9fe; --qa5-fg:#3b0764;
    --qa6-bg:#cffafe; --qa6-fg:#0c4a6e;
    --qa7-bg:#fef9c3; --qa7-fg:#713f12;
    --qa8-bg:#fce7f3; --qa8-fg:#500724;
}

/* ════════════════════════════
   DARK MODE  (vibrant palette)
   ════════════════════════════ */
[data-theme="dark"],
.stApp[data-theme="dark"] {
    --bg-app:        #0d0f17;
    --bg-sidebar:    #11131e;
    --bg-card:       #181b29;
    --bg-card-hover: #1f2235;
    --bg-info:       #181b29;
    --bg-chat:       #13151f;
    --border:        #2a2d45;
    --accent:        #818cf8;
    --accent-soft:   #1e2040;
    --text-primary:  #e8e6ff;
    --text-secondary:#9d99cc;
    --text-muted:    #5c5888;

    /* quick-action button palette — vibrant */
    --qa1-bg:#ff1a6b; --qa1-fg:#ffffff;
    --qa2-bg:#ff6d00; --qa2-fg:#ffffff;
    --qa3-bg:#00c853; --qa3-fg:#001a09;
    --qa4-bg:#2979ff; --qa4-fg:#ffffff;
    --qa5-bg:#9c27b0; --qa5-fg:#ffffff;
    --qa6-bg:#00bcd4; --qa6-fg:#001a1f;
    --qa7-bg:#ffd600; --qa7-fg:#1a1400;
    --qa8-bg:#e91e63; --qa8-fg:#ffffff;
}

/* ─── SIDEBAR ─── */
[data-testid="stSidebar"] {
    background: var(--bg-sidebar) !important;
    border-right: 1px solid var(--border) !important;
    padding-top: 0 !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.5rem;
}

/* sidebar logo/title */
.sidebar-brand {
    font-family: 'DM Serif Display', serif;
    font-size: 1.25rem;
    font-weight: 400;
    color: var(--accent);
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 0 0 1rem 0;
    letter-spacing: -0.01em;
}

/* section labels in sidebar */
.sidebar-section-label {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin: 1.2rem 0 0.5rem 0;
}

/* project list items */
.proj-item {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.875rem;
    padding: 9px 12px;
    border-radius: var(--radius-sm);
    cursor: pointer;
    color: var(--text-secondary);
    border: 1px solid transparent;
    margin-bottom: 4px;
    transition: all var(--transition);
    background: transparent;
}
.proj-item:hover {
    background: var(--bg-card-hover);
    color: var(--text-primary);
    border-color: var(--border);
}
.proj-item.active {
    background: var(--accent-soft);
    color: var(--accent);
    border-color: var(--accent);
    font-weight: 600;
}

/* ─── NEW PROJECT BUTTON ─── */
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] button {
    background: var(--accent) !important;
    color: #fff !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    letter-spacing: 0.01em !important;
    padding: 0.5rem 1rem !important;
    transition: opacity var(--transition) !important;
}
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] button:hover {
    opacity: 0.88 !important;
}

/* sidebar project buttons */
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] button {
    background: transparent !important;
    color: var(--text-secondary) !important;
    border: 1px solid transparent !important;
    border-radius: var(--radius-sm) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.875rem !important;
    text-align: left !important;
    padding: 9px 12px !important;
    transition: all var(--transition) !important;
    font-weight: 400 !important;
}
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] button:hover {
    background: var(--bg-card-hover) !important;
    color: var(--text-primary) !important;
    border-color: var(--border) !important;
}

/* ─── MAIN AREA ─── */
.stApp {
    background: var(--bg-app) !important;
    font-family: 'DM Sans', sans-serif;
}
.block-container {
    padding: 1.5rem 2rem 4rem 2rem !important;
    max-width: 100% !important;
}

/* ─── PROJECT BANNER (top of center) ─── */
.project-banner {
    background: var(--bg-info);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
}
.project-banner h2 {
    font-family: 'DM Serif Display', serif;
    font-size: 1.5rem;
    font-weight: 400;
    color: var(--text-primary);
    margin: 0 0 0.75rem 0;
    line-height: 1.2;
}
.info-pills {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}
.info-pill {
    background: var(--accent-soft);
    border: 1px solid var(--border);
    border-radius: 100px;
    padding: 3px 12px;
    font-size: 0.78rem;
    font-weight: 500;
    color: var(--text-secondary);
    font-family: 'DM Sans', sans-serif;
    display: flex;
    align-items: center;
    gap: 5px;
}
.info-pill span.pill-label {
    color: var(--text-muted);
    font-weight: 400;
    font-size: 0.72rem;
}

/* ─── SECTION HEADERS ─── */
.section-header {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin: 0 0 0.75rem 0;
}

/* ─── CHAT AREA ─── */
.chat-container {
    background: var(--bg-chat);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 1rem;
    min-height: 300px;
}
[data-testid="stChatMessage"] {
    background: var(--bg-card) !important;
    border-radius: var(--radius-md) !important;
    border: 1px solid var(--border) !important;
    margin-bottom: 0.5rem !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* chat input */
[data-testid="stChatInputContainer"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    background: var(--bg-card) !important;
}

/* ─── QUICK ACTIONS PANEL ─── */
.qa-header {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin: 0 0 0.75rem 0;
}
.qa-panel {
    background: var(--bg-info);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 1rem;
}

/* quick-action buttons base */
div[class*="qa-panel"] [data-testid="stBaseButton-secondary"] button,
.qa-panel ~ div [data-testid="stBaseButton-secondary"] button {
    border-radius: var(--radius-md) !important;
    min-height: 72px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    border: none !important;
    white-space: pre-wrap !important;
    line-height: 1.4 !important;
    transition: transform var(--transition), filter var(--transition) !important;
}

/* individual QA button colors via nth-child on the studio wrapper */
.studio-wrap [data-testid="stVerticalBlock"] > div:nth-child(1) button { background: var(--qa1-bg) !important; color: var(--qa1-fg) !important; border:none !important; border-radius:var(--radius-md) !important; min-height:72px !important; font-family:'DM Sans',sans-serif !important; font-size:0.78rem !important; font-weight:600 !important; }
.studio-wrap [data-testid="stVerticalBlock"] > div:nth-child(2) button { background: var(--qa2-bg) !important; color: var(--qa2-fg) !important; border:none !important; border-radius:var(--radius-md) !important; min-height:72px !important; font-family:'DM Sans',sans-serif !important; font-size:0.78rem !important; font-weight:600 !important; }
.studio-wrap [data-testid="stVerticalBlock"] > div:nth-child(3) button { background: var(--qa3-bg) !important; color: var(--qa3-fg) !important; border:none !important; border-radius:var(--radius-md) !important; min-height:72px !important; font-family:'DM Sans',sans-serif !important; font-size:0.78rem !important; font-weight:600 !important; }
.studio-wrap [data-testid="stVerticalBlock"] > div:nth-child(4) button { background: var(--qa4-bg) !important; color: var(--qa4-fg) !important; border:none !important; border-radius:var(--radius-md) !important; min-height:72px !important; font-family:'DM Sans',sans-serif !important; font-size:0.78rem !important; font-weight:600 !important; }
.studio-wrap [data-testid="stVerticalBlock"] > div:nth-child(5) button { background: var(--qa5-bg) !important; color: var(--qa5-fg) !important; border:none !important; border-radius:var(--radius-md) !important; min-height:72px !important; font-family:'DM Sans',sans-serif !important; font-size:0.78rem !important; font-weight:600 !important; }
.studio-wrap [data-testid="stVerticalBlock"] > div:nth-child(6) button { background: var(--qa6-bg) !important; color: var(--qa6-fg) !important; border:none !important; border-radius:var(--radius-md) !important; min-height:72px !important; font-family:'DM Sans',sans-serif !important; font-size:0.78rem !important; font-weight:600 !important; }
.studio-wrap [data-testid="stVerticalBlock"] > div:nth-child(7) button { background: var(--qa7-bg) !important; color: var(--qa7-fg) !important; border:none !important; border-radius:var(--radius-md) !important; min-height:72px !important; font-family:'DM Sans',sans-serif !important; font-size:0.78rem !important; font-weight:600 !important; }
.studio-wrap [data-testid="stVerticalBlock"] > div:nth-child(8) button { background: var(--qa8-bg) !important; color: var(--qa8-fg) !important; border:none !important; border-radius:var(--radius-md) !important; min-height:72px !important; font-family:'DM Sans',sans-serif !important; font-size:0.78rem !important; font-weight:600 !important; }
.studio-wrap [data-testid="stVerticalBlock"] > div button:hover {
    transform: translateY(-2px) !important;
    filter: brightness(1.08) !important;
    box-shadow: 0 4px 16px rgba(0,0,0,0.15) !important;
}

/* ─── METRICS ─── */
[data-testid="stMetric"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    padding: 10px 14px !important;
}
[data-testid="stMetricLabel"] {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.07em !important;
    text-transform: uppercase !important;
    color: var(--text-muted) !important;
}
[data-testid="stMetricValue"] {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    color: var(--text-primary) !important;
}

/* ─── DIVIDER ─── */
hr {
    border-color: var(--border) !important;
    margin: 0.75rem 0 !important;
}

/* ─── PAGE TITLE (h1) for forms ─── */
h1 {
    font-family: 'DM Serif Display', serif !important;
    font-weight: 400 !important;
    color: var(--text-primary) !important;
    letter-spacing: -0.02em !important;
}

/* ─── DOWNLOAD BUTTON ─── */
[data-testid="stDownloadButton"] button {
    background: var(--accent-soft) !important;
    color: var(--accent) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    transition: background var(--transition) !important;
}
[data-testid="stDownloadButton"] button:hover {
    background: var(--accent) !important;
    color: #fff !important;
}

/* ─── CHAT HISTORY SCROLL ─── */
.chat-scroll {
    max-height: 58vh;
    overflow-y: auto;
    padding-right: 4px;
    scrollbar-width: thin;
    scrollbar-color: var(--border) transparent;
}

/* ─── FORM INPUTS ─── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    font-family: 'DM Sans', sans-serif !important;
    border-radius: var(--radius-sm) !important;
    border: 1px solid var(--border) !important;
    background: var(--bg-card) !important;
    color: var(--text-primary) !important;
}

/* remove default streamlit padding on columns */
[data-testid="column"] {
    padding: 0 0.4rem !important;
}
[data-testid="column"]:first-child { padding-left: 0 !important; }
[data-testid="column"]:last-child  { padding-right: 0 !important; }

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

    # ── 3-column layout: center is dominant ──
    left_col, mid_col, right_col = st.columns([1, 2.8, 1.1])

    # ════════════════════════════
    # LEFT — project info + export
    # ════════════════════════════
    with left_col:
        # Project title card
        st.markdown(
            f"""
            <div class="project-banner">
                <h2>🔬 {meta['project_name']}</h2>
                <div class="info-pills">
                    <div class="info-pill">
                        <span class="pill-label">Topic</span>
                        {meta['topic'][:28] + ('…' if len(meta['topic']) > 28 else '')}
                    </div>
                    <div class="info-pill">
                        <span class="pill-label">Timeline</span>
                        {meta['timeline']}
                    </div>
                    <div class="info-pill">
                        {'✅ Docs' if meta.get('has_docs') else '📄 No docs'}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Export
        st.markdown('<div class="sidebar-section-label" style="margin-top:1rem;">Backup</div>', unsafe_allow_html=True)
        export_data = export_project(pid)
        st.download_button(
            label="📤 Export Project",
            data=export_data,
            file_name=f"{meta['project_name']}.json",
            mime="application/json",
            use_container_width=True
        )

        # Chat history summary (last few turns)
        messages_all = load_chat_history(pid)
        if messages_all:
            st.markdown('<div class="sidebar-section-label" style="margin-top:1rem;">Recent</div>', unsafe_allow_html=True)
            for msg in messages_all[-4:]:
                icon = "🧑" if msg["role"] == "user" else "🤖"
                snippet = msg["content"][:60].replace("\n", " ") + ("…" if len(msg["content"]) > 60 else "")
                st.markdown(
                    f'<div style="font-size:0.76rem;color:var(--text-muted);padding:4px 0;border-bottom:1px solid var(--border);line-height:1.4;">'
                    f'{icon} {snippet}</div>',
                    unsafe_allow_html=True
                )

    # ════════════════════════════
    # CENTER — chat
    # ════════════════════════════
    with mid_col:
        st.markdown('<div class="section-header">Research Chat</div>', unsafe_allow_html=True)

        messages = load_chat_history(pid)
        for msg in messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # ════════════════════════════
    # RIGHT — quick actions (no "Studio" branding)
    # ════════════════════════════
    with right_col:
        st.markdown('<div class="qa-header">Quick Actions</div>', unsafe_allow_html=True)
        st.markdown('<div class="studio-wrap">', unsafe_allow_html=True)

        STUDIO = [
            ("📅\nRoadmap",       "roadmap"),
            ("🔍\nResearch Gap",  "gap"),
            ("📚\nLearning",      "learning"),
            ("🧠\nMethodology",   "methodology"),
            ("📄\nPaper Intel",   "paper"),
            ("🌐\nDiscovery",     "discovery"),
            ("🎓\nMentor",        "mentor"),
            ("❓\nQuiz",          "quiz"),
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
