# ResearchEngine 🚀
[https://helpful-klepon-6bb92c.netlify.app/]
ResearchEngine is an AI-powered research assistant that helps students, researchers, and developers analyze research papers, discover research gaps, generate project roadmaps, create learning plans, and receive mentor-style guidance using Retrieval-Augmented Generation (RAG).

## Features

### 📚 Document Processing
- Upload and analyze:
  - PDF
  - DOCX
  - TXT
  - CSV
- Multiple file support
- Folder ingestion support
- Automatic chunking and embedding

### 🔍 Research Intelligence
- Project Summary
- Research Gap Analysis
- Literature Review Assistance
- Paper Intelligence
- Research Discovery
- Methodology Generation
- Learning Path Generation
- Research Roadmap Generation
- Research Mentor Guidance

### 🧠 AI & RAG
- Google Gemini Integration
- HuggingFace Embeddings
- FAISS Vector Database
- Semantic Search
- Context-Aware Research Assistance

### 🎯 Planned Enhancements
- Persistent Project Sessions
- Conversational Research Mentor
- Project Progress Tracking
- Quiz Evaluation System
- Long-Term Project Memory
- Multi-Project Workspace

---

## Tech Stack

### Languages
- Python

### AI & LLM
- Google Gemini
- LangChain

### Embeddings
- Sentence Transformers
- HuggingFace Embeddings
- all-MiniLM-L6-v2

### Vector Database
- FAISS

### Frontend
- Streamlit

### Document Processing
- PyMuPDF
- Docx2txt
- CSV Loader

---

## Installation

### Clone Repository

```bash
git clone https://github.com/yourusername/ResearchEngine.git

cd ResearchEngine
```

### Create Virtual Environment

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Linux / Mac:

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_google_api_key
```

---

## Run Application

### CLI Version

```bash
python model.py
```

### Streamlit Version

```bash
streamlit run app.py
```

---

## Project Structure

```text
ResearchEngine/
│
├── app.py
├── model.py
├── requirements.txt
├── README.md
├── .gitignore
├── .env
│
├── projects/
│
└── assets/
```

---

## Use Cases

- Academic Research
- Literature Review
- Thesis Planning
- Research Gap Discovery
- Learning New Research Domains
- Research Project Management

---

## Author

**Bhavika Jata**

B.Tech Artificial Intelligence & Data Science

KJ Somaiya College of Engineering
