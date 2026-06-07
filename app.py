import warnings
warnings.filterwarnings("ignore")

import os
import json
import uuid
from datetime import datetime
import tempfile

from dotenv import load_dotenv

load_dotenv()

import streamlit as st

from langchain_community.document_loaders import PyMuPDFLoader, TextLoader, CSVLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

# ==================== PROJECT MANAGEMENT ====================
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
    return sorted(projects, key=lambda x: x.get("created_at", ""), reverse=True)

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
    metadata["imported_from"] = metadata.get("project_name", "Unknown")

    os.makedirs(get_project_path(new_project_id), exist_ok=True)
    save_metadata(new_project_id, metadata)
    save_chat_history(new_project_id, chat_history)

    return new_project_id

# ==================== RAG CLASS ====================
class RAG:
    def __init__(self):
        self.documents = None
        self.chunks = None
        self.embeddings = None
        self.vectorstore = None

    def load_data_from_files(self, uploaded_files, project_id):
        self.documents = []
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

# ==================== RESEARCH ANALYST ====================
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

    def quizgenerator_json(self):
        context = self._get_context()
        prompt = f"""
You are an expert research mentor.
Topic: {self.topic}
Problem Statement: {self.problem_statement}
Relevant Research Context: {context}

Generate exactly 5 multiple choice questions to test understanding of this research topic.

Return ONLY valid JSON in this exact format:
{{
  "questions": [
    {{
      "question": "What is overfitting?",
      "options": [
        "Model memorizes training data",
        "Model generalizes well",
        "Feature scaling technique",
        "Data cleaning method"
      ],
      "answer": 0,
      "explanation": "Overfitting occurs when a model learns training data too well, including noise."
    }}
  ]
}}

Make questions challenging but fair. Ensure answer is the index (0-3) of the correct option.
"""
        response = self.llm.invoke(prompt).content
        try:
            # Extract JSON from response
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = response[start:end]
                return json.loads(json_str)
        except:
            pass
        # Fallback
        return {"questions": []}

    def flashcards_json(self):
        context = self._get_context()
        prompt = f"""
You are an expert research mentor.
Topic: {self.topic}
Problem Statement: {self.problem_statement}
Relevant Research Context: {context}

Generate exactly 8 flashcards for key concepts in this research area.

Return ONLY valid JSON in this exact format:
{{
  "flashcards": [
    {{
      "front": "CNN",
      "back": "Convolutional Neural Network - a deep learning architecture for processing grid-like data such as images."
    }}
  ]
}}

Make flashcards educational and comprehensive.
"""
        response = self.llm.invoke(prompt).content
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = response[start:end]
                return json.loads(json_str)
        except:
            pass
        return {"flashcards": []}

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

# ==================== GRAPH CLASS ====================
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

# ==================== LLM & EMBEDDINGS ====================
@st.cache_resource
def get_llm():
    return ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0.6)

@st.cache_resource
def load_cached_faiss(project_id):
    rag = RAG()
    rag.load_vectordb(project_id)
    return rag

@st.cache_resource
def get_embeddings():
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# ==================== THEME CSS ====================
def apply_theme():
    theme = st.session_state.get("theme", "dark")
    
    if theme == "light":
        st.markdown("""
        <style>
        /* Light Mode - Pastel Aesthetic */
        .stApp {
            background: #FFF8FC;
        }
        [data-testid="stAppViewContainer"] {
            background: #FFF8FC;
        }
        .main-panel, [data-testid="stVerticalBlock"] {
            background: transparent;
        }
        .project-card {
            background: #F5EFFF;
            border-radius: 18px;
            padding: 12px 16px;
            margin-bottom: 12px;
            cursor: pointer;
            border: 1px solid #FFB7D5;
            transition: all 0.2s ease;
            box-shadow: 0 2px 6px rgba(0,0,0,0.03);
        }
        .project-card:hover {
            background: #FFF4F7;
            transform: translateX(4px);
            border-color: #C8A2FF;
            box-shadow: 0 4px 12px rgba(200,162,255,0.15);
        }
        .project-card.active {
            background: #E8D5FF;
            border-left: 4px solid #C8A2FF;
            border-color: #C8A2FF;
        }
        .project-card-title {
            font-weight: 600;
            font-size: 1rem;
            color: #5A3E8A;
            margin-bottom: 4px;
        }
        .project-card-date {
            font-size: 0.7rem;
            color: #9B7FC9;
        }
        .metadata-card {
            background: #F5EFFF;
            border-radius: 18px;
            padding: 20px;
            margin-bottom: 20px;
            border: 1px solid #FFB7D5;
            box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        }
        .chat-message-user {
            background: #E8D5FF;
            border-radius: 18px;
            padding: 12px 16px;
            margin-bottom: 12px;
            max-width: 85%;
            margin-left: auto;
            border-bottom-right-radius: 4px;
            color: #3A2A5E;
        }
        .chat-message-assistant {
            background: #FFF4F7;
            border-radius: 18px;
            padding: 12px 16px;
            margin-bottom: 12px;
            max-width: 85%;
            margin-right: auto;
            border-bottom-left-radius: 4px;
            border: 1px solid #FFB7D5;
            color: #4A3A6E;
        }
        .quick-actions-panel {
            background: #F5EFFF;
            border-radius: 18px;
            padding: 16px;
            border: 1px solid #FFB7D5;
            box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        }
        .stButton button {
            border-radius: 40px;
            transition: all 0.2s ease;
        }
        .stButton button:hover {
            transform: translateY(-2px);
        }
        h1, h2, h3, p, span, label {
            color: #4A3A6E;
        }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        /* Dark Mode - Cyber Neon Aesthetic */
        .stApp {
            background: #0D1117;
        }
        [data-testid="stAppViewContainer"] {
            background: #0D1117;
        }
        .main-panel, [data-testid="stVerticalBlock"] {
            background: transparent;
        }
        .project-card {
            background: #111827;
            border-radius: 18px;
            padding: 12px 16px;
            margin-bottom: 12px;
            cursor: pointer;
            border: 1px solid #00FFFF;
            transition: all 0.2s ease;
            box-shadow: 0 0 5px rgba(0,255,255,0.1);
        }
        .project-card:hover {
            background: #1A2335;
            transform: translateX(4px);
            box-shadow: 0 0 12px #00FFFF;
            border-color: #FF00FF;
        }
        .project-card.active {
            background: #1A0B2E;
            border-left: 4px solid #FF00FF;
            box-shadow: 0 0 15px #FF00FF;
        }
        .project-card-title {
            font-weight: 600;
            font-size: 1rem;
            color: #39FF14;
            margin-bottom: 4px;
        }
        .project-card-date {
            font-size: 0.7rem;
            color: #00FFFF;
        }
        .metadata-card {
            background: #111827;
            border-radius: 18px;
            padding: 20px;
            margin-bottom: 20px;
            border: 1px solid #00FFFF;
            box-shadow: 0 0 10px rgba(0,255,255,0.2);
        }
        .chat-message-user {
            background: #FF00FF20;
            border-radius: 18px;
            padding: 12px 16px;
            margin-bottom: 12px;
            max-width: 85%;
            margin-left: auto;
            border-bottom-right-radius: 4px;
            border: 1px solid #FF00FF;
            color: #E0E0E0;
        }
        .chat-message-assistant {
            background: #00FFFF10;
            border-radius: 18px;
            padding: 12px 16px;
            margin-bottom: 12px;
            max-width: 85%;
            margin-right: auto;
            border-bottom-left-radius: 4px;
            border: 1px solid #00FFFF;
            color: #E0E0E0;
        }
        .quick-actions-panel {
            background: #111827;
            border-radius: 18px;
            padding: 16px;
            border: 1px solid #00FFFF;
            box-shadow: 0 0 10px rgba(0,255,255,0.2);
        }
        .stButton button {
            border-radius: 40px;
            transition: all 0.2s ease;
        }
        .stButton button:hover {
            transform: translateY(-2px);
            box-shadow: 0 0 8px #39FF14;
        }
        h1, h2, h3, p, span, label {
            color: #E0E0E0;
        }
        </style>
        """, unsafe_allow_html=True)

# ==================== SESSION STATE INIT ====================
if "active_project_id" not in st.session_state:
    st.session_state.active_project_id = None
if "agent" not in st.session_state:
    st.session_state.agent = None
if "graph" not in st.session_state:
    st.session_state.graph = None
if "show_new_project_form" not in st.session_state:
    st.session_state.show_new_project_form = False
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "quiz_index" not in st.session_state:
    st.session_state.quiz_index = 0
if "quiz_score" not in st.session_state:
    st.session_state.quiz_score = 0
if "quiz_complete" not in st.session_state:
    st.session_state.quiz_complete = False
if "quiz_answer_submitted" not in st.session_state:
    st.session_state.quiz_answer_submitted = False
if "quiz_selected_answer" not in st.session_state:
    st.session_state.quiz_selected_answer = None
if "flashcards" not in st.session_state:
    st.session_state.flashcards = None
if "flashcard_index" not in st.session_state:
    st.session_state.flashcard_index = 0
if "flashcard_showing_back" not in st.session_state:
    st.session_state.flashcard_showing_back = False

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

# ==================== QUIZ RENDERER ====================
def render_quiz():
    if st.session_state.quiz_complete:
        st.success(f"🎉 Quiz Complete!\n\nScore: {st.session_state.quiz_score}/{len(st.session_state.quiz_data.get('questions', []))}")
        if st.button("📝 Take Quiz Again"):
            st.session_state.quiz_complete = False
            st.session_state.quiz_index = 0
            st.session_state.quiz_score = 0
            st.session_state.quiz_answer_submitted = False
            st.session_state.quiz_selected_answer = None
            st.rerun()
        return

    questions = st.session_state.quiz_data.get("questions", [])
    if not questions:
        st.warning("No quiz questions available.")
        return

    if st.session_state.quiz_index >= len(questions):
        st.session_state.quiz_complete = True
        st.rerun()
        return

    q = questions[st.session_state.quiz_index]
    
    st.markdown(f"**Question {st.session_state.quiz_index + 1} of {len(questions)}**")
    st.markdown(f"### {q['question']}")
    
    if not st.session_state.quiz_answer_submitted:
        selected = st.radio("Select your answer:", q['options'], key=f"q_{st.session_state.quiz_index}")
        if st.button("✅ Submit Answer"):
            correct_idx = q['answer']
            is_correct = (selected == q['options'][correct_idx])
            if is_correct:
                st.session_state.quiz_score += 1
                st.success("✅ Correct!")
            else:
                st.error(f"❌ Incorrect. The correct answer is: {q['options'][correct_idx]}")
            st.info(f"📖 Explanation: {q['explanation']}")
            st.session_state.quiz_answer_submitted = True
            st.session_state.quiz_selected_answer = selected
            st.rerun()
    else:
        st.info(f"You selected: {st.session_state.quiz_selected_answer}")
        if st.button("➡️ Next Question"):
            st.session_state.quiz_index += 1
            st.session_state.quiz_answer_submitted = False
            st.session_state.quiz_selected_answer = None
            st.rerun()

# ==================== FLASHCARD RENDERER ====================
def render_flashcards():
    flashcards = st.session_state.flashcards.get("flashcards", [])
    if not flashcards:
        st.warning("No flashcards available.")
        return
    
    total = len(flashcards)
    current = st.session_state.flashcard_index
    card = flashcards[current]
    
    st.markdown(f"**Card {current + 1} of {total}**")
    
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown("---")
        if not st.session_state.flashcard_showing_back:
            st.markdown(f"### 📇 {card['front']}")
            if st.button("🔍 Show Answer", use_container_width=True):
                st.session_state.flashcard_showing_back = True
                st.rerun()
        else:
            st.markdown(f"### 📖 {card['back']}")
            if st.button("🙈 Hide Answer", use_container_width=True):
                st.session_state.flashcard_showing_back = False
                st.rerun()
        st.markdown("---")
    
    col_prev, col_next = st.columns(2)
    with col_prev:
        if current > 0:
            if st.button("◀ Previous", use_container_width=True):
                st.session_state.flashcard_index -= 1
                st.session_state.flashcard_showing_back = False
                st.rerun()
    with col_next:
        if current < total - 1:
            if st.button("Next ▶", use_container_width=True):
                st.session_state.flashcard_index += 1
                st.session_state.flashcard_showing_back = False
                st.rerun()

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="ResearchEngine",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

apply_theme()

# ==================== THEME TOGGLE ====================
theme_col1, theme_col2 = st.columns([6, 1])
with theme_col2:
    if st.button("🌙" if st.session_state.theme == "light" else "☀️"):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()

# ==================== THREE PANEL LAYOUT ====================
left_panel, center_panel, right_panel = st.columns([1.3, 4.8, 1.6])

# ==================== LEFT PANEL ====================
with left_panel:
    st.markdown("## 🔬 ResearchEngine")
    st.markdown("---")
    
    if st.button("➕ New Project", use_container_width=True, type="primary"):
        st.session_state.show_new_project_form = True
        st.session_state.active_project_id = None
    
    st.markdown("---")
    
    st.markdown("### 📥 Import / Export")
    uploaded_project_file = st.file_uploader("Import Project", type=["json"], key="import_uploader")
    if uploaded_project_file is not None:
        try:
            imported_project_id = import_project(uploaded_project_file)
            st.success("Project imported!")
            load_project(imported_project_id)
            st.rerun()
        except Exception as e:
            st.error(f"Import failed: {str(e)}")
    
    if st.session_state.active_project_id:
        pid = st.session_state.active_project_id
        meta = st.session_state.active_meta
        export_data = export_project(pid)
        st.download_button(
            label="📤 Export Project",
            data=export_data,
            file_name=f"{meta['project_name']}.json",
            mime="application/json",
            use_container_width=True
        )
    
    st.markdown("---")
    st.markdown("### 📂 Project History")
    
    all_projects = load_all_projects()
    if not all_projects:
        st.caption("No projects yet. Create one above.")
    else:
        for proj in all_projects:
            pid = proj["project_id"]
            is_active = (pid == st.session_state.active_project_id)
            active_class = "active" if is_active else ""
            st.markdown(f"""
            <div class="project-card {active_class}" onclick="alert('load')">
                <div class="project-card-title">{proj['project_name'][:30]}</div>
                <div class="project-card-date">{proj.get('created_at', 'Unknown date')}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Open", key=f"open_{pid}", use_container_width=True):
                st.session_state.show_new_project_form = False
                load_project(pid)
                st.rerun()

# ==================== NEW PROJECT FORM ====================
if st.session_state.show_new_project_form:
    with center_panel:
        st.title("✨ Create New Project")
        with st.form("new_project_form"):
            project_name = st.text_input("Project Name", placeholder="e.g. Crime Hotspot Analysis")
            topic = st.text_input("Research Topic", placeholder="e.g. Urban Crime Prediction using ML")
            problem_stmt = st.text_area("Problem Statement", placeholder="Describe what you're solving...")
            timeline = st.text_input("Timeline", placeholder="e.g. 8 weeks")
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
                resource_names = []
                if uploaded_files:
                    with st.spinner("Processing documents..."):
                        rag = RAG()
                        rag.load_data_from_files(uploaded_files, project_id)
                        rag.chunking()
                        rag.embedding()
                        rag.build_vectordb()
                        rag.save_vectordb(project_id)
                        resource_names = [f.name for f in uploaded_files]
                    st.success(f"Loaded {len(rag.documents)} document pages.")
                
                metadata = {
                    "project_id": project_id,
                    "project_name": project_name,
                    "topic": topic,
                    "problem_statement": problem_stmt,
                    "timeline": timeline,
                    "created_at": datetime.now().strftime("%d %b %Y"),
                    "resources": resource_names,
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

# ==================== CENTER PANEL ====================
elif st.session_state.active_project_id and st.session_state.agent:
    pid = st.session_state.active_project_id
    meta = st.session_state.active_meta
    agent = st.session_state.agent
    
    with center_panel:
        # Metadata Card
        st.markdown(f"""
        <div class="metadata-card">
            <h2>🔬 {meta['project_name']}</h2>
            <p><strong>📅 Timeline:</strong> {meta['timeline']}</p>
            <p><strong>🗓 Created:</strong> {meta.get('created_at', 'Unknown')}</p>
            <p><strong>📚 Topic:</strong> {meta['topic']}</p>
            <p><strong>📄 Resources:</strong> {', '.join(meta.get('resources', [])) if meta.get('resources') else 'No documents uploaded'}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 💬 Research Chat")
        
        # Chat History
        messages = load_chat_history(pid)
        chat_container = st.container()
        with chat_container:
            for msg in messages:
                if msg["role"] == "user":
                    st.markdown(f'<div class="chat-message-user">🗣️ {msg["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-message-assistant">🤖 {msg["content"]}</div>', unsafe_allow_html=True)
        
        # Chat Input
        prompt = st.chat_input("Ask your research mentor anything...")
        if prompt:
            with st.chat_message("user"):
                st.markdown(prompt)
            messages = append_message(pid, "user", prompt)
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = agent.chat(prompt, messages)
                st.markdown(response)
            append_message(pid, "assistant", response)
            st.rerun()
    
    # ==================== RIGHT PANEL ====================
    with right_panel:
        st.markdown("""
        <div class="quick-actions-panel">
            <h3 style="margin-top:0;">⚡ Quick Actions</h3>
        </div>
        """, unsafe_allow_html=True)
        
        actions = [
            ("📅 Roadmap", "roadmap"),
            ("🔍 Research Gap", "gap"),
            ("📚 Learning Path", "learning"),
            ("🧠 Methodology", "methodology"),
            ("📄 Paper Intelligence", "paper"),
            ("🌐 Research Discovery", "discovery"),
            ("🎓 Research Mentor", "mentor"),
            ("❓ Interactive Quiz", "quiz"),
            ("🃏 Interactive Flashcards", "flashcards"),
        ]
        
        for label, key in actions:
            if st.button(label, key=f"action_{key}", use_container_width=True):
                if key == "quiz":
                    with st.spinner("Generating quiz..."):
                        quiz_json = agent.quizgenerator_json()
                        st.session_state.quiz_data = quiz_json
                        st.session_state.quiz_index = 0
                        st.session_state.quiz_score = 0
                        st.session_state.quiz_complete = False
                        st.session_state.quiz_answer_submitted = False
                        st.session_state.quiz_selected_answer = None
                    st.rerun()
                elif key == "flashcards":
                    with st.spinner("Generating flashcards..."):
                        flashcards_json = agent.flashcards_json()
                        st.session_state.flashcards = flashcards_json
                        st.session_state.flashcard_index = 0
                        st.session_state.flashcard_showing_back = False
                    st.rerun()
                else:
                    with st.spinner(f"Generating {label}..."):
                        state = {}
                        if key == "roadmap":
                            state = st.session_state.graph.roadmap_node(state)
                        elif key == "gap":
                            state = st.session_state.graph.researchgap_node(state)
                        elif key == "learning":
                            state = st.session_state.graph.learning_node(state)
                        elif key == "methodology":
                            state = st.session_state.graph.methodology_node(state)
                        elif key == "paper":
                            state = st.session_state.graph.paperintelligence_node(state)
                        elif key == "discovery":
                            state = st.session_state.graph.researchdiscovery_node(state)
                        elif key == "mentor":
                            state = st.session_state.graph.researchmentor_node(state)
                        answer = state.get("answer", "")
                    append_message(pid, "user", f"Generate: {label}")
                    append_message(pid, "assistant", answer)
                    st.rerun()
        
        # Quiz Display
        if st.session_state.quiz_data and st.session_state.quiz_data.get("questions"):
            st.markdown("---")
            st.markdown("### ❓ Active Quiz")
            render_quiz()
        
        # Flashcards Display
        if st.session_state.flashcards and st.session_state.flashcards.get("flashcards"):
            st.markdown("---")
            st.markdown("### 🃏 Active Flashcards")
            render_flashcards()

# ==================== LANDING PAGE ====================
else:
    st.markdown("""
    <div style="text-align:center; padding: 80px 40px;">
        <h1>🔬 ResearchEngine</h1>
        <p style="font-size:1.2rem; color:#888;">
            Your AI-powered research mentor. Create a project to get started.
        </p>
        <br>
        <p style="color:#555;">
            ← Click <strong>➕ New Project</strong> in the left panel
        </p>
    </div>
    """, unsafe_allow_html=True)
