const API_BASE_URL = 'https://bhavikajata-researchengine-api.hf.space';

function generateId(): string {
  return Math.random().toString(36).substring(2, 10);
}

export interface Project {
  project_id: string;
  topic: string;
  problem_statement: string;
  timeline: string;
  created_at: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface ToolResult {
  tool: string;
  result: string;
  timestamp: string;
}

export interface QuizQuestion {
  question: string;
  options: string[];
  answer: number;
  explanation: string;
}

export interface Quiz {
  questions: QuizQuestion[];
}

export interface Flashcard {
  front: string;
  back: string;
}

export interface Flashcards {
  flashcards: Flashcard[];
}

// Maps the UI's tool-name strings to the backend's endpoint names.
// (The UI and the FastAPI backend were built independently and used slightly
// different naming, so this just bridges the two without changing either side.)
const TOOL_NAME_MAP: Record<string, string> = {
  roadmap: 'roadmap',
  gap_analysis: 'researchgap',
  learning_path: 'learning',
  methodology: 'methodology',
  paper_intelligence: 'paperintelligence',
  research_discovery: 'researchdiscovery',
  mentor_review: 'researchmentor',
  project_summary: 'projectsummary',
};

async function apiFetch(path: string, options: RequestInit = {}) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      ...(options.body && !(options.body instanceof FormData)
        ? { 'Content-Type': 'application/json' }
        : {}),
      ...options.headers,
    },
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const errBody = await res.json();
      detail = errBody.detail ? JSON.stringify(errBody.detail) : detail;
    } catch {
      // response wasn't JSON, fall back to statusText
    }
    throw new Error(`API error (${res.status}): ${detail}`);
  }

  return res.json();
}

export async function createProject(
  topic: string,
  problem_statement: string,
  timeline: string
): Promise<Project> {
  const data = await apiFetch('/projects', {
    method: 'POST',
    body: JSON.stringify({ topic, problem_statement, timeline }),
  });
  return data.metadata as Project;
}

export async function loadAllProjects(): Promise<Project[]> {
  const data = await apiFetch('/projects');
  return data as Project[];
}

export async function loadProject(projectId: string): Promise<Project | null> {
  try {
    const data = await apiFetch(`/projects/${projectId}/load`, { method: 'POST' });
    return data.metadata as Project;
  } catch {
    return null;
  }
}

// The backend stores chat history per project. Call this after loadProject()
// to restore the conversation — loadProject() only returns project metadata.
export async function getChatHistory(projectId: string): Promise<Message[]> {
  const data = await apiFetch(`/chat/${projectId}/history`);
  // Backend stores history as {role, content} pairs without id/timestamp,
  // so we generate those here to match the Message shape the UI expects.
  return (data as { role: 'user' | 'assistant'; content: string }[]).map((m) => ({
    id: generateId(),
    role: m.role,
    content: m.content,
    timestamp: new Date().toISOString(),
  }));
}

export async function uploadDocuments(
  projectId: string,
  files: File[]
): Promise<{ success: boolean; count: number }> {
  const formData = new FormData();
  files.forEach((f) => formData.append('files', f));

  const data = await apiFetch(`/projects/${projectId}/documents`, {
    method: 'POST',
    body: formData,
  });

  return { success: data.status === 'indexed', count: data.count ?? 0 };
}

// Kept for compatibility with any existing call sites — the backend indexes
// documents in the same step as uploadDocuments, so this just re-confirms status.
export async function indexDocuments(
  projectId: string
): Promise<{ success: boolean; message: string }> {
  return { success: true, message: `Documents for project ${projectId} are indexed.` };
}

export async function sendChatMessage(
  projectId: string,
  message: string,
  _history: Message[]
): Promise<Message> {
  const data = await apiFetch('/chat', {
    method: 'POST',
    body: JSON.stringify({ project_id: projectId, message }),
  });

  return {
    id: generateId(),
    role: 'assistant',
    content: data.answer,
    timestamp: new Date().toISOString(),
  };
}

export async function runTool(projectId: string, toolName: string): Promise<ToolResult> {
  const backendToolName = TOOL_NAME_MAP[toolName] || toolName;

  const data = await apiFetch(`/tools/${backendToolName}`, {
    method: 'POST',
    body: JSON.stringify({ project_id: projectId }),
  });

  return {
    tool: toolName,
    result: data.answer,
    timestamp: new Date().toISOString(),
  };
}

export async function generateQuiz(projectId: string): Promise<Quiz> {
  const data = await apiFetch('/quiz', {
    method: 'POST',
    body: JSON.stringify({ project_id: projectId }),
  });
  return data as Quiz;
}

export async function checkQuizAnswers(
  quiz: Quiz,
  userAnswers: number[]
): Promise<{
  correct: number;
  total: number;
  results: { questionIndex: number; correct: boolean; userAnswer: number }[];
}> {
  // Grading is simple enough to keep on the frontend — no need for a round trip.
  let correct = 0;
  const results = quiz.questions.map((q, i) => {
    const isCorrect = userAnswers[i] === q.answer;
    if (isCorrect) correct++;
    return { questionIndex: i, correct: isCorrect, userAnswer: userAnswers[i] };
  });
  return { correct, total: quiz.questions.length, results };
}

export async function generateFlashcards(projectId: string): Promise<Flashcards> {
  const data = await apiFetch('/flashcards', {
    method: 'POST',
    body: JSON.stringify({ project_id: projectId }),
  });
  return data as Flashcards;
}

export async function exportProject(projectId: string): Promise<string> {
  const data = await apiFetch(`/projects/${projectId}/export`);
  return JSON.stringify(data, null, 2);
}

export async function importProject(jsonData: string): Promise<Project> {
  const blob = new Blob([jsonData], { type: 'application/json' });
  const formData = new FormData();
  formData.append('file', blob, 'import.json');

  const data = await apiFetch('/projects/import', {
    method: 'POST',
    body: formData,
  });

  return data.metadata as Project;
}
