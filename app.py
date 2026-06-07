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
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
 
    def build_vectordb(self):
        self.vectorstore = FAISS.from_documents(self.chunks, self.embeddings)
 
    def save_vectordb(self, project_id):
        faiss_path = get_faiss_path(project_id)
        os.makedirs(faiss_path, exist_ok=True)
        self.vectorstore.save_local(faiss_path)
 
    def load_vectordb(self, project_id):
        faiss_path = get_faiss_path(project_id)
        if os.path.exists(faiss_path):
            self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
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
 
    # ── feature methods (unchanged) ──
 
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
Be detailed and practical.
"""
        return self.llm.invoke(prompt).content
 
    # ── NEW: free-form chat method ──
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
    [data-testid="stSidebar"] { background: #0f1117; }
    .project-card {
        background: #1e2130;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 8px;
        cursor: pointer;
        border-left: 3px solid #4f8ef7;
    }
    .project-card:hover { background: #252a40; }
    .stChatMessage { border-radius: 10px; }
</style>
""", unsafe_allow_html=True)
 
 
# ── LLM (shared, cached) ──
@st.cache_resource
def get_llm():
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.6)
 
 
# ── Session state defaults ──
if "active_project_id" not in st.session_state:
    st.session_state.active_project_id = None
if "agent" not in st.session_state:
    st.session_state.agent = None
if "graph" not in st.session_state:
    st.session_state.graph = None
if "show_new_project_form" not in st.session_state:
    st.session_state.show_new_project_form = False
 
 
def load_project(project_id):
    """Load an existing project into session state."""
    meta_path = get_metadata_path(project_id)
    if not os.path.exists(meta_path):
        st.error("Project not found.")
        return
 
    with open(meta_path) as f:
        meta = json.load(f)
 
    rag = RAG()
    has_docs = rag.load_vectordb(project_id)
    if not has_docs:
        rag = None   # project was created without documents
 
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
 
    col1, col2, col3 = st.columns(3)
    col1.metric("Topic", meta["topic"][:40] + ("..." if len(meta["topic"]) > 40 else ""))
    col2.metric("Timeline", meta["timeline"])
    col3.metric("Docs", "Yes ✅" if meta.get("has_docs") else "No 📄")
 
    st.markdown("---")
 
    # ── FEATURE BUTTONS ──
    st.markdown("### ⚡ Quick Actions")
    cols = st.columns(4)
    features = [
        ("📅 Roadmap",       "roadmap"),
        ("🔍 Research Gap",  "gap"),
        ("📚 Learning Path", "learning"),
        ("🧠 Methodology",   "methodology"),
        ("📄 Paper Intel",   "paper"),
        ("🌐 Discovery",     "discovery"),
        ("🎓 Mentor",        "mentor"),
        ("❓ Quiz",          "quiz"),
    ]
    for i, (label, key) in enumerate(features):
        if cols[i % 4].button(label, key=f"feat_{key}", use_container_width=True):
            with st.spinner(f"Generating {label}..."):
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
            append_message(pid, "user", f"Generate: {label}")
            append_message(pid, "assistant", answer)
            st.rerun()
 
    st.markdown("---")
    st.markdown("### 💬 Research Chat")
 
    # ── DISPLAY CHAT HISTORY ──
    messages = load_chat_history(pid)
    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
 
    # ── CHAT INPUT ──
    prompt = st.chat_input("Ask your research mentor anything...")
 
    if prompt:
        # Show user message immediately
        with st.chat_message("user"):
            st.markdown(prompt)
 
        # Save user message
        messages = append_message(pid, "user", prompt)
 
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = agent.chat(prompt, messages)
            st.markdown(response)
 
        # Save assistant response
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
