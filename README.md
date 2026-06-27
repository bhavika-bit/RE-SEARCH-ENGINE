# ResearchEngine 🚀

ResearchEngine is an AI-powered research assistant that helps students, researchers, and
developers analyze research papers, discover research gaps, generate project roadmaps,
create learning plans, and receive mentor-style guidance using Retrieval-Augmented
Generation (RAG).

**Live demo:** https://re-searchengine.netlify.app
**Live API:** https://bhavikajata-researchengine-api.hf.space/docs

## Architecture

This project is split into two independently deployed services that communicate over a REST API.

- **`/project`** — React + TypeScript + Vite + Tailwind frontend. Deployed on Netlify, builds automatically from this repo.
- **`/backend`** — `model.py` (RAG pipeline, research-analysis logic) wrapped in a FastAPI app (`main.py`). Deployed as a Docker Space on Hugging Face Spaces, running a RAG pipeline (LangChain, FAISS, HuggingFace embeddings) powered by Google Gemini.

The frontend calls the backend's REST endpoints directly from the browser.

## Features

### 📚 Document Processing
- Upload and analyze PDF, DOCX, TXT, CSV
- Multiple file support, automatic chunking and embedding
- FAISS vector storage, persisted per project

### 🔍 Research Intelligence
- Project Summary, Research Gap Analysis, Paper Intelligence, Research Discovery
- Methodology Generation, Learning Path Generation, Research Roadmap Generation
- Research Mentor Guidance (structured critique of project direction)

### 🧠 AI & RAG
- Google Gemini for generation
- HuggingFace `sentence-transformers/all-MiniLM-L6-v2` for embeddings
- FAISS for semantic search over uploaded documents

### 🎓 Self-Testing
- AI-generated multiple-choice quizzes (answers hidden until checked)
- AI-generated flashcards

### 💾 Project Continuity
- Export a project (metadata + chat history) as JSON
- Import a previously exported project to continue where you left off

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| Backend API | FastAPI, Uvicorn |
| AI / LLM | Google Gemini (`gemini-2.5-flash`) via `langchain-google-genai` |
| Embeddings | HuggingFace `sentence-transformers/all-MiniLM-L6-v2` |

## Running locally

### Backend
```bash
cd backend
pip install -r requirements.txt
GOOGLE_API_KEY=your_key_here uvicorn main:app --reload
```
Visit `http://localhost:8000/docs` for interactive API docs.

### Frontend
```bash
cd project
npm install
npm run dev
```
Update `API_BASE_URL` in `project/src/services/api.ts` to `http://localhost:8000` to point the frontend at your local backend instead of the deployed one.

## API Endpoints

- `POST /projects` — create a project
- `GET /projects` — list saved projects
- `POST /projects/{id}/load` — load an existing project
- `POST /projects/{id}/documents` — upload and index documents
- `GET /projects/{id}/export` / `POST /projects/import` — project portability
- `POST /chat` — conversational research mentor
- `POST /tools/{tool_name}` — run a research-analysis tool (roadmap, researchgap, learning, methodology, paperintelligence, researchdiscovery, researchmentor, projectsummary)
- `POST /quiz` / `POST /flashcards` — generate self-test material

## Author

**Bhavika Jata**
B.Tech, Artificial Intelligence & Data Science
K. J. Somaiya School of Engineering
| Vector DB | FAISS |
| Document parsing | PyMuPDF, Docx2txt, CSVLoader |
| Frontend hosting | Netlify |
| Backend hosting | Hugging Face Spaces (Docker SDK) |

## Project Structure
