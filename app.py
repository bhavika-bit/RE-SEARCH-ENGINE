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
6. Generate learning resources.

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
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = response[start:end]
                return json.loads(json_str)
        except:
            pass
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
9. Generate learning resources.

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
10. Generate learning resources.

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
3. Idea feasibility
4. Generate learning resources.

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
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")


# Session state defaults
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
if "weak_topics" not in st.session_state:
    st.session_state.weak_topics = []
if "strong_topics" not in st.session_state:
    st.session_state.strong_topics = []
if "flashcards" not in st.session_state:
    st.session_state.flashcards = None
if "flashcard_index" not in st.session_state:
    st.session_state.flashcard_index = 0
if "flashcard_showing_back" not in st.session_state:
    st.session_state.flashcard_showing_back = False
if "flashcard_mastered" not in st.session_state:
    st.session_state.flashcard_mastered = set()
if "flashcard_review" not in st.session_state:
    st.session_state.flashcard_review = set()
if "quiz_mode" not in st.session_state:
    st.session_state.quiz_mode = None  # 'quiz' or 'flashcards'


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


def render_quiz():
    st.markdown("### 📝 Interactive Quiz")
    
    if st.session_state.quiz_complete:
        total = len(st.session_state.quiz_data.get("questions", []))
        score = st.session_state.quiz_score
        percentage = (score / total) * 100 if total > 0 else 0
        
        st.balloons()
        st.success(f"🎉 Quiz Complete!\n\n**Score: {score}/{total} ({percentage:.0f}%)**")
        
        # Show weak topics based on incorrect answers
        if st.session_state.weak_topics:
            st.markdown("### 📚 Topics to Review")
            for topic in st.session_state.weak_topics:
                st.warning(f"⚠️ {topic}")
        
        if st.session_state.strong_topics:
            st.markdown("### ✅ Topics You've Mastered")
            for topic in st.session_state.strong_topics:
                st.success(f"✓ {topic}")
        
        if st.button("🔄 Take Quiz Again", use_container_width=True):
            st.session_state.quiz_complete = False
            st.session_state.quiz_index = 0
            st.session_state.quiz_score = 0
            st.session_state.quiz_answer_submitted = False
            st.session_state.quiz_selected_answer = None
            st.session_state.weak_topics = []
            st.session_state.strong_topics = []
            st.rerun()
        return

    questions = st.session_state.quiz_data.get("questions", [])
    if not questions:
        st.warning("No quiz questions available. Generate a quiz first.")
        return

    if st.session_state.quiz_index >= len(questions):
        st.session_state.quiz_complete = True
        st.rerun()
        return

    q = questions[st.session_state.quiz_index]
    
    # Progress bar
    progress = (st.session_state.quiz_index) / len(questions)
    st.progress(progress, text=f"Question {st.session_state.quiz_index + 1} of {len(questions)}")
    
    st.markdown(f"### {q['question']}")
    
    if not st.session_state.quiz_answer_submitted:
        selected = st.radio("Select your answer:", q['options'], key=f"q_{st.session_state.quiz_index}", index=None)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Submit Answer", use_container_width=True, type="primary"):
                if selected is None:
                    st.error("Please select an answer!")
                else:
                    correct_idx = q['answer']
                    is_correct = (selected == q['options'][correct_idx])
                    
                    if is_correct:
                        st.session_state.quiz_score += 1
                        st.success("✅ Correct! Great job!")
                    else:
                        st.error(f"❌ Incorrect. The correct answer is: {q['options'][correct_idx]}")
                        # Track weak topic
                        topic = q.get('topic', 'General Concept')
                        if topic not in st.session_state.weak_topics:
                            st.session_state.weak_topics.append(topic)
                    
                    st.info(f"📖 **Explanation:** {q['explanation']}")
                    st.session_state.quiz_answer_submitted = True
                    st.session_state.quiz_selected_answer = selected
                    st.rerun()
    else:
        st.info(f"You selected: {st.session_state.quiz_selected_answer}")
        if st.button("➡️ Next Question", use_container_width=True, type="primary"):
            st.session_state.quiz_index += 1
            st.session_state.quiz_answer_submitted = False
            st.session_state.quiz_selected_answer = None
            st.rerun()


def render_flashcards():
    st.markdown("### 🃏 Interactive Flashcards")
    
    flashcards = st.session_state.flashcards.get("flashcards", [])
    if not flashcards:
        st.warning("No flashcards available. Generate flashcards first.")
        return
    
    # Filter out mastered cards if needed
    active_cards = [i for i in range(len(flashcards)) if i not in st.session_state.flashcard_mastered]
    
    if not active_cards:
        st.success("🎉 Congratulations! You've mastered all flashcards!")
        if st.button("🔄 Reset All Flashcards", use_container_width=True):
            st.session_state.flashcard_mastered = set()
            st.session_state.flashcard_review = set()
            st.session_state.flashcard_index = 0
            st.rerun()
        return
    
    # Adjust index if current card is mastered
    if st.session_state.flashcard_index in st.session_state.flashcard_mastered:
        st.session_state.flashcard_index = active_cards[0]
    
    total = len(active_cards)
    current_pos = active_cards.index(st.session_state.flashcard_index) if st.session_state.flashcard_index in active_cards else 0
    current_card_index = active_cards[current_pos]
    card = flashcards[current_card_index]
    
    # Progress
    mastered_count = len(st.session_state.flashcard_mastered)
    st.progress(mastered_count / len(flashcards), text=f"Mastered: {mastered_count}/{len(flashcards)}")
    
    st.markdown(f"**Card {current_pos + 1} of {total}**")
    
    # Flashcard display
    st.markdown("---")
    if not st.session_state.flashcard_showing_back:
        st.markdown(f"### 📇 {card['front']}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Show Answer", use_container_width=True):
                st.session_state.flashcard_showing_back = True
                st.rerun()
    else:
        st.markdown(f"### 📖 {card['back']}")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("✅ I Know It", use_container_width=True, type="primary"):
                st.session_state.flashcard_mastered.add(current_card_index)
                if current_card_index in st.session_state.flashcard_review:
                    st.session_state.flashcard_review.discard(current_card_index)
                # Move to next card
                remaining = [i for i in active_cards if i not in st.session_state.flashcard_mastered]
                if remaining:
                    st.session_state.flashcard_index = remaining[0]
                st.session_state.flashcard_showing_back = False
                st.rerun()
        with col2:
            if st.button("🔄 Need Review", use_container_width=True):
                st.session_state.flashcard_review.add(current_card_index)
                # Move to next card
                remaining = [i for i in active_cards if i not in st.session_state.flashcard_mastered]
                if remaining:
                    next_idx = (current_pos + 1) % len(remaining) if len(remaining) > 1 else remaining[0]
                    st.session_state.flashcard_index = remaining[next_idx] if next_idx < len(remaining) else remaining[0]
                st.session_state.flashcard_showing_back = False
                st.rerun()
        with col3:
            if st.button("🙈 Hide Answer", use_container_width=True):
                st.session_state.flashcard_showing_back = False
                st.rerun()
    
    st.markdown("---")
    
    # Navigation
    col_prev, col_info, col_next = st.columns([1, 2, 1])
    with col_prev:
        if current_pos > 0:
            if st.button("◀ Previous", use_container_width=True):
                st.session_state.flashcard_index = active_cards[current_pos - 1]
                st.session_state.flashcard_showing_back = False
                st.rerun()
    with col_info:
        st.markdown(f"<p style='text-align:center'>Card {current_pos + 1} of {total}</p>", unsafe_allow_html=True)
    with col_next:
        if current_pos < total - 1:
            if st.button("Next ▶", use_container_width=True):
                st.session_state.flashcard_index = active_cards[current_pos + 1]
                st.session_state.flashcard_showing_back = False
                st.rerun()
    
    # Review section
    if st.session_state.flashcard_review:
        st.markdown("---")
        st.markdown("### 🔄 Cards to Review")
        for idx in st.session_state.flashcard_review:
            st.info(f"📌 {flashcards[idx]['front']}")
        
        if st.button("Review Weak Cards", use_container_width=True):
            if st.session_state.flashcard_review:
                st.session_state.flashcard_index = list(st.session_state.flashcard_review)[0]
                st.session_state.flashcard_showing_back = False
                st.rerun()


# Page config
st.set_page_config(
    page_title="ResearchEngine",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Theme CSS
def apply_theme():
    theme = st.session_state.theme
    
    if theme == "light":
        st.markdown("""
        <style>
        /* Light Mode - Pastel Aesthetic */
        .stApp {
            background: linear-gradient(135deg, #FFF8FC 0%, #FDF4F8 100%);
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #F5EFFF 0%, #EBE4F5 100%);
            border-right: 2px solid #FFB7D5;
        }
        .project-card {
            background: #FFFFFF;
            border-radius: 16px;
            padding: 12px 16px;
            margin-bottom: 10px;
            cursor: pointer;
            border: 1px solid #FFD6E8;
            transition: all 0.2s ease;
            box-shadow: 0 2px 8px rgba(255,183,213,0.1);
        }
        .project-card:hover {
            background: #FFF4F7;
            transform: translateX(5px);
            border-color: #C8A2FF;
            box-shadow: 0 4px 15px rgba(200,162,255,0.15);
        }
        .project-card.active {
            background: #E8D5FF;
            border-left: 4px solid #C8A2FF;
            border-color: #C8A2FF;
        }
        .project-card-title {
            font-weight: 600;
            font-size: 1rem;
            color: #6B4E9E;
            margin-bottom: 4px;
        }
        .project-card-date {
            font-size: 0.7rem;
            color: #B89BD6;
        }
        .stButton button {
            border-radius: 30px;
            transition: all 0.2s ease;
            font-weight: 500;
        }
        .stButton button:hover {
            transform: translateY(-2px);
        }
        .stTextInput input, .stTextArea textarea {
            border-radius: 12px;
            border: 1px solid #FFD6E8;
        }
        h1, h2, h3, p, span, label {
            color: #5A4A7A;
        }
        .chat-message-user {
            background: linear-gradient(135deg, #E8D5FF 0%, #DEC9F5 100%);
            border-radius: 20px;
            padding: 12px 18px;
            margin-bottom: 12px;
            max-width: 80%;
            margin-left: auto;
            color: #3A2A5E;
        }
        .chat-message-assistant {
            background: #FFFFFF;
            border-radius: 20px;
            padding: 12px 18px;
            margin-bottom: 12px;
            max-width: 80%;
            margin-right: auto;
            border: 1px solid #FFD6E8;
            color: #5A4A7A;
        }
        div[data-testid="stProgress"] > div > div > div > div {
            background-color: #C8A2FF;
        }
        .stAlert {
            border-radius: 12px;
        }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        /* Dark Mode - Vibrant Cyber Neon */
        .stApp {
            background: linear-gradient(135deg, #0D0F1A 0%, #0A0C16 100%);
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #11131F 0%, #0D0F1A 100%);
            border-right: 2px solid #00FFFF;
            box-shadow: 0 0 20px rgba(0,255,255,0.1);
        }
        .project-card {
            background: #161A2D;
            border-radius: 16px;
            padding: 12px 16px;
            margin-bottom: 10px;
            cursor: pointer;
            border: 1px solid #00FFFF;
            transition: all 0.2s ease;
            box-shadow: 0 0 8px rgba(0,255,255,0.1);
        }
        .project-card:hover {
            background: #1E2340;
            transform: translateX(5px);
            box-shadow: 0 0 20px #00FFFF;
            border-color: #FF00FF;
        }
        .project-card.active {
            background: #2A1B4E;
            border-left: 4px solid #FF00FF;
            box-shadow: 0 0 20px #FF00FF;
        }
        .project-card-title {
            font-weight: 600;
            font-size: 1rem;
            color: #39FF14;
            margin-bottom: 4px;
            text-shadow: 0 0 5px #39FF14;
        }
        .project-card-date {
            font-size: 0.7rem;
            color: #00FFFF;
        }
        .stButton button {
            border-radius: 30px;
            transition: all 0.2s ease;
            font-weight: 500;
        }
        .stButton button:hover {
            transform: translateY(-2px);
            box-shadow: 0 0 15px #00FFFF;
        }
        .stTextInput input, .stTextArea textarea {
            border-radius: 12px;
            background: #161A2D;
            border: 1px solid #00FFFF;
            color: #E0E0E0;
        }
        h1, h2, h3, p, span, label {
            color: #E0E0E0;
        }
        .chat-message-user {
            background: linear-gradient(135deg, #FF00FF20 0%, #FF00FF10 100%);
            border-radius: 20px;
            padding: 12px 18px;
            margin-bottom: 12px;
            max-width: 80%;
            margin-left: auto;
            border: 1px solid #FF00FF;
            color: #E0E0E0;
        }
        .chat-message-assistant {
            background: #161A2D;
            border-radius: 20px;
            padding: 12px 18px;
            margin-bottom: 12px;
            max-width: 80%;
            margin-right: auto;
            border: 1px solid #00FFFF;
            color: #E0E0E0;
        }
        div[data-testid="stProgress"] > div > div > div > div {
            background: linear-gradient(90deg, #00FFFF, #FF00FF);
        }
        .stAlert {
            border-radius: 12px;
            border: 1px solid #00FFFF;
        }
        </style>
        """, unsafe_allow_html=True)

apply_theme()

# Sidebar
with st.sidebar:
    st.markdown("# 🔬 ResearchEngine")
    st.markdown("---")
    
    # Theme toggle
    theme_label = "☀️ Light Mode" if st.session_state.theme == "dark" else "🌙 Dark Mode"
    if st.button(theme_label, use_container_width=True):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()
    
    st.markdown("---")
    
    if st.button("➕ New Project", use_container_width=True, type="primary"):
        st.session_state.show_new_project_form = True
        st.session_state.active_project_id = None
    
    st.markdown("### 📁 My Projects")
    
    all_projects = load_all_projects()
    
    if not all_projects:
        st.caption("✨ No projects yet. Create one above.")
    else:
        for proj in all_projects:
            pid = proj["project_id"]
            label = proj["project_name"]
            is_active = (pid == st.session_state.active_project_id)
            
            if is_active:
                st.markdown(f"""
                <div class="project-card active">
                    <div class="project-card-title">▶ {label}</div>
                    <div class="project-card-date">{proj.get('created_at', 'Unknown')}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="project-card">
                    <div class="project-card-title">{label}</div>
                    <div class="project-card-date">{proj.get('created_at', 'Unknown')}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Open", key=f"open_{pid}", use_container_width=True):
                    st.session_state.show_new_project_form = False
                    load_project(pid)
                    st.rerun()
    
    st.markdown("---")
    st.markdown("### 📦 Import/Export")
    # Initialize the flag at the top with other session state defaults
if "import_processed" not in st.session_state:
    st.session_state.import_processed = False

# Then replace the import block with:
uploaded_project_file = st.file_uploader(
    "📥 Import Project",
    type=["json"],
    key="import_uploader"
)

if uploaded_project_file is not None and not st.session_state.import_processed:
    try:
        imported_project_id = import_project(uploaded_project_file)
        st.success("✅ Project imported successfully!")
        load_project(imported_project_id)
        st.session_state.import_processed = True
        st.rerun()
    except Exception as e:
        st.error(f"Import failed: {str(e)}")

# Reset the flag when no file is uploaded
if uploaded_project_file is None:
    st.session_state.import_processed = False
    
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


# New Project Form
if st.session_state.show_new_project_form:
    st.title("✨ Create New Project")
    
    with st.form("new_project_form"):
        project_name = st.text_input("Project Name", placeholder="e.g., Crime Hotspot Analysis")
        topic = st.text_input("Research Topic", placeholder="e.g., Urban Crime Prediction using ML")
        problem_stmt = st.text_area("Problem Statement", placeholder="Describe what you're solving...")
        timeline = st.text_input("Timeline", placeholder="e.g., 8 weeks")
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
                st.success(f"✅ Loaded {len(rag.documents)} document pages.")
            
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
            
            st.success("🎉 Project created successfully!")
            st.rerun()


# Active Project View
elif st.session_state.active_project_id and st.session_state.agent:
    pid = st.session_state.active_project_id
    meta = st.session_state.active_meta
    agent = st.session_state.agent
    graph = st.session_state.graph
    
    st.title(f"🔬 {meta['project_name']}")
    
    # Project info cards
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📚 Topic", meta["topic"][:35] + ("..." if len(meta["topic"]) > 35 else ""))
    col2.metric("📅 Timeline", meta["timeline"])
    col3.metric("📄 Documents", "Yes ✅" if meta.get("has_docs") else "No 📄")
    col4.metric("🗓 Created", meta.get("created_at", "Unknown"))
    
    st.markdown("---")
    
    # Quick Actions
    st.markdown("## ⚡ Quick Actions")
    action_cols = st.columns(4)
    
    actions = [
        ("📅 Roadmap", "roadmap"),
        ("🔍 Research Gap", "gap"),
        ("📚 Learning Path", "learning"),
        ("🧠 Methodology", "methodology"),
        ("📄 Paper Intel", "paper"),
        ("🌐 Discovery", "discovery"),
        ("🎓 Mentor", "mentor"),
    ]
    
    for i, (label, key) in enumerate(actions):
        if action_cols[i % 4].button(label, key=f"feat_{key}", use_container_width=True):
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
                answer = state.get("answer", "")
            append_message(pid, "user", f"Generate: {label}")
            append_message(pid, "assistant", answer)
            st.rerun()
    
    st.markdown("---")
    
    # Quiz and Flashcards Section
    st.markdown("## 🎓 Practice & Assessment")
    
    quiz_col, flash_col = st.columns(2)
    
    with quiz_col:
        st.markdown("### 📝 Take a Quiz")
        if st.button("🎯 Generate New Quiz", use_container_width=True, type="primary"):
            with st.spinner("Generating quiz questions..."):
                quiz_json = agent.quizgenerator_json()
                st.session_state.quiz_data = quiz_json
                st.session_state.quiz_index = 0
                st.session_state.quiz_score = 0
                st.session_state.quiz_complete = False
                st.session_state.quiz_answer_submitted = False
                st.session_state.quiz_selected_answer = None
                st.session_state.weak_topics = []
                st.session_state.strong_topics = []
                st.session_state.quiz_mode = 'quiz'
            st.rerun()
        
        if st.session_state.quiz_data and st.session_state.quiz_mode == 'quiz':
            render_quiz()
    
    with flash_col:
        st.markdown("### 🃏 Practice with Flashcards")
        if st.button("🔄 Generate New Flashcards", use_container_width=True, type="primary"):
            with st.spinner("Generating flashcards..."):
                flashcards_json = agent.flashcards_json()
                st.session_state.flashcards = flashcards_json
                st.session_state.flashcard_index = 0
                st.session_state.flashcard_showing_back = False
                st.session_state.flashcard_mastered = set()
                st.session_state.flashcard_review = set()
                st.session_state.quiz_mode = 'flashcards'
            st.rerun()
        
        if st.session_state.flashcards and st.session_state.quiz_mode == 'flashcards':
            render_flashcards()
    
    st.markdown("---")
    
    # Chat Section
    st.markdown("## 💬 Research Chat")
    
    messages = load_chat_history(pid)
    for msg in messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-message-user">🗣️ {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-message-assistant">🤖 {msg["content"]}</div>', unsafe_allow_html=True)
    
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

else:
    st.markdown("""
    <div style="text-align:center; padding: 80px 40px;">
        <h1>🔬 ResearchEngine</h1>
        <p style="font-size:1.2rem; opacity:0.7;">
            Your AI-powered research mentor. Create a project to get started.
        </p>
        <br>
        <p style="opacity:0.5;">
            ← Click <strong>➕ New Project</strong> in the sidebar
        </p>
    </div>
    """, unsafe_allow_html=True)
