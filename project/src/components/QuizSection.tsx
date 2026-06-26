import { useState } from 'react';
import { HelpCircle, Sparkles, CheckCircle2, XCircle, RotateCcw } from 'lucide-react';
import { useProject } from '../contexts/ProjectContext';
import { generateQuiz, checkQuizAnswers } from '../services/api';

export default function QuizSection() {
  const { activeProject, quiz, setQuiz, userAnswers, setUserAnswers } = useProject();
  const [isGenerating, setIsGenerating] = useState(false);
  const [isChecking, setIsChecking] = useState(false);
  const [checked, setChecked] = useState(false);
  const [results, setResults] = useState<{ correct: number; total: number; results: { questionIndex: number; correct: boolean; userAnswer: number }[] } | null>(null);

  const handleGenerateQuiz = async () => {
    if (!activeProject || isGenerating) return;
    setIsGenerating(true);
    try {
      const newQuiz = await generateQuiz(activeProject.project_id);
      setQuiz(newQuiz);
      setUserAnswers(new Array(newQuiz.questions.length).fill(-1));
      setChecked(false);
      setResults(null);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSelectAnswer = (questionIndex: number, answerIndex: number) => {
    if (checked) return;
    const newAnswers = [...userAnswers];
    newAnswers[questionIndex] = answerIndex;
    setUserAnswers(newAnswers);
  };

  const handleCheckAnswers = async () => {
    if (!quiz || isChecking) return;
    setIsChecking(true);
    try {
      const result = await checkQuizAnswers(quiz, userAnswers);
      setResults(result);
      setChecked(true);
    } finally {
      setIsChecking(false);
    }
  };

  const handleReset = () => {
    setQuiz(null);
    setUserAnswers([]);
    setChecked(false);
    setResults(null);
  };

  return (
    <section id="quiz" className="scroll-mt-20 lg:scroll-mt-8 min-h-screen py-12 lg:py-16">
      <div className="flex items-center gap-3 mb-8">
        <div className="p-2 bg-amber-100 dark:bg-amber-900/30 rounded-lg">
          <HelpCircle className="text-amber-600 dark:text-amber-500" size={24} />
        </div>
        <h2 className="text-2xl font-display font-semibold text-stone-800 dark:text-stone-100">
          Quiz
        </h2>
      </div>

      {!activeProject ? (
        <div className="bg-white dark:bg-stone-800/50 rounded-2xl p-12 border border-stone-200 dark:border-stone-700 text-center">
          <HelpCircle size={48} className="mx-auto text-stone-300 dark:text-stone-600 mb-4" />
          <p className="text-stone-500 dark:text-stone-400">
            Create or load a project to generate quizzes
          </p>
        </div>
      ) : !quiz ? (
        <div className="bg-white dark:bg-stone-800/50 rounded-2xl p-12 border border-stone-200 dark:border-stone-700 text-center">
          <button
            onClick={handleGenerateQuiz}
            disabled={isGenerating}
            className="inline-flex items-center gap-2 px-6 py-3 bg-amber-500 hover:bg-amber-600 disabled:bg-amber-300 dark:disabled:bg-amber-900 text-white font-medium rounded-xl transition-colors"
          >
            {isGenerating ? (
              <>
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles size={20} />
                Generate Quiz
              </>
            )}
          </button>
          <p className="mt-4 text-sm text-stone-500 dark:text-stone-400">
            Generate 5 multiple-choice questions based on your research
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Score display */}
          {checked && results && (
            <div className="bg-gradient-to-r from-amber-100 to-amber-50 dark:from-stone-800 dark:to-stone-800/50 rounded-2xl p-6 border border-amber-200 dark:border-stone-700">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-white dark:bg-stone-700 rounded-lg shadow-sm">
                    <CheckCircle2 size={24} className="text-green-500" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-stone-800 dark:text-stone-200">
                      {results.correct} / {results.total}
                    </p>
                    <p className="text-sm text-stone-500 dark:text-stone-400">Correct Answers</p>
                  </div>
                </div>
                <button
                  onClick={handleReset}
                  className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-stone-700 hover:bg-stone-50 dark:hover:bg-stone-600 text-stone-700 dark:text-stone-200 font-medium rounded-lg transition-colors shadow-sm"
                >
                  <RotateCcw size={18} />
                  New Quiz
                </button>
              </div>
            </div>
          )}

          {/* Questions */}
          {quiz.questions.map((question, qIndex) => {
            const userAnswer = userAnswers[qIndex];
            const isCorrect = results?.results[qIndex]?.correct;

            return (
              <div
                key={qIndex}
                className={`bg-white dark:bg-stone-800/50 rounded-2xl p-6 border transition-colors ${
                  checked
                    ? isCorrect
                      ? 'border-green-300 dark:border-green-700'
                      : 'border-red-300 dark:border-red-700'
                    : 'border-stone-200 dark:border-stone-700'
                }`}
              >
                <div className="flex items-start gap-4">
                  <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                    checked
                      ? isCorrect
                        ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400'
                        : 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400'
                      : 'bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400'
                  }`}>
                    {checked ? (
                      isCorrect ? (
                        <CheckCircle2 size={16} />
                      ) : (
                        <XCircle size={16} />
                      )
                    ) : (
                      qIndex + 1
                    )}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-stone-800 dark:text-stone-200 mb-4">
                      {question.question}
                    </p>
                    <div className="space-y-2">
                      {question.options.map((option, oIndex) => {
                        const isSelected = userAnswer === oIndex;
                        const isCorrectAnswer = question.answer === oIndex;

                        return (
                          <button
                            key={oIndex}
                            onClick={() => handleSelectAnswer(qIndex, oIndex)}
                            disabled={checked}
                            className={`w-full text-left px-4 py-3 rounded-xl border transition-all ${
                              checked
                                ? isCorrectAnswer
                                  ? 'bg-green-50 dark:bg-green-900/20 border-green-300 dark:border-green-700 text-green-800 dark:text-green-200'
                                  : isSelected
                                  ? 'bg-red-50 dark:bg-red-900/20 border-red-300 dark:border-red-700 text-red-800 dark:text-red-200'
                                  : 'border-stone-200 dark:border-stone-700 text-stone-600 dark:text-stone-400'
                                : isSelected
                                ? 'bg-amber-50 dark:bg-amber-900/20 border-amber-300 dark:border-amber-700 text-amber-800 dark:text-amber-200'
                                : 'border-stone-200 dark:border-stone-700 hover:border-amber-300 dark:hover:border-amber-700 text-stone-700 dark:text-stone-300'
                            }`}
                          >
                            <div className="flex items-center gap-3">
                              <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 ${
                                checked
                                  ? isCorrectAnswer
                                    ? 'border-green-500 bg-green-500'
                                    : isSelected
                                    ? 'border-red-500 bg-red-500'
                                    : 'border-stone-300 dark:border-stone-600'
                                  : isSelected
                                  ? 'border-amber-500 bg-amber-500'
                                  : 'border-stone-300 dark:border-stone-600'
                              }`}>
                                {(checked && (isCorrectAnswer || isSelected)) && (
                                  <div className={`w-2 h-2 rounded-full ${
                                    isCorrectAnswer ? 'bg-white' : 'bg-white'
                                  }`} />
                                )}
                              </div>
                              <span className="text-sm">{option}</span>
                            </div>
                          </button>
                        );
                      })}
                    </div>
                    {checked && question.explanation && (
                      <div className="mt-4 p-4 bg-stone-50 dark:bg-stone-900 rounded-xl">
                        <p className="text-sm text-stone-600 dark:text-stone-400">
                          <span className="font-medium text-stone-800 dark:text-stone-200">Explanation: </span>
                          {question.explanation}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}

          {/* Check Answers Button */}
          {!checked && (
            <div className="text-center">
              <button
                onClick={handleCheckAnswers}
                disabled={isChecking || userAnswers.some(a => a === -1)}
                className="inline-flex items-center gap-2 px-6 py-3 bg-amber-500 hover:bg-amber-600 disabled:bg-stone-300 dark:disabled:bg-stone-600 text-white font-medium rounded-xl transition-colors"
              >
                {isChecking ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Checking...
                  </>
                ) : (
                  <>
                    <CheckCircle2 size={20} />
                    Check Answers
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
