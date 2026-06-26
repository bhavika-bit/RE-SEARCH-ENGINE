# ResearchEngine API (backend)

FastAPI wrapper around `model.py` (RAG + Gemini research mentor logic).
Deployed on Render so the Netlify/bolt.new frontend has a real backend to call.

## Deploy on Render

1. Push this folder's contents to a GitHub repo (or a `backend/` subfolder of an existing repo).
2. Go to [render.com](https://render.com) → New → **Web Service** → connect your GitHub repo.
3. Settings:
   - **Root Directory**: this folder (e.g. `backend`) if it's a subfolder, otherwise leave blank.
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add an environment variable: `GOOGLE_API_KEY` = your Gemini key.
5. Deploy. Render gives you a URL like `https://researchengine-api.onrender.com`.

## Local testing

```bash
pip install -r requirements.txt
GOOGLE_API_KEY=your_key_here uvicorn main:app --reload
```

Visit `http://localhost:8000/docs` for interactive API docs (Swagger UI) — useful for testing
each endpoint by hand before wiring the frontend to it.

## Endpoints

- `POST /projects` — create a project `{topic, problem_statement, timeline}`
- `GET /projects` — list saved projects
- `POST /projects/{id}/load` — load an existing project into memory
- `POST /projects/{id}/documents` — upload files (multipart form, field name `files`)
- `GET /projects/{id}/export` — export project + chat as JSON
- `POST /projects/import` — import a previously exported JSON (multipart, field name `file`)
- `POST /chat` — `{project_id, message}` → `{answer}`
- `POST /chat/clear` — `{project_id}`
- `GET /chat/{id}/history` — chat history list
- `POST /tools/{tool_name}` — `{project_id}` → `{answer}`. tool_name one of:
  `roadmap`, `researchgap`, `learning`, `methodology`, `paperintelligence`,
  `researchdiscovery`, `researchmentor`, `projectsummary`
- `POST /quiz` — `{project_id}` → `{questions: [...]}`
- `POST /flashcards` — `{project_id}` → `{flashcards: [...]}`

## Note on free-tier Render

Render's free web services spin down after ~15 minutes of inactivity and take
~30-60 seconds to wake up on the next request. The frontend's first request
after idle time may feel slow — this is expected, not a bug.
