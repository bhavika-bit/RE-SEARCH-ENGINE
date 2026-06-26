import { useState } from 'react';
import { Layers, Sparkles, ChevronLeft, ChevronRight, RotateCw } from 'lucide-react';
import { useProject } from '../contexts/ProjectContext';
import { generateFlashcards } from '../services/api';

export default function FlashcardsSection() {
  const { activeProject, flashcards, setFlashcards, currentFlashcardIndex, setCurrentFlashcardIndex } = useProject();
  const [isGenerating, setIsGenerating] = useState(false);
  const [isFlipped, setIsFlipped] = useState(false);

  const handleGenerateFlashcards = async () => {
    if (!activeProject || isGenerating) return;
    setIsGenerating(true);
    try {
      const newFlashcards = await generateFlashcards(activeProject.project_id);
      setFlashcards(newFlashcards);
      setCurrentFlashcardIndex(0);
      setIsFlipped(false);
    } finally {
      setIsGenerating(false);
    }
  };

  const handlePrev = () => {
    if (!flashcards || currentFlashcardIndex === 0) return;
    setCurrentFlashcardIndex(currentFlashcardIndex - 1);
    setIsFlipped(false);
  };

  const handleNext = () => {
    if (!flashcards || currentFlashcardIndex === flashcards.flashcards.length - 1) return;
    setCurrentFlashcardIndex(currentFlashcardIndex + 1);
    setIsFlipped(false);
  };

  const handleFlip = () => {
    setIsFlipped(!isFlipped);
  };

  const currentCard = flashcards?.flashcards[currentFlashcardIndex];

  return (
    <section id="flashcards" className="scroll-mt-20 lg:scroll-mt-8 min-h-screen py-12 lg:py-16">
      <div className="flex items-center gap-3 mb-8">
        <div className="p-2 bg-amber-100 dark:bg-amber-900/30 rounded-lg">
          <Layers className="text-amber-600 dark:text-amber-500" size={24} />
        </div>
        <h2 className="text-2xl font-display font-semibold text-stone-800 dark:text-stone-100">
          Flashcards
        </h2>
      </div>

      {!activeProject ? (
        <div className="bg-white dark:bg-stone-800/50 rounded-2xl p-12 border border-stone-200 dark:border-stone-700 text-center">
          <Layers size={48} className="mx-auto text-stone-300 dark:text-stone-600 mb-4" />
          <p className="text-stone-500 dark:text-stone-400">
            Create or load a project to generate flashcards
          </p>
        </div>
      ) : !flashcards ? (
        <div className="bg-white dark:bg-stone-800/50 rounded-2xl p-12 border border-stone-200 dark:border-stone-700 text-center">
          <button
            onClick={handleGenerateFlashcards}
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
                Generate Flashcards
              </>
            )}
          </button>
          <p className="mt-4 text-sm text-stone-500 dark:text-stone-400">
            Generate 8 flashcards for key concepts
          </p>
        </div>
      ) : (
        <div className="flex flex-col items-center">
          {/* Flashcard */}
          <div className="perspective-1000 w-full max-w-lg">
            <div
              onClick={handleFlip}
              className={`relative w-full h-72 cursor-pointer transition-transform duration-500 preserve-3d ${
                isFlipped ? 'rotate-y-180' : ''
              }`}
              style={{
                transformStyle: 'preserve-3d',
                transform: isFlipped ? 'rotateY(180deg)' : 'rotateY(0deg)',
              }}
            >
              {/* Front */}
              <div
                className="absolute inset-0 bg-gradient-to-br from-amber-50 to-amber-100 dark:from-stone-800 dark:to-stone-900 rounded-2xl border border-amber-200 dark:border-stone-700 shadow-lg flex flex-col items-center justify-center p-8 backface-hidden"
                style={{ backfaceVisibility: 'hidden' }}
              >
                <div className="absolute top-4 right-4">
                  <RotateCw size={20} className="text-amber-400 dark:text-stone-500" />
                </div>
                <p className="text-center text-sm text-stone-500 dark:text-stone-400 mb-2">TERM</p>
                <h3 className="text-2xl font-display font-semibold text-stone-800 dark:text-stone-200 text-center">
                  {currentCard?.front}
                </h3>
              </div>

              {/* Back */}
              <div
                className="absolute inset-0 bg-gradient-to-br from-amber-500 to-amber-600 dark:from-amber-600 dark:to-amber-700 rounded-2xl border border-amber-300 dark:border-amber-800 shadow-lg flex flex-col items-center justify-center p-8 backface-hidden"
                style={{ backfaceVisibility: 'hidden', transform: 'rotateY(180deg)' }}
              >
                <div className="absolute top-4 right-4">
                  <RotateCw size={20} className="text-amber-200 dark:text-amber-300" />
                </div>
                <p className="text-center text-sm text-amber-200 dark:text-amber-300 mb-2">DEFINITION</p>
                <p className="text-lg text-white text-center leading-relaxed">
                  {currentCard?.back}
                </p>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <div className="flex items-center justify-center gap-4 mt-8">
            <button
              onClick={handlePrev}
              disabled={currentFlashcardIndex === 0}
              className="p-3 rounded-xl bg-stone-100 dark:bg-stone-800 hover:bg-stone-200 dark:hover:bg-stone-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft size={24} className="text-stone-600 dark:text-stone-400" />
            </button>

            <div className="flex items-center gap-2 px-4 py-2 bg-amber-100 dark:bg-amber-900/30 rounded-lg">
              <span className="text-sm font-medium text-amber-700 dark:text-amber-400">
                {currentFlashcardIndex + 1} / {flashcards.flashcards.length}
              </span>
            </div>

            <button
              onClick={handleNext}
              disabled={currentFlashcardIndex === flashcards.flashcards.length - 1}
              className="p-3 rounded-xl bg-stone-100 dark:bg-stone-800 hover:bg-stone-200 dark:hover:bg-stone-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronRight size={24} className="text-stone-600 dark:text-stone-400" />
            </button>
          </div>

          <p className="mt-4 text-sm text-stone-500 dark:text-stone-400">
            Click the card to flip
          </p>

          {/* Progress dots */}
          <div className="flex gap-2 mt-6">
            {flashcards.flashcards.map((_, i) => (
              <button
                key={i}
                onClick={() => {
                  setCurrentFlashcardIndex(i);
                  setIsFlipped(false);
                }}
                className={`w-2 h-2 rounded-full transition-all ${
                  i === currentFlashcardIndex
                    ? 'bg-amber-500 w-6'
                    : 'bg-stone-300 dark:bg-stone-600 hover:bg-stone-400 dark:hover:bg-stone-500'
                }`}
              />
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
