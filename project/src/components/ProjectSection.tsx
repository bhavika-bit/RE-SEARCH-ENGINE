import { useState, useRef, useCallback } from 'react';
import {
  FolderOpen,
  Plus,
  Upload,
  FileText,
  Database,
  ChevronDown,
  Sparkles,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react';
import { useProject } from '../contexts/ProjectContext';
import {
  createProject,
  loadAllProjects,
  loadProject,
  uploadDocuments,
  indexDocuments,
  importProject,
} from '../services/api';
import { getTopicTheme } from '../utils/topicTheme';

export default function ProjectSection() {
  const {
    activeProject,
    setActiveProject,
    projects,
    setProjects,
    documentStatus,
    setDocumentStatus,
    uploadedFiles,
    setUploadedFiles,
  } = useProject();

  const [topic, setTopic] = useState('');
  const [problemStatement, setProblemStatement] = useState('');
  const [timeline, setTimeline] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [selectProjectId, setSelectProjectId] = useState('');
  const [isImporting, setIsImporting] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isIndexing, setIsIndexing] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const importInputRef = useRef<HTMLInputElement>(null);

  const handleCreateProject = async () => {
    if (!topic.trim()) return;
    setIsCreating(true);
    try {
      const project = await createProject(topic, problemStatement, timeline);
      setActiveProject(project);
      setTopic('');
      setProblemStatement('');
      setTimeline('');
      const allProjects = await loadAllProjects();
      setProjects(allProjects);
    } finally {
      setIsCreating(false);
    }
  };

  const handleLoadProject = async () => {
    if (!selectProjectId) return;
    const project = await loadProject(selectProjectId);
    if (project) {
      setActiveProject(project);
      setSelectProjectId('');
    }
  };

  const handleImportProject = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsImporting(true);
    try {
      const text = await file.text();
      const project = await importProject(text);
      setActiveProject(project);
      const allProjects = await loadAllProjects();
      setProjects(allProjects);
    } catch (err) {
      console.error('Import failed:', err);
    } finally {
      setIsImporting(false);
      if (importInputRef.current) importInputRef.current.value = '';
    }
  };

  const handleFileDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      const files = Array.from(e.dataTransfer.files).filter(
        f =>
          f.type === 'application/pdf' ||
          f.type === 'text/plain' ||
          f.type === 'text/csv' ||
          f.name.endsWith('.docx')
      );
      if (files.length > 0) {
        setUploadedFiles(files);
        setIsUploading(true);
        await uploadDocuments(files);
        setIsUploading(false);
        setDocumentStatus(`${files.length} file(s) ready to index`);
      }
    },
    [setUploadedFiles, setDocumentStatus]
  );

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      setUploadedFiles(files);
      setIsUploading(true);
      await uploadDocuments(files);
      setIsUploading(false);
      setDocumentStatus(`${files.length} file(s) ready to index`);
    }
  };

  const handleIndexDocuments = async () => {
    if (!activeProject || uploadedFiles.length === 0) return;
    setIsIndexing(true);
    setDocumentStatus('Indexing documents...');
    try {
      const result = await indexDocuments(activeProject.project_id);
      setDocumentStatus(result.message);
    } catch {
      setDocumentStatus('Indexing failed. Please try again.');
    } finally {
      setIsIndexing(false);
    }
  };

  const loadProjectsList = async () => {
    const allProjects = await loadAllProjects();
    setProjects(allProjects);
  };

  const topicTheme = activeProject ? getTopicTheme(activeProject.topic) : null;

  return (
    <section id="project" className="scroll-mt-20 lg:scroll-mt-8 min-h-screen py-12 lg:py-16">
      <div className="flex items-center gap-3 mb-8">
        <div className="p-2 bg-amber-100 dark:bg-amber-900/30 rounded-lg">
          <FolderOpen className="text-amber-600 dark:text-amber-500" size={24} />
        </div>
        <h2 className="text-2xl font-display font-semibold text-stone-800 dark:text-stone-100">
          Project
        </h2>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Create New Project */}
        <div className="bg-white dark:bg-stone-800/50 rounded-2xl p-6 border border-stone-200 dark:border-stone-700 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <Plus size={18} className="text-amber-500" />
            <h3 className="font-medium text-stone-800 dark:text-stone-200">Create New Project</h3>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm text-stone-600 dark:text-stone-400 mb-1.5">
                Topic
              </label>
              <input
                type="text"
                value={topic}
                onChange={e => setTopic(e.target.value)}
                placeholder="e.g., Deep Learning for Medical Imaging"
                className="w-full px-4 py-2.5 rounded-xl border border-stone-200 dark:border-stone-600 bg-stone-50 dark:bg-stone-900 text-stone-800 dark:text-stone-200 placeholder-stone-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
              />
            </div>

            <div>
              <label className="block text-sm text-stone-600 dark:text-stone-400 mb-1.5">
                Problem Statement
              </label>
              <textarea
                value={problemStatement}
                onChange={e => setProblemStatement(e.target.value)}
                placeholder="Describe the research problem you want to solve..."
                rows={3}
                className="w-full px-4 py-2.5 rounded-xl border border-stone-200 dark:border-stone-600 bg-stone-50 dark:bg-stone-900 text-stone-800 dark:text-stone-200 placeholder-stone-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all resize-none"
              />
            </div>

            <div>
              <label className="block text-sm text-stone-600 dark:text-stone-400 mb-1.5">
                Timeline
              </label>
              <input
                type="text"
                value={timeline}
                onChange={e => setTimeline(e.target.value)}
                placeholder="e.g., 6 months"
                className="w-full px-4 py-2.5 rounded-xl border border-stone-200 dark:border-stone-600 bg-stone-50 dark:bg-stone-900 text-stone-800 dark:text-stone-200 placeholder-stone-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
              />
            </div>

            <button
              onClick={handleCreateProject}
              disabled={isCreating || !topic.trim()}
              className="w-full py-2.5 px-4 bg-amber-500 hover:bg-amber-600 disabled:bg-stone-300 dark:disabled:bg-stone-600 text-white font-medium rounded-xl transition-colors flex items-center justify-center gap-2"
            >
              {isCreating ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <Sparkles size={18} />
                  Create Project
                </>
              )}
            </button>
          </div>
        </div>

        {/* Resume / Import Project */}
        <div className="space-y-6">
          {/* Resume Project */}
          <div className="bg-white dark:bg-stone-800/50 rounded-2xl p-6 border border-stone-200 dark:border-stone-700 shadow-sm">
            <div className="flex items-center gap-2 mb-4">
              <Database size={18} className="text-amber-500" />
              <h3 className="font-medium text-stone-800 dark:text-stone-200">Resume Project</h3>
            </div>

            <div className="flex gap-2">
              <div className="relative flex-1">
                <button
                  onClick={() => {
                    setIsDropdownOpen(!isDropdownOpen);
                    loadProjectsList();
                  }}
                  className="w-full px-4 py-2.5 rounded-xl border border-stone-200 dark:border-stone-600 bg-stone-50 dark:bg-stone-900 text-stone-800 dark:text-stone-200 text-left flex items-center justify-between"
                >
                  <span className={selectProjectId ? '' : 'text-stone-400'}>
                    {selectProjectId
                      ? projects.find(p => p.project_id === selectProjectId)?.topic?.slice(0, 30) + '...'
                      : 'Select a project'}
                  </span>
                  <ChevronDown
                    size={18}
                    className={`transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`}
                  />
                </button>

                {isDropdownOpen && (
                  <div className="absolute top-full left-0 right-0 mt-2 bg-white dark:bg-stone-800 border border-stone-200 dark:border-stone-600 rounded-xl shadow-lg max-h-48 overflow-auto z-10">
                    {projects.length === 0 ? (
                      <div className="px-4 py-3 text-sm text-stone-500">No projects found</div>
                    ) : (
                      projects.map(project => (
                        <button
                          key={project.project_id}
                          onClick={() => {
                            setSelectProjectId(project.project_id);
                            setIsDropdownOpen(false);
                          }}
                          className="w-full px-4 py-2.5 text-left hover:bg-amber-50 dark:hover:bg-stone-700 text-sm text-stone-700 dark:text-stone-300"
                        >
                          {project.topic}
                        </button>
                      ))
                    )}
                  </div>
                )}
              </div>

              <button
                onClick={handleLoadProject}
                disabled={!selectProjectId}
                className="px-4 py-2.5 bg-stone-200 dark:bg-stone-700 hover:bg-stone-300 dark:hover:bg-stone-600 disabled:opacity-50 text-stone-700 dark:text-stone-200 font-medium rounded-xl transition-colors"
              >
                Load
              </button>
            </div>
          </div>

          {/* Import Project */}
          <div className="bg-white dark:bg-stone-800/50 rounded-2xl p-6 border border-stone-200 dark:border-stone-700 shadow-sm">
            <div className="flex items-center gap-2 mb-4">
              <Upload size={18} className="text-amber-500" />
              <h3 className="font-medium text-stone-800 dark:text-stone-200">Import Project</h3>
            </div>

            <input
              ref={importInputRef}
              type="file"
              accept=".json"
              onChange={handleImportProject}
              className="hidden"
            />

            <button
              onClick={() => importInputRef.current?.click()}
              disabled={isImporting}
              className="w-full py-2.5 px-4 border-2 border-dashed border-stone-300 dark:border-stone-600 hover:border-amber-400 dark:hover:border-amber-500 rounded-xl text-stone-600 dark:text-stone-400 transition-colors flex items-center justify-center gap-2"
            >
              {isImporting ? (
                <div className="w-5 h-5 border-2 border-stone-400/30 border-t-stone-400 rounded-full animate-spin" />
              ) : (
                <>
                  <FileText size={18} />
                  Import from JSON
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Document Upload */}
      <div className="mt-6 bg-white dark:bg-stone-800/50 rounded-2xl p-6 border border-stone-200 dark:border-stone-700 shadow-sm">
        <div className="flex items-center gap-2 mb-4">
          <Upload size={18} className="text-amber-500" />
          <h3 className="font-medium text-stone-800 dark:text-stone-200">Document Upload</h3>
        </div>

        <div
          onDragOver={e => e.preventDefault()}
          onDrop={handleFileDrop}
          className="border-2 border-dashed border-stone-300 dark:border-stone-600 rounded-xl p-8 text-center hover:border-amber-400 dark:hover:border-amber-500 transition-colors"
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.txt,.csv,.docx"
            multiple
            onChange={handleFileSelect}
            className="hidden"
          />

          {isUploading ? (
            <div className="flex items-center justify-center gap-3">
              <div className="w-6 h-6 border-2 border-amber-500/30 border-t-amber-500 rounded-full animate-spin" />
              <span className="text-stone-600 dark:text-stone-400">Uploading files...</span>
            </div>
          ) : (
            <>
              <p className="text-stone-600 dark:text-stone-400 mb-3">
                Drag and drop files here, or{' '}
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="text-amber-600 dark:text-amber-400 hover:underline"
                >
                  browse
                </button>
              </p>
              <p className="text-sm text-stone-400">Supports PDF, TXT, CSV, DOCX</p>
            </>
          )}
        </div>

        {uploadedFiles.length > 0 && (
          <div className="mt-4 space-y-2">
            {uploadedFiles.map((file, i) => (
              <div
                key={i}
                className="flex items-center gap-2 px-3 py-2 bg-stone-100 dark:bg-stone-900 rounded-lg text-sm"
              >
                <FileText size={16} className="text-amber-500" />
                <span className="text-stone-700 dark:text-stone-300">{file.name}</span>
              </div>
            ))}
          </div>
        )}

        <div className="mt-4 flex items-center gap-4">
          <button
            onClick={handleIndexDocuments}
            disabled={isIndexing || uploadedFiles.length === 0 || !activeProject}
            className="py-2.5 px-6 bg-amber-500 hover:bg-amber-600 disabled:bg-stone-300 dark:disabled:bg-stone-600 text-white font-medium rounded-xl transition-colors flex items-center gap-2"
          >
            {isIndexing ? (
              <>
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Indexing...
              </>
            ) : (
              <>
                <Database size={18} />
                Index Documents
              </>
            )}
          </button>

          {documentStatus && (
            <span className="text-sm text-stone-600 dark:text-stone-400 flex items-center gap-2">
              {documentStatus.includes('failed') ? (
                <AlertCircle size={16} className="text-red-500" />
              ) : (
                <CheckCircle2 size={16} className="text-green-500" />
              )}
              {documentStatus}
            </span>
          )}
        </div>
      </div>

      {/* Active Project Status */}
      {activeProject && (
        <div className="mt-6 bg-gradient-to-r from-amber-100 to-amber-50 dark:from-stone-800 dark:to-stone-800/50 rounded-2xl p-6 border border-amber-200 dark:border-stone-700 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <CheckCircle2 size={18} className="text-amber-600 dark:text-amber-400" />
            <h3 className="font-medium text-stone-800 dark:text-stone-200">Active Project</h3>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <label className="text-xs text-stone-500 dark:text-stone-400 uppercase tracking-wide">
                Project ID
              </label>
              <p className="text-stone-800 dark:text-stone-200 font-mono text-sm">
                {activeProject.project_id}
              </p>
            </div>

            <div className="sm:col-span-2">
              <label className="text-xs text-stone-500 dark:text-stone-400 uppercase tracking-wide">
                Topic
              </label>
              <p className="text-stone-800 dark:text-stone-200 text-sm">{activeProject.topic}</p>
            </div>

            <div>
              <label className="text-xs text-stone-500 dark:text-stone-400 uppercase tracking-wide">
                Chat Theme
              </label>
              <div className="flex items-center gap-2 mt-1">
                {topicTheme && (
                  <>
                    <div
                      className="w-4 h-4 rounded-full"
                      style={{ backgroundColor: topicTheme.accentColor }}
                    />
                    <topicTheme.icon size={16} style={{ color: topicTheme.accentColor }} />
                    <span className="text-sm text-stone-600 dark:text-stone-400">
                      {topicTheme.name}
                    </span>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
