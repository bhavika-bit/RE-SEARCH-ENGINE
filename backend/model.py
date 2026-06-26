import warnings
warnings.filterwarnings("ignore")

import os
import json
import uuid
from datetime import datetime
import tempfile

from dotenv import load_dotenv

load_dotenv()

from langchain_community.document_loaders import PyMuPDFLoader, TextLoader, CSVLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI

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

    def load_data(self):
        """CLI-based document loader"""
        path_input = input("""
Enter file/folder paths separated by commas:

Examples:
C:\\paper1.pdf
C:\\paper1.pdf,C:\\paper2.pdf
C:\\ResearchFolder

Enter path(s):
""")

        paths = [p.strip() for p in path_input.split(",")]
        self.documents = []

        for path in paths:
            if os.path.isdir(path):
                for file in os.listdir(path):
                    full_path = os.path.join(path, file)
                    ext = os.path.splitext(file)[1].lower()
                    try:
                        if ext == ".pdf":
                            loader = PyMuPDFLoader(full_path)
                        elif ext == ".txt":
                            loader = TextLoader(full_path)
                        elif ext == ".csv":
                            loader = CSVLoader(full_path)
                        elif ext == ".docx":
                            loader = Docx2txtLoader(full_path)
                        else:
                            continue
                        docs = loader.load()
                        self.documents.extend(docs)
                    except Exception as e:
                        print(f"Skipped {file}: {e}")
            elif os.path.isfile(path):
                ext = os.path.splitext(path)[1].lower()
                try:
                    if ext == ".pdf":
                        loader = PyMuPDFLoader(path)
                    elif ext == ".txt":
                        loader = TextLoader(path)
                    elif ext == ".csv":
                        loader = CSVLoader(path)
                    elif ext == ".docx":
                        loader = Docx2txtLoader(path)
                    else:
                        print(f"Unsupported file: {path}")
                        continue
                    docs = loader.load()
                    self.documents.extend(docs)
                except Exception as e:
                    print(f"Error loading {path}: {e}")
            else:
                print(f"Path not found: {path}")

        print(f"\nLoaded {len(self.documents)} documents/pages successfully.")

    def load_data_from_files(self, uploaded_files, project_id):
        """Streamlit-based document loader from file uploads"""
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
                    print(f"Unsupported file: {uf.name}")
                    continue
                docs = loader.load()
                self.documents.extend(docs)
            except Exception as e:
                print(f"Skipped {uf.name}: {e}")
            finally:
                os.unlink(tmp_path)

    def chunking(self):
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150
        )
        self.chunks = splitter.split_documents(self.documents)

    def embedding(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        vec = self.embeddings.embed_query("hello world")

    def build_vectordb(self):
        """Create FAISS vectorstore from chunks"""
        self.vectorstore = FAISS.from_documents(self.chunks, self.embeddings)

    def vectordb(self):
        """Legacy method - creates vectorstore"""
        self.vectorstore = FAISS.from_documents(self.chunks, self.embeddings)

    def save_vectordb(self, project_id):
        """Persist FAISS vectorstore to disk"""
        faiss_path = get_faiss_path(project_id)
        os.makedirs(faiss_path, exist_ok=True)
        self.vectorstore.save_local(faiss_path)

    def load_vectordb(self, project_id):
        """Load FAISS vectorstore from disk"""
        faiss_path = get_faiss_path(project_id)
        if os.path.exists(faiss_path):
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            self.vectorstore = FAISS.load_local(
                faiss_path, 
                self.embeddings, 
                allow_dangerous_deserialization=True
            )
            return True
        return False


# ==================== RESEARCH ANALYST CLASS ====================

class ResearchAnalyst:
    def __init__(self, rag_instance, llm_instance):
        self.rag = rag_instance
        self.llm = llm_instance
        self.topic = None
        self.problem_statement = None
        self.timeline = None

    def set_project(self, topic, problem_statement, timeline):
        """Initialize project context"""
        self.topic = topic
        self.problem_statement = problem_statement
        self.timeline = timeline

    def _get_context(self, k=5):
        """Retrieve relevant research context from vectorstore"""
        if self.rag is None or self.rag.vectorstore is None:
            return "No research context available."
        query = f"Topic: {self.topic}\nProblem Statement: {self.problem_statement}"
        results = self.rag.vectorstore.similarity_search(query, k=k)
        return "\n\n".join([doc.page_content for doc in results])

    # ==================== CORE FEATURES ====================

    def roadmap_generation(self):
        context = self._get_context()
        prompt = f"""
You are a research project manager.

Topic: {self.topic}
Problem Statement: {self.problem_statement}
Timeline: {self.timeline}

Retrieved Research Context:
{context}

Generate a project execution roadmap.

## Milestones

Week-by-week deliverables.

## Dependencies

What must be completed before each milestone?

## Deliverables

Documents
Code
Experiments
Presentation

## Time Allocation

Percentage effort for:
- Literature review
- Data preparation
- Modeling
- Evaluation
- Documentation

## Risk Timeline

Predict likely bottlenecks.

## Final Submission Checklist

Everything needed before project completion.
"""
        response = self.llm.invoke(prompt)
        return response.content

    def researchgap(self):
        context = self._get_context()
        prompt = f"""
You are a research reviewer.

Topic: {self.topic}
Problem Statement: {self.problem_statement}

Retrieved Research Context:
{context}

Perform a gap analysis.

Generate:

## 1. Common Themes

What are most papers trying to solve?

## 2. Repeated Methodologies

What techniques appear repeatedly?

## 3. Current Limitations

Identify:
- Dataset limitations
- Model limitations
- Evaluation limitations
- Deployment limitations

## 4. Missing Research Areas

Identify:
- Areas with little attention
- Missing comparisons
- Missing datasets
- Missing benchmarks

## 5. Novelty Opportunities

Generate 10 research ideas.

For each:
- Why it is novel
- Difficulty (1-10)
- Publication potential

## 6. Best Research Direction

Select the single most promising direction.

Defend your reasoning.
"""
        response = self.llm.invoke(prompt)
        return response.content

    def learning(self):
        context = self._get_context()
        prompt = f"""
You are an academic mentor.

Topic: {self.topic}
Problem Statement: {self.problem_statement}

Retrieved Research Context:
{context}

Build a personalized learning roadmap.

Generate:

## Prerequisites

What must be known first?

## Knowledge Graph

Create:

Foundation
→ Intermediate
→ Advanced
→ Research

## Weekly Learning Plan

Week 1:
Week 2:
...

## Practical Exercises

For each stage:
- Project
- Coding exercise
- Paper reading

## Common Mistakes

List beginner traps.

## Readiness Checkpoints

How can the student verify mastery?

Prioritize understanding over memorization.
"""
        response = self.llm.invoke(prompt)
        return response.content

    def quizgenerator(self):
        context = self._get_context()
        prompt = f"""
You are an expert research mentor.
Topic: {self.topic}
Problem Statement: {self.problem_statement}
Relevant Research Context: {context}

Generate:
1. MCQ quizzes to practice the concept don't reveal the answers before the user gives and 
answer, show options and then check user answers with the correct answer
2. Flashcards with keywords and definitions
3. Presentation points and practice
4. Topics to focus more on and topics that are already well understood based on the quiz answers
given by the user. Do not guess this, use users answers to tell the topics.

Be detailed and practical.
"""
        response = self.llm.invoke(prompt)
        return response.content

    def quizgenerator_json(self):
        """Generate quiz questions in structured JSON format"""
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
        """Generate flashcards in structured JSON format"""
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
You are a research architect.

Topic: {self.topic}
Problem Statement: {self.problem_statement}
Timeline: {self.timeline}

Retrieved Research Context:
{context}

Design a complete project methodology.

Generate:

## 1. Recommended Architecture

Explain:
- Inputs
- Processing stages
- Models
- Outputs

## 2. Alternative Architectures

Generate:
- Conservative approach
- Balanced approach
- Novel approach

Compare:
- Difficulty
- Innovation
- Expected outcome

## 3. Implementation Plan

Phase-wise:

Phase 1:
Phase 2:
Phase 3:
...

## 4. Technical Stack

Specify:
- Libraries
- Frameworks
- Hardware requirements

## 5. Risk Analysis

For each risk:
- Probability
- Impact
- Mitigation

## 6. Publication Potential

Rate:
- Novelty
- Feasibility
- Publishability

Be brutally realistic.
"""
        response = self.llm.invoke(prompt)
        return response.content

    def paperintelligence(self):
        context = self._get_context()
        prompt = f"""
You are a research analyst.

Topic: {self.topic}
Problem Statement: {self.problem_statement}

Retrieved Research Context:
{context}

Build a paper intelligence report.

Generate:

## Paper Comparison Matrix

For each paper:

| Paper | Dataset | Model | Results | Strength | Weakness |

## Methodology Trends

Identify:
- Most common architectures
- Most common datasets
- Most common evaluation metrics

## Contradictions

Where do papers disagree?

## Most Influential Papers

Rank top 5.

Explain why.

## Reading Priority

Create:

Beginner Papers
Intermediate Papers
Advanced Papers

## Research Takeaways

Summarize lessons a researcher should learn.
"""
        response = self.llm.invoke(prompt)
        return response.content

    def researchdiscovery(self):
        context = self._get_context()
        prompt = f"""
You are a senior research scout.

Topic: {self.topic}
Problem Statement: {self.problem_statement}

Retrieved Research Context:
{context}

Your task is NOT to summarize.

Build a research landscape report.

Generate:

## 1. Field Overview
- What subdomain does this belong to?
- What problems are researchers trying to solve?

## 2. Important Research Directions
List 5 major research directions currently being explored.

For each:
- Goal
- Why it matters
- Recent popularity

## 3. Research Opportunities
Identify underexplored opportunities based on the retrieved papers.

## 4. Dataset Landscape
Create a table:

| Dataset | Purpose | Size | Common Usage |

## 5. Research Ecosystem
List:
- Major conferences
- Journals
- Research groups
- GitHub repositories

## 6. Emerging Trends
Predict where this field may move within 2-3 years.

Output should resemble a research scouting report.
"""
        response = self.llm.invoke(prompt)
        return response.content

    def researchmentor(self):
        context = self._get_context()
        prompt = f"""
You are a strict thesis supervisor.

Topic: {self.topic}
Problem Statement: {self.problem_statement}
Timeline: {self.timeline}

Retrieved Research Context:
{context}

Conduct a project review.

Generate:

## Overall Assessment

Rate:
- Clarity
- Novelty
- Feasibility
- Impact

## Strengths

## Weaknesses

## Reviewer Concerns

List questions a reviewer may ask.

## Missing Components

What is not yet addressed?

## Next 5 Actions

Most important tasks right now.

## Success Probability

Estimate likelihood of completion within timeline.

Be constructive but brutally honest.
"""
        response = self.llm.invoke(prompt)
        return response.content

    def projectsummary(self):
        context = self._get_context()
        prompt = f"""
You are preparing a project brief for a professor.

Topic: {self.topic}
Problem Statement: {self.problem_statement}

Retrieved Research Context:
{context}

Generate:

## Executive Summary

## Problem Statement

## Why This Matters

## Current State of Research

## Proposed Solution

## Expected Outcomes

## Technical Requirements

## Innovation Score (1-10)

## Feasibility Score (1-10)

## Elevator Pitch (100 words)

The output should be presentation-ready.
"""
        response = self.llm.invoke(prompt)
        return response.content

    def chat(self, user_message, history):
        """Conversational research mentor"""
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

    def quizgenerator_node(self, state):
        state["answer"] = self.agent.quizgenerator()
        return state

    def flashcards_node(self, state):
        state["answer"] = self.agent.flashcards_json()
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
