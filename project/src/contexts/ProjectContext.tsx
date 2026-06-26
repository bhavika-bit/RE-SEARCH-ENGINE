import { createContext, useContext, useState, ReactNode } from 'react';
import { Project, Message, Quiz, Flashcards, ToolResult } from '../services/api';

interface ProjectContextType {
  activeProject: Project | null;
  projects: Project[];
  chatHistory: Message[];
  toolResults: ToolResult[];
  quiz: Quiz | null;
  userAnswers: number[];
  flashcards: Flashcards | null;
  currentFlashcardIndex: number;
  setActiveProject: (project: Project | null) => void;
  setProjects: (projects: Project[]) => void;
  addMessage: (message: Message) => void;
  clearChat: () => void;
  addToolResult: (result: ToolResult) => void;
  setQuiz: (quiz: Quiz | null) => void;
  setUserAnswers: (answers: number[]) => void;
  setFlashcards: (flashcards: Flashcards | null) => void;
  setCurrentFlashcardIndex: (index: number) => void;
  documentStatus: string;
  setDocumentStatus: (status: string) => void;
  uploadedFiles: File[];
  setUploadedFiles: (files: File[]) => void;
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined);

export function ProjectProvider({ children }: { children: ReactNode }) {
  const [activeProject, setActiveProject] = useState<Project | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [chatHistory, setChatHistory] = useState<Message[]>([]);
  const [toolResults, setToolResults] = useState<ToolResult[]>([]);
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [userAnswers, setUserAnswers] = useState<number[]>([]);
  const [flashcards, setFlashcards] = useState<Flashcards | null>(null);
  const [currentFlashcardIndex, setCurrentFlashcardIndex] = useState(0);
  const [documentStatus, setDocumentStatus] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);

  const addMessage = (message: Message) => {
    setChatHistory(prev => [...prev, message]);
  };

  const clearChat = () => {
    setChatHistory([]);
  };

  const addToolResult = (result: ToolResult) => {
    setToolResults(prev => [...prev, result]);
  };

  return (
    <ProjectContext.Provider
      value={{
        activeProject,
        projects,
        chatHistory,
        toolResults,
        quiz,
        userAnswers,
        flashcards,
        currentFlashcardIndex,
        setActiveProject,
        setProjects,
        addMessage,
        clearChat,
        addToolResult,
        setQuiz,
        setUserAnswers,
        setFlashcards,
        setCurrentFlashcardIndex,
        documentStatus,
        setDocumentStatus,
        uploadedFiles,
        setUploadedFiles,
      }}
    >
      {children}
    </ProjectContext.Provider>
  );
}

export function useProject() {
  const context = useContext(ProjectContext);
  if (!context) {
    throw new Error('useProject must be used within a ProjectProvider');
  }
  return context;
}
