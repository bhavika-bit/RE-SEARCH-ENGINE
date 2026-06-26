import { useState } from 'react';
import {
  Wrench,
  Map,
  Search,
  BookOpen,
  Cpu,
  FileText,
  Compass,
  MessageCircle,
  FileBarChart,
  Loader2,
} from 'lucide-react';
import { useProject } from '../contexts/ProjectContext';
import { runTool } from '../services/api';
import MarkdownRenderer from './MarkdownRenderer';

const tools = [
  { id: 'roadmap', name: 'Project Roadmap', icon: Map, description: 'Generate week-by-week project timeline' },
  { id: 'gap_analysis', name: 'Research Gap Analysis', icon: Search, description: 'Identify novel research opportunities' },
  { id: 'learning_path', name: 'Learning Path', icon: BookOpen, description: 'Build personalized learning roadmap' },
  { id: 'methodology', name: 'Methodology', icon: Cpu, description: 'Design complete research methodology' },
  { id: 'paper_intelligence', name: 'Paper Intelligence', icon: FileText, description: 'Analyze and compare research papers' },
  { id: 'research_discovery', name: 'Research Discovery', icon: Compass, description: 'Map the research landscape' },
  { id: 'mentor_review', name: 'Research Mentor Review', icon: MessageCircle, description: 'Get expert project feedback' },
  { id: 'project_summary', name: 'Project Summary', icon: FileBarChart, description: 'Generate executive summary' },
];

export default function ToolsSection() {
  const { activeProject, addToolResult, toolResults } = useProject();
  const [runningTool, setRunningTool] = useState<string | null>(null);
  const [activeResult, setActiveResult] = useState<string | null>(null);

  const handleRunTool = async (toolId: string) => {
    if (!activeProject || runningTool) return;

    setRunningTool(toolId);
    try {
      const result = await runTool(activeProject.project_id, toolId);
      addToolResult(result);
      setActiveResult(toolId);
    } catch (error) {
      console.error('Tool error:', error);
    } finally {
      setRunningTool(null);
    }
  };

  const latestResult = toolResults.find(r => r.tool === activeResult);

  return (
    <section id="tools" className="scroll-mt-20 lg:scroll-mt-8 min-h-screen py-12 lg:py-16">
      <div className="flex items-center gap-3 mb-8">
        <div className="p-2 bg-amber-100 dark:bg-amber-900/30 rounded-lg">
          <Wrench className="text-amber-600 dark:text-amber-500" size={24} />
        </div>
        <h2 className="text-2xl font-display font-semibold text-stone-800 dark:text-stone-100">
          Tools
        </h2>
      </div>

      {!activeProject ? (
        <div className="bg-white dark:bg-stone-800/50 rounded-2xl p-12 border border-stone-200 dark:border-stone-700 text-center">
          <Wrench size={48} className="mx-auto text-stone-300 dark:text-stone-600 mb-4" />
          <p className="text-stone-500 dark:text-stone-400">
            Create or load a project to use research tools
          </p>
        </div>
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {tools.map(tool => {
              const Icon = tool.icon;
              const isRunning = runningTool === tool.id;
              const hasResult = toolResults.some(r => r.tool === tool.id);

              return (
                <button
                  key={tool.id}
                  onClick={() => handleRunTool(tool.id)}
                  disabled={runningTool !== null}
                  className={`p-5 rounded-2xl border text-left transition-all ${
                    activeResult === tool.id
                      ? 'bg-amber-50 dark:bg-amber-900/20 border-amber-300 dark:border-amber-700'
                      : hasResult
                      ? 'bg-green-50 dark:bg-green-900/10 border-green-200 dark:border-green-800'
                      : 'bg-white dark:bg-stone-800/50 border-stone-200 dark:border-stone-700 hover:border-amber-300 dark:hover:border-amber-700'
                  } ${runningTool && runningTool !== tool.id ? 'opacity-50' : ''}`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className={`p-2 rounded-lg ${
                      activeResult === tool.id
                        ? 'bg-amber-200 dark:bg-amber-800/40'
                        : 'bg-stone-100 dark:bg-stone-700'
                    }`}>
                      {isRunning ? (
                        <Loader2 size={20} className="text-amber-600 dark:text-amber-400 animate-spin" />
                      ) : (
                        <Icon
                          size={20}
                          className={activeResult === tool.id
                            ? 'text-amber-600 dark:text-amber-400'
                            : 'text-stone-600 dark:text-stone-400'
                          }
                        />
                      )}
                    </div>
                    {hasResult && activeResult !== tool.id && (
                      <div className="w-2 h-2 bg-green-500 rounded-full" />
                    )}
                  </div>
                  <h3 className="font-medium text-stone-800 dark:text-stone-200 mb-1">
                    {tool.name}
                  </h3>
                  <p className="text-xs text-stone-500 dark:text-stone-400">
                    {tool.description}
                  </p>
                </button>
              );
            })}
          </div>

          {/* Tool Result */}
          {latestResult && (
            <div className="mt-8 bg-white dark:bg-stone-800/50 rounded-2xl p-6 border border-stone-200 dark:border-stone-700">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-amber-100 dark:bg-amber-900/30 rounded-lg">
                  {(() => {
                    const tool = tools.find(t => t.id === latestResult.tool);
                    const Icon = tool?.icon || Wrench;
                    return <Icon size={20} className="text-amber-600 dark:text-amber-400" />;
                  })()}
                </div>
                <div>
                  <h3 className="font-medium text-stone-800 dark:text-stone-200">
                    {tools.find(t => t.id === latestResult.tool)?.name || 'Tool Result'}
                  </h3>
                  <p className="text-xs text-stone-500">
                    Completed at {new Date(latestResult.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              </div>
              <div className="prose dark:prose-invert max-w-none">
                <MarkdownRenderer content={latestResult.result} />
              </div>
            </div>
          )}
        </>
      )}
    </section>
  );
}
