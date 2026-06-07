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
    """
    Export metadata + chat history.
    Does NOT export FAISS vector database.
    """
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
    """
    Import project metadata + chat history.
    Creates a fresh project ID.
    """
    data = json.load(uploaded_file)
 
    metadata = data["metadata"]
    chat_history = data.get("chat_history", [])
 
    new_project_id = str(uuid.uuid4())[:8]
 
    metadata["project_id"] = new_project_id
 
    os.makedirs(get_project_path(new_project_id), exist_ok=True)
 
    save_metadata(
        new_project_id,
        metadata
    )
 
    save_chat_history(
        new_project_id,
        chat_history
    )
 
    return new_project_id
 
 
class RAG:
    def __init__(self):
        self.documents = None
        self.chunks = None
        self.embeddings = None
        self.vectorstore = None
 
    def load_data_from_files(self, uploaded_files, project_id):
        """Accept Streamlit UploadedFile objects, save to temp, load."""
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
        """Chat with context from documents + project info + conversation history."""
        context = self._get_context()
 
        history_text = ""
        for msg in history[-10:]:   # last 10 messages for context window
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
    /* ── Dark mode ── */
    [data-testid="stAppViewContainer"][data-theme="dark"] [data-testid="stSidebar"],
    .stApp[data-theme="dark"] [data-testid="stSidebar"] {
        background: #0f1117;
    }
    [data-testid="stAppViewContainer"][data-theme="dark"] .project-card,
    .stApp[data-theme="dark"] .project-card {
        background: #1e2130;
        border-left: 3px solid #4f8ef7;
        color: #ffffff;
    }
    [data-testid="stAppViewContainer"][data-theme="dark"] .project-card:hover,
    .stApp[data-theme="dark"] .project-card:hover {
        background: #252a40;
    }
 
    /* ── Light mode — pastel palette ── */
    [data-testid="stAppViewContainer"][data-theme="light"] [data-testid="stSidebar"],
    .stApp[data-theme="light"] [data-testid="stSidebar"] {
        background: #f0f4ff;
    }
    [data-testid="stAppViewContainer"][data-theme="light"] .project-card,
    .stApp[data-theme="light"] .project-card {
        background: #e8eeff;
        border-left: 3px solid #7ba7f7;
        color: #2c3e6b;
    }
    [data-testid="stAppViewContainer"][data-theme="light"] .project-card:hover,
    .stApp[data-theme="light"] .project-card:hover {
        background: #dce6ff;
    }
 
    /* Fallback: applies when theme attribute is absent (default dark-style) */
    [data-testid="stSidebar"] {
        background: #0f1117;
    }
    .project-card {
        background: #1e2130;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 8px;
        cursor: pointer;
        border-left: 3px solid #4f8ef7;
    }
    .project-card:hover { background: #252a40; }
 
    /* ── Light mode overrides for main content ── */
    @media (prefers-color-scheme: light) {
        [data-testid="stSidebar"] {
            background: #f0f4ff !important;
        }
        .project-card {
            background: #e8eeff !important;
            border-left: 3px solid #7ba7f7 !important;
            color: #2c3e6b !important;
        }
        .project-card:hover {
            background: #dce6ff !important;
        }
    }
 
    .stChatMessage { border-radius: 10px; }
 
    /* ── Quick Action buttons — shared base ── */
    .quick-action-btn {
        display: block;
        width: 100%;
        padding: 10px 14px;
        margin-bottom: 7px;
        border-radius: 9px;
        border: none;
        font-size: 0.88rem;
        font-weight: 600;
        text-align: left;
        cursor: pointer;
        transition: filter 0.15s ease, transform 0.1s ease;
        letter-spacing: 0.01em;
    }
    .quick-action-btn:hover {
        filter: brightness(1.08);
        transform: translateX(2px);
    }
 
    /* ── LIGHT MODE pastel — target the right column's stButton elements ── */
    [data-theme="light"] [data-testid="column"]:last-child .stButton:nth-child(1) button,
    .stApp[data-theme="light"] [data-testid="column"]:last-child .stButton:nth-child(1) button
        { background: #ffd6e0 !important; color: #7a2240 !important; border: none !important; }
    [data-theme="light"] [data-testid="column"]:last-child .stButton:nth-child(2) button,
    .stApp[data-theme="light"] [data-testid="column"]:last-child .stButton:nth-child(2) button
        { background: #fde2c8 !important; color: #7a3d10 !important; border: none !important; }
    [data-theme="light"] [data-testid="column"]:last-child .stButton:nth-child(3) button,
    .stApp[data-theme="light"] [data-testid="column"]:last-child .stButton:nth-child(3) button
        { background: #d4f0c8 !important; color: #255c18 !important; border: none !important; }
    [data-theme="light"] [data-testid="column"]:last-child .stButton:nth-child(4) button,
    .stApp[data-theme="light"] [data-testid="column"]:last-child .stButton:nth-child(4) button
        { background: #cde8ff !important; color: #0d3d6b !important; border: none !important; }
    [data-theme="light"] [data-testid="column"]:last-child .stButton:nth-child(5) button,
    .stApp[data-theme="light"] [data-testid="column"]:last-child .stButton:nth-child(5) button
        { background: #e8d5fb !important; color: #4a1d80 !important; border: none !important; }
    [data-theme="light"] [data-testid="column"]:last-child .stButton:nth-child(6) button,
    .stApp[data-theme="light"] [data-testid="column"]:last-child .stButton:nth-child(6) button
        { background: #c8f0ee !important; color: #0d4f4c !important; border: none !important; }
    [data-theme="light"] [data-testid="column"]:last-child .stButton:nth-child(7) button,
    .stApp[data-theme="light"] [data-testid="column"]:last-child .stButton:nth-child(7) button
        { background: #fff3c4 !important; color: #6b4d00 !important; border: none !important; }
    [data-theme="light"] [data-testid="column"]:last-child .stButton:nth-child(8) button,
    .stApp[data-theme="light"] [data-testid="column"]:last-child .stButton:nth-child(8) button
        { background: #ffd6f5 !important; color: #6b0d55 !important; border: none !important; }
 
    /* ── DARK MODE vibrant — same right column targeting ── */
    [data-theme="dark"] [data-testid="column"]:last-child .stButton:nth-child(1) button,
    .stApp[data-theme="dark"] [data-testid="column"]:last-child .stButton:nth-child(1) button
        { background: #ff2d6b !important; color: #fff !important; border: none !important; }
    [data-theme="dark"] [data-testid="column"]:last-child .stButton:nth-child(2) button,
    .stApp[data-theme="dark"] [data-testid="column"]:last-child .stButton:nth-child(2) button
        { background: #ff7a00 !important; color: #fff !important; border: none !important; }
    [data-theme="dark"] [data-testid="column"]:last-child .stButton:nth-child(3) button,
    .stApp[data-theme="dark"] [data-testid="column"]:last-child .stButton:nth-child(3) button
        { background: #00e676 !important; color: #002b15 !important; border: none !important; }
    [data-theme="dark"] [data-testid="column"]:last-child .stButton:nth-child(4) button,
    .stApp[data-theme="dark"] [data-testid="column"]:last-child .stButton:nth-child(4) button
        { background: #2979ff !important; color: #fff !important; border: none !important; }
    [data-theme="dark"] [data-testid="column"]:last-child .stButton:nth-child(5) button,
    .stApp[data-theme="dark"] [data-testid="column"]:last-child .stButton:nth-child(5) button
        { background: #d500f9 !important; color: #fff !important; border: none !important; }
    [data-theme="dark"] [data-testid="column"]:last-child .stButton:nth-child(6) button,
    .stApp[data-theme="dark"] [data-testid="column"]:last-child .stButton:nth-child(6) button
        { background: #00e5ff !important; color: #002b30 !important; border: none !important; }
    [data-theme="dark"] [data-testid="column"]:last-child .stButton:nth-child(7) button,
    .stApp[data-theme="dark"] [data-testid="column"]:last-child .stButton:nth-child(7) button
        { background: #ffea00 !important; color: #2b2500 !important; border: none !important; }
    [data-theme="dark"] [data-testid="column"]:last-child .stButton:nth-child(8) button,
    .stApp[data-theme="dark"] [data-testid="column"]:last-child .stButton:nth-child(8) button
        { background: #ff4081 !important; color: #fff !important; border: none !important; }
 
    /* Fallback dark (no data-theme attr) */
    [data-testid="column"]:last-child .stButton:nth-child(1) button { background: #ff2d6b !important; color: #fff !important; border: none !important; }
    [data-testid="column"]:last-child .stButton:nth-child(2) button { background: #ff7a00 !important; color: #fff !important; border: none !important; }
    [data-testid="column"]:last-child .stButton:nth-child(3) button { background: #00e676 !important; color: #002b15 !important; border: none !important; }
    [data-testid="column"]:last-child .stButton:nth-child(4) button { background: #2979ff !important; color: #fff !important; border: none !important; }
    [data-testid="column"]:last-child .stButton:nth-child(5) button { background: #d500f9 !important; color: #fff !important; border: none !important; }
    [data-testid="column"]:last-child .stButton:nth-child(6) button { background: #00e5ff !important; color: #002b30 !important; border: none !important; }
    [data-testid="column"]:last-child .stButton:nth-child(7) button { background: #ffea00 !important; color: #2b2500 !important; border: none !important; }
    [data-testid="column"]:last-child .stButton:nth-child(8) button { background: #ff4081 !important; color: #fff !important; border: none !important; }
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
    """Load an existing project into session state."""
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
        rag = None  # project was created without documents
 
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
    ("📅 Roadmap",       "roadmap",      "qa-roadmap"),
    ("🔍 Research Gap",  "gap",          "qa-gap"),
    ("📚 Learning Path", "learning",     "qa-learning"),
    ("🧠 Methodology",   "methodology",  "qa-methodology"),
    ("📄 Paper Intel",   "paper",        "qa-paper"),
    ("🌐 Discovery",     "discovery",    "qa-discovery"),
    ("🎓 Mentor",        "mentor",       "qa-mentor"),
    ("❓ Quiz",          "quiz",         "qa-quiz"),
]
 
 
with st.sidebar:
    st.markdown("## 🔬 ResearchEngine")
    st.markdown("---")
 
    if st.button("＋ New Project", use_container_width=True, type="primary"):
        st.session_state.show_new_project_form = True
        st.session_state.active_project_id = None
 
    st.markdown("### My Projects")
 
    all_projects = load_all_projects()
 
    if not all_projects:
        st.caption("No projects yet. Create one above.")
    else:
        for proj in all_projects:
            pid = proj["project_id"]
            label = proj["project_name"]
            is_active = (pid == st.session_state.active_project_id)
            btn_label = f"{'▶ ' if is_active else ''}{label}"
            if st.button(btn_label, key=f"proj_{pid}", use_container_width=True):
                st.session_state.show_new_project_form = False
                load_project(pid)
                st.rerun()
 
    uploaded_project_file = st.file_uploader(
        "📥 Import Project",
        type=["json"]
    )
 
    if uploaded_project_file is not None:
        try:
            imported_project_id = import_project(uploaded_project_file)
            st.success("Project imported successfully!")
            load_project(imported_project_id)
            st.rerun()
        except Exception as e:
            st.error(f"Import failed: {str(e)}")
 
 
# ── Handle triggered feature (runs in main area, keeps sidebar clean) ──
if st.session_state.triggered_feature and st.session_state.active_project_id and st.session_state.agent:
    key   = st.session_state.triggered_feature
    pid   = st.session_state.active_project_id
    graph = st.session_state.graph
 
    feature_label = next((lbl for lbl, k, _ in FEATURES if k == key), key)
 
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
 
 
# NEW PROJECT FORM
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
 
            # Process documents if any
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
 
            # Save metadata
            metadata = {
                "project_id": project_id,
                "project_name": project_name,
                "topic": topic,
                "problem_statement": problem_stmt,
                "timeline": timeline,
                "has_docs": rag is not None
            }
            save_metadata(project_id, metadata)
 
            # Load into session
            llm = get_llm()
            agent = ResearchAnalyst(rag_instance=rag, llm_instance=llm)
            agent.set_project(topic=topic, problem_statement=problem_stmt, timeline=timeline)
 
            st.session_state.active_project_id = project_id
            st.session_state.agent = agent
            st.session_state.graph = Graph(agent)
            st.session_state.active_meta = metadata
            st.session_state.show_new_project_form = False
 
            # Auto project summary as first message
            with st.spinner("Generating project summary..."):
                summary = agent.projectsummary()
            append_message(project_id, "assistant", f"**Project Summary**\n\n{summary}")
 
            st.success("Project created!")
            st.rerun()
 
 
# ACTIVE PROJECT VIEW
elif st.session_state.active_project_id and st.session_state.agent:
    pid   = st.session_state.active_project_id
    meta  = st.session_state.active_meta
    agent = st.session_state.agent
    graph = st.session_state.graph
 
    st.title(f"🔬 {meta['project_name']}")
 
    # ── 3-COLUMN LAYOUT ──
    left_col, mid_col, right_col = st.columns([1, 2.5, 1])
 
    # ════════════════════════════════
    # LEFT COLUMN — project info & export
    # ════════════════════════════════
    with left_col:
        st.markdown("#### 📋 Project Info")
        st.metric("Topic", meta["topic"][:30] + ("..." if len(meta["topic"]) > 30 else ""))
        st.metric("Timeline", meta["timeline"])
        st.metric("Docs", "Yes ✅" if meta.get("has_docs") else "No 📄")
 
        st.markdown("---")
        st.markdown("#### 📦 Backup")
        export_data = export_project(pid)
        st.download_button(
            label="📤 Export Project",
            data=export_data,
            file_name=f"{meta['project_name']}.json",
            mime="application/json",
            use_container_width=True
        )
 
    # ════════════════════════════════
    # MIDDLE COLUMN — chat
    # ════════════════════════════════
    with mid_col:
        st.markdown("### 💬 Research Chat")
 
        messages = load_chat_history(pid)
        for msg in messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
 
    # ════════════════════════════════
    # RIGHT COLUMN — quick actions
    # ════════════════════════════════
    with right_col:
        st.markdown("#### ⚡ Quick Actions")
        for label, key, css_class in FEATURES:
            if st.button(label, key=f"qa_{key}", use_container_width=True):
                st.session_state.triggered_feature = key
                st.rerun()
 
    # ── CHAT INPUT (page-level — Streamlit requires this outside columns) ──
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
 
 
# ── LANDING / EMPTY STATE ──
else:
    st.markdown("""
    <div style="text-align:center; padding: 80px 40px;">
        <h1>🔬 ResearchEngine</h1>
        <p style="font-size:1.2rem; color:#888;">
            Your AI-powered research mentor. Create a project to get started.
        </p>
        <br>
        <p style="color:#555;">
            ← Click <strong>＋ New Project</strong> in the sidebar
        </p>
    </div>
    """, unsafe_allow_html=True)
