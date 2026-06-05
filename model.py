import warnings
warnings.filterwarnings("ignore")

import os
from dotenv import load_dotenv
import os

load_dotenv()
from langchain_community.document_loaders import PyMuPDFLoader,TextLoader,CSVLoader,Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


class RAG:

    def __init__(self):
        self.documents = None
        self.chunks = None
        self.embeddings = None
        self.vectorstore = None

    def load_data(self):
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

    def vectordb(self):
        self.vectorstore = FAISS.from_documents(self.chunks, self.embeddings)

    # def querytest(self):
    #     query = "What is the main topic of the research paper?"
    #     results = self.vectorstore.similarity_search(query, k=2)


from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate


class ResearchAnalyst:

    def __init__(self, rag_instance, llm_instance):
        self.rag = rag_instance
        self.llm = llm_instance
        # --- FIX: state lives here, set once via set_project() ---
        self.topic = None
        self.problem_statement = None
        self.timeline = None

    def set_project(self, topic, problem_statement, timeline):
        """Call this once before using any feature method."""
        self.topic = topic
        self.problem_statement = problem_statement
        self.timeline = timeline

    # --- FIX: single shared helper so retrieval isn't repeated 8 times ---
    def _get_context(self, k=5):
        query = f"Topic: {self.topic}\nProblem Statement: {self.problem_statement}"
        results = self.rag.vectorstore.similarity_search(query, k=k)
        context = "\n\n".join([doc.page_content for doc in results])
        return context


    def roadmap_generation(self):
        if self.rag is not None:
            context = self._get_context()
        else:
            context = None
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
        response = self.llm.invoke(prompt)
        return response.content

    def researchgap(self):
        if self.rag is not None:
            context = self._get_context()
        else:
            context = None
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
        response = self.llm.invoke(prompt)
        return response.content

    def learning(self):
        if self.rag is not None:
            context = self._get_context()
        else:
            context = None
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
        response = self.llm.invoke(prompt)
        return response.content

    def quizgenerator(self):
        if self.rag is not None:
            context = self._get_context()
        else:
            context = None
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

    def methodology(self):
        if self.rag is not None:
            context = self._get_context()
        else:
            context = None
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
        response = self.llm.invoke(prompt)
        return response.content

    def paperintelligence(self):
        if self.rag is not None:
            context = self._get_context()
        else:
            context = None
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
        response = self.llm.invoke(prompt)
        return response.content

    def researchdiscovery(self):
        if self.rag is not None:
            context = self._get_context()
        else:
            context = None
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
        response = self.llm.invoke(prompt)
        return response.content

    def researchmentor(self):
        if self.rag is not None:
            context = self._get_context()
        else:
            context = None
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
        response = self.llm.invoke(prompt)
        return response.content
    def projectsummary(self):
        if self.rag is not None:
            context = self._get_context()
        else:
            context = None
        prompt = f"""
You are an expert research mentor and thesis supervisor.
Topic: {self.topic}
Problem Statement: {self.problem_statement}
Relevant Research Context: {context}

Generate:
1. Project summary
2. pre requisites
3. Project scope
4. comparison with current research and trends
5. idea feasibility

Be detailed and practical.
"""
        response = self.llm.invoke(prompt)
        return response.content


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
    def projectsummary_node(self,state):
        state["answer"] = self.agent.projectsummary()
        return state
choice = input("""
Do you have sources?

1. Yes
2. No

Enter choice:
""")

# input() returns string, not integer
if choice.strip().lower() == "yes":
    rag = RAG()
    rag.load_data()
    rag.chunking()
    rag.embedding()
    rag.vectordb()

else:
    rag = None


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.6
)

agent = ResearchAnalyst(
    rag_instance=rag,
    llm_instance=llm
)

graph = Graph(agent)

topic = input("Enter topic: ")
problem_statement = input("Enter problem statement: ")
timeline = input("Enter timeline: ")

agent.set_project(
    topic,
    problem_statement,
    timeline
)

state = {}

state = graph.projectsummary_node(state)

print("\n==============================")
print("PROJECT SUMMARY")
print("==============================\n")
print(state["answer"])

while True:

    choice = input("""
================================
RESEARCH ANALYST
================================

1. Project Roadmap
2. Research Gap Analysis
3. Learning Path
4. Quiz Generator
5. Methodology Generator
6. Paper Intelligence
7. Research Discovery
8. Research Mentor
9. Exit

Enter choice:
""")

    state = {}

    if choice == "1":

        state = graph.roadmap_node(state)
        print(state["answer"])

    elif choice == "2":

        state = graph.researchgap_node(state)
        print(state["answer"])

    elif choice == "3":

        state = graph.learning_node(state)
        print(state["answer"])

    elif choice == "4":

        state = graph.quizgenerator_node(state)
        print(state["answer"])

    elif choice == "5":

        state = graph.methodology_node(state)
        print(state["answer"])

    elif choice == "6":

        state = graph.paperintelligence_node(state)
        print(state["answer"])

    elif choice == "7":

        state = graph.researchdiscovery_node(state)
        print(state["answer"])

    elif choice == "8":

        state = graph.researchmentor_node(state)
        print(state["answer"])

    elif choice == "9":

        print("Exiting Research Analyst...")
        break

    else:

        print("Invalid choice. Please try again.")