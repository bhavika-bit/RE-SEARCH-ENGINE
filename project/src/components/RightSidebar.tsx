import { useState } from 'react';
import {
  Wrench,
  HelpCircle,
  Layers,
  Map,
  Search,
  BookOpen,
  Cpu,
  FileText,
  Compass,
  MessageCircle,
  FileBarChart,
  Loader2,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  RotateCw,
  X,
  Sparkles,
} from 'lucide-react';
import { useProject } from '../contexts/ProjectContext';
import { runTool, generateQuiz, checkQuizAnswers, generateFlashcards } from '../services/api';
import MarkdownRenderer from './MarkdownRenderer';

const tools = [
  { id: 'roadmap', name: 'Roadmap', icon: Map, description: 'Project timeline' },
  { id: 'gap_analysis', name: 'Gap Analysis', icon: Search, description: 'Research opportunities' },
  { id: 'learning_path', name: 'Learning Path', icon: BookOpen, description: 'Personalized roadmap' },
  { id: 'methodology', name: 'Methodology', icon: Cpu, description: 'Research methodology' },
  { id: 'paper_intelligence', name: 'Papers', icon: FileText, description: 'Paper analysis' },
  { id: 'research_discovery', name: 'Discovery', icon: Compass, description: 'Research landscape' },
  { id: 'mentor_review', name: 'Review', icon: MessageCircle, description: 'Expert feedback' },
  { id: 'project_summary', name: 'Summary', icon: FileBarChart, description: 'Executive summary' },
];

type ActivePanel = 'tools' | 'quiz' | 'flashcards' | null;

export default function RightSidebar() {
  const {
    activeProject,
    toolResults,
    addToolResult,
    quiz,
    setQuiz,
    userAnswers,
    setUserAnswers,
    flashcards,
    setFlashcards,
    currentFlashcardIndex,
    setCurrentFlashcardIndex,
  } = useProject();

  const [activePanel, setActivePanel] = useState<ActivePanel>(null);
  const [runningTool, setRunningTool] = useState<string | null>(null);
  const [activeToolResult, setActiveToolResult] = useState<string | null>(null);
  const [isGeneratingQuiz, setIsGeneratingQuiz] = useState(false);
  const [isCheckingQuiz, setIsCheckingQuiz] = useState(false);
  const [quizChecked, setQuizChecked] = useState(false);
  const [quizResults, setQuizResults] = useState<{ correct: number; total: number; results: { questionIndex: number; correct: boolean }[] } | null>(null);
  const [isGeneratingFlashcards, setIsGeneratingFlashcards] = useState(false);
  const [isFlipped, setIsFlipped] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const handleRunTool = async (toolId: string) => {
    if (!activeProject || runningTool) return;
    setRunningTool(toolId);
    try {
      const result = await runTool(activeProject.project_id, toolId);
      addToolResult(result);
      setActiveToolResult(toolId);
    } catch (error) {
      console.error('Tool error:', error);
    } finally {
      setRunningTool(null);
    }
  };

  const handleGenerateQuiz = async () => {
    if (!activeProject) return;
    setIsGeneratingQuiz(true);
    try {
      const newQuiz = await generateQuiz(activeProject.project_id);
      setQuiz(newQuiz);
      setUserAnswers(new Array(newQuiz.questions.length).fill(-1));
      setQuizChecked(false);
      setQuizResults(null);
      setActivePanel('quiz');
    } finally {
      setIsGeneratingQuiz(false);
    }
  };

  const handleSelectAnswer = (questionIndex: number, answerIndex: number) => {
    if (quizChecked) return;
    const newAnswers = [...userAnswers];
    newAnswers[questionIndex] = answerIndex;
    setUserAnswers(newAnswers);
  };

  const handleCheckAnswers = async () => {
    if (!quiz) return;
    setIsCheckingQuiz(true);
    try {
      const result = await checkQuizAnswers(quiz, userAnswers);
      setQuizResults(result);
      setQuizChecked(true);
    } finally {
      setIsCheckingQuiz(false);
    }
  };

  const handleGenerateFlashcards = async () => {
    if (!activeProject) return;
    setIsGeneratingFlashcards(true);
    try {
      const newFlashcards = await generateFlashcards(activeProject.project_id);
      setFlashcards(newFlashcards);
      setCurrentFlashcardIndex(0);
      setIsFlipped(false);
      setActivePanel('flashcards');
    } finally {
      setIsGeneratingFlashcards(false);
    }
  };

  const handlePrevFlashcard = () => {
    if (!flashcards || currentFlashcardIndex === 0) return;
    setCurrentFlashcardIndex(currentFlashcardIndex - 1);
    setIsFlipped(false);
  };

  const handleNextFlashcard = () => {
    if (!flashcards || currentFlashcardIndex === flashcards.flashcards.length - 1) return;
    setCurrentFlashcardIndex(currentFlashcardIndex + 1);
    setIsFlipped(false);
  };

  const latestToolResult = activeToolResult ? toolResults.find(r => r.tool === activeToolResult) : null;
  const currentCard = flashcards?.flashcards[currentFlashcardIndex];

  const NavButtons = ({ vertical = false }: { vertical?: boolean }) => (
    <div className={`flex ${vertical ? 'flex-col gap-2' : 'gap-1'}`}>
      <button
        onClick={() => {
          setActivePanel('tools');
          if (!vertical) setIsMobileOpen(true);
        }}
        className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
          activePanel === 'tools'
            ? 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400'
            : 'text-stone-600 dark:text-stone-400 hover:bg-stone-100 dark:hover:bg-stone-800'
        }`}
      >
        <Wrench size={16} />
        {vertical && <span>Tools</span>}
      </button>
      <button
        onClick={handleGenerateQuiz}
        disabled={!activeProject || isGeneratingQuiz}
        className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
          activePanel === 'quiz'
            ? 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400'
            : 'text-stone-600 dark:text-stone-400 hover:bg-stone-100 dark:hover:bg-stone-800 disabled:opacity-50'
        }`}
      >
        {isGeneratingQuiz ? <Loader2 size={16} className="animate-spin" /> : <HelpCircle size={16} />}
        {vertical && <span>Quiz</span>}
      </button>
      <button
        onClick={handleGenerateFlashcards}
        disabled={!activeProject || isGeneratingFlashcards}
        className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
          activePanel === 'flashcards'
            ? 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400'
            : 'text-stone-600 dark:text-stone-400 hover:bg-stone-100 dark:hover:bg-stone-800 disabled:opacity-50'
        }`}
      >
        {isGeneratingFlashcards ? <Loader2 size={16} className="animate-spin" /> : <Layers size={16} />}
        {vertical && <span>Flashcards</span>}
      </button>
    </div>
  );

  return (
    <>
      {/* Mobile FAB */}
      <div className="lg:hidden fixed bottom-4 right-4 z-50">
        <button
          onClick={() => setIsMobileOpen(!isMobileOpen)}
          className="w-14 h-14 bg-amber-500 hover:bg-amber-600 text-white rounded-full shadow-lg flex items-center justify-center"
        >
          {isMobileOpen ? <X size={24} /> : <Sparkles size={24} />}
        </button>
      </div>

      {/* Mobile Drawer */}
      {isMobileOpen && (
        <div className="lg:hidden fixed inset-0 z-40">
          <div
            className="absolute inset-0 bg-black/20 dark:bg-black/40"
            onClick={() => setIsMobileOpen(false)}
          />
          <div className="absolute top-0 right-0 bottom-0 w-80 max-w-[85vw] bg-amber-50 dark:bg-stone-900 border-l border-stone-200 dark:border-stone-700 overflow-auto">
            <div className="p-4 border-b border-stone-200 dark:border-stone-700 flex items-center justify-between">
              <h3 className="font-medium text-stone-800 dark:text-stone-200">Research Tools</h3>
              <button onClick={() => setIsMobileOpen(false)} className="p-1">
                <X size={20} className="text-stone-500" />
              </button>
            </div>
            <div className="p-4">
              <NavButtons vertical />
              <div className="mt-4">
                <PanelContent />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex fixed right-0 top-0 bottom-0 w-80 bg-amber-50 dark:bg-stone-900 border-l border-stone-200 dark:border-stone-700 z-30 flex-col">
        {/* Header */}
        <div className="p-4 border-b border-stone-200 dark:border-stone-700">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles size={18} className="text-amber-500" />
            <h3 className="font-medium text-stone-800 dark:text-stone-200">Research Tools</h3>
          </div>
          <div className="flex gap-1">
            <NavButtons />
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-4">
          <PanelContent />
        </div>
      </aside>
    </>
  );

  function PanelContent() {
    if (!activeProject) {
      return (
        <div className="text-center py-8">
          <p className="text-sm text-stone-500 dark:text-stone-400">
            Create or load a project to use tools
          </p>
        </div>
      );
    }

    if (activePanel === null) {
      return (
        <div className="text-center py-8">
          <p className="text-sm text-stone-500 dark:text-stone-400">
            Select a tool above to get started
          </p>
        </div>
      );
    }

    if (activePanel === 'tools') {
      return (
        <div className="space-y-3">
          {/* Tool Grid */}
          <div className="grid grid-cols-2 gap-2 mb-4">
            {tools.map(tool => {
              const Icon = tool.icon;
              const isRunning = runningTool === tool.id;
              const hasResult = toolResults.some(r => r.tool === tool.id);

              return (
                <button
                  key={tool.id}
                  onClick={() => handleRunTool(tool.id)}
                  disabled={runningTool !== null}
                  className={`p-3 rounded-lg border text-left transition-all ${
                    activeToolResult === tool.id
                      ? 'bg-amber-100 dark:bg-amber-900/20 border-amber-300 dark:border-amber-700'
                      : hasResult
                      ? 'bg-green-50 dark:bg-green-900/10 border-green-200 dark:border-green-800'
                      : 'bg-white dark:bg-stone-800/50 border-stone-200 dark:border-stone-700 hover:border-amber-300 dark:hover:border-amber-700'
                  } ${runningTool && runningTool !== tool.id ? 'opacity-50' : ''}`}
                >
                  <div className="flex items-center justify-between mb-1">
                    {isRunning ? (
                      <Loader2 size={14} className="text-amber-500 animate-spin" />
                    ) : (
                      <Icon
                        size={14}
                        className={activeToolResult === tool.id
                          ? 'text-amber-600 dark:text-amber-400'
                          : 'text-stone-500'
                        }
                      />
                    )}
                    {hasResult && activeToolResult !== tool.id && (
                      <CheckCircle2 size={10} className="text-green-500" />
                    )}
                  </div>
                  <p className="text-xs font-medium text-stone-700 dark:text-stone-300">{tool.name}</p>
                  <p className="text-[10px] text-stone-400 truncate">{tool.description}</p>
                </button>
              );
            })}
          </div>

          {/* Tool Result */}
          {latestToolResult && (
            <div className="bg-white dark:bg-stone-800/50 rounded-lg p-3 border border-stone-200 dark:border-stone-700">
              <div className="flex items-center gap-2 mb-2">
                {(() => {
                  const tool = tools.find(t => t.id === latestToolResult.tool);
                  const Icon = tool?.icon || Wrench;
                  return <Icon size={14} className="text-amber-500" />;
                })()}
                <span className="text-xs font-medium text-stone-700 dark:text-stone-300">
                  {tools.find(t => t.id === latestToolResult.tool)?.name}
                </span>
              </div>
              <div className="text-xs max-h-64 overflow-auto">
                <MarkdownRenderer content={latestToolResult.result} />
              </div>
            </div>
          )}
        </div>
      );
    }

    if (activePanel === 'quiz' && quiz) {
      return (
        <div className="space-y-3">
          {/* Score */}
          {quizChecked && quizResults && (
            <div className="bg-amber-100 dark:bg-amber-900/20 rounded-lg p-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle2 size={16} className="text-green-500" />
                <span className="text-sm font-medium text-stone-800 dark:text-stone-200">
                  {quizResults.correct}/{quizResults.total}
                </span>
              </div>
              <button
                onClick={() => {
                  setQuiz(null);
                  setQuizChecked(false);
                  setQuizResults(null);
                  setUserAnswers([]);
                }}
                className="p-1 hover:bg-amber-200 dark:hover:bg-amber-800/40 rounded"
              >
                <RotateCw size={14} className="text-stone-500" />
              </button>
            </div>
          )}

          {/* Questions */}
          {quiz.questions.map((question, qIndex) => {
            const isCorrect = quizResults?.results[qIndex]?.correct;
            const userAnswer = userAnswers[qIndex];

            return (
              <div
                key={qIndex}
                className={`bg-white dark:bg-stone-800/50 rounded-lg p-3 border ${
                  quizChecked
                    ? isCorrect
                      ? 'border-green-300 dark:border-green-700'
                      : 'border-red-300 dark:border-red-700'
                    : 'border-stone-200 dark:border-stone-700'
                }`}
              >
                <div className="flex items-start gap-2 mb-2">
                  <div className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-medium flex-shrink-0 ${
                    quizChecked
                      ? isCorrect
                        ? 'bg-green-100 dark:bg-green-900/30 text-green-600'
                        : 'bg-red-100 dark:bg-red-900/30 text-red-600'
                      : 'bg-amber-100 dark:bg-amber-900/30 text-amber-600'
                  }`}>
                    {qIndex + 1}
                  </div>
                  <p className="text-xs text-stone-700 dark:text-stone-300">{question.question}</p>
                </div>
                <div className="space-y-1">
                  {question.options.map((option, oIndex) => {
                    const isSelected = userAnswer === oIndex;
                    const isCorrectAnswer = question.answer === oIndex;

                    return (
                      <button
                        key={oIndex}
                        onClick={() => handleSelectAnswer(qIndex, oIndex)}
                        disabled={quizChecked}
                        className={`w-full text-left px-2 py-1.5 rounded text-[11px] transition-colors ${
                          quizChecked
                            ? isCorrectAnswer
                              ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400'
                              : isSelected
                              ? 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400'
                              : 'text-stone-500'
                            : isSelected
                            ? 'bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400'
                            : 'hover:bg-stone-50 dark:hover:bg-stone-700 text-stone-600 dark:text-stone-400'
                        }`}
                      >
                        {option}
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })}

          {/* Check Button */}
          {!quizChecked && (
            <button
              onClick={handleCheckAnswers}
              disabled={isCheckingQuiz || userAnswers.some(a => a === -1)}
              className="w-full py-2 bg-amber-500 hover:bg-amber-600 disabled:bg-stone-300 dark:disabled:bg-stone-600 text-white text-sm font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              {isCheckingQuiz ? (
                <Loader2 size={14} className="animate-spin" />
              ) : (
                <CheckCircle2 size={14} />
              )}
              Check Answers
            </button>
          )}
        </div>
      );
    }

    if (activePanel === 'flashcards' && flashcards && currentCard) {
      return (
        <div className="space-y-3">
          {/* Flashcard */}
          <div
            onClick={() => setIsFlipped(!isFlipped)}
            className="cursor-pointer"
            style={{ perspective: '1000px' }}
          >
            <div
              className="relative h-40 transition-transform duration-500"
              style={{
                transformStyle: 'preserve-3d',
                transform: isFlipped ? 'rotateY(180deg)' : 'rotateY(0deg)',
              }}
            >
              {/* Front */}
              <div
                className="absolute inset-0 bg-gradient-to-br from-amber-50 to-amber-100 dark:from-stone-800 dark:to-stone-900 rounded-lg border border-amber-200 dark:border-stone-700 flex flex-col items-center justify-center p-4"
                style={{ backfaceVisibility: 'hidden' }}
              >
                <p className="text-[10px] text-stone-400 mb-1">TERM</p>
                <p className="text-sm font-medium text-stone-800 dark:text-stone-200 text-center">
                  {currentCard.front}
                </p>
              </div>
              {/* Back */}
              <div
                className="absolute inset-0 bg-gradient-to-br from-amber-500 to-amber-600 dark:from-amber-600 dark:to-amber-700 rounded-lg border border-amber-300 dark:border-amber-800 flex flex-col items-center justify-center p-4"
                style={{ backfaceVisibility: 'hidden', transform: 'rotateY(180deg)' }}
              >
                <p className="text-[10px] text-amber-200 mb-1">DEFINITION</p>
                <p className="text-xs text-white text-center">{currentCard.back}</p>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <div className="flex items-center justify-between">
            <button
              onClick={handlePrevFlashcard}
              disabled={currentFlashcardIndex === 0}
              className="p-2 rounded-lg bg-stone-100 dark:bg-stone-800 hover:bg-stone-200 dark:hover:bg-stone-700 disabled:opacity-30"
            >
              <ChevronLeft size={16} className="text-stone-600 dark:text-stone-400" />
            </button>
            <span className="text-xs text-stone-500">
              {currentFlashcardIndex + 1} / {flashcards.flashcards.length}
            </span>
            <button
              onClick={handleNextFlashcard}
              disabled={currentFlashcardIndex === flashcards.flashcards.length - 1}
              className="p-2 rounded-lg bg-stone-100 dark:bg-stone-800 hover:bg-stone-200 dark:hover:bg-stone-700 disabled:opacity-30"
            >
              <ChevronRight size={16} className="text-stone-600 dark:text-stone-400" />
            </button>
          </div>

          {/* Progress dots */}
          <div className="flex justify-center gap-1">
            {flashcards.flashcards.map((_, i) => (
              <button
                key={i}
                onClick={() => {
                  setCurrentFlashcardIndex(i);
                  setIsFlipped(false);
                }}
                className={`h-1.5 rounded-full transition-all ${
                  i === currentFlashcardIndex
                    ? 'bg-amber-500 w-4'
                    : 'bg-stone-300 dark:bg-stone-600 w-1.5'
                }`}
              />
            ))}
          </div>
        </div>
      );
    }

    return null;
  }
}
