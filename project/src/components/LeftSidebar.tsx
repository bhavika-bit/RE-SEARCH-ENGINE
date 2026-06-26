import { useState, useRef, useCallback } from 'react';
import {
  Plus,
  Upload,
  FileText,
  Database,
  FolderOpen,
  ChevronDown,
  Sparkles,
  X,
  File,
  CheckCircle2,
  AlertCircle,
  Sun,
  Moon,
  Menu,
  Loader2,
} from 'lucide-react';
import { useProject } from '../contexts/ProjectContext';
import { useTheme } from '../contexts/ThemeContext';
import { createProject, loadAllProjects, importProject, uploadDocuments, indexDocuments } from '../services/api';

export default function LeftSidebar() {
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
  const { theme, toggleTheme } = useTheme();

  const [topic, setTopic] = useState('');
  const [problemStatement, setProblemStatement] = useState('');
  const [timeline, setTimeline] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [selectProjectId, setSelectProjectId] = useState('');
  const [isImporting, setIsImporting] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isIndexing, setIsIndexing] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);

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
    const project = projects.find(p => p.project_id === selectProjectId);
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

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="p-4 border-b border-stone-200 dark:border-stone-700">
        <h1 className="text-xl font-display font-semibold text-amber-600 dark:text-amber-500">
          ResearchEngine
        </h1>
        <p className="text-xs text-stone-500 dark:text-stone-400 mt-1">RAG Research Mentor</p>
      </div>

      {/* Create Project */}
      <div className="p-4 border-b border-stone-200 dark:border-stone-700">
        <div className="flex items-center gap-2 mb-3">
          <Plus size={16} className="text-amber-500" />
          <h3 className="text-sm font-medium text-stone-700 dark:text-stone-300">New Project</h3>
        </div>

        <div className="space-y-2">
          <input
            type="text"
            value={topic}
            onChange={e => setTopic(e.target.value)}
            placeholder="Topic"
            className="w-full px-3 py-2 text-sm rounded-lg border border-stone-200 dark:border-stone-600 bg-stone-50 dark:bg-stone-900 text-stone-800 dark:text-stone-200 placeholder-stone-400 focus:outline-none focus:ring-1 focus:ring-amber-500"
          />
          <textarea
            value={problemStatement}
            onChange={e => setProblemStatement(e.target.value)}
            placeholder="Problem statement"
            rows={2}
            className="w-full px-3 py-2 text-sm rounded-lg border border-stone-200 dark:border-stone-600 bg-stone-50 dark:bg-stone-900 text-stone-800 dark:text-stone-200 placeholder-stone-400 focus:outline-none focus:ring-1 focus:ring-amber-500 resize-none"
          />
          <input
            type="text"
            value={timeline}
            onChange={e => setTimeline(e.target.value)}
            placeholder="Timeline (e.g., 6 months)"
            className="w-full px-3 py-2 text-sm rounded-lg border border-stone-200 dark:border-stone-600 bg-stone-50 dark:bg-stone-900 text-stone-800 dark:text-stone-200 placeholder-stone-400 focus:outline-none focus:ring-1 focus:ring-amber-500"
          />
          <button
            onClick={handleCreateProject}
            disabled={isCreating || !topic.trim()}
            className="w-full py-2 px-3 bg-amber-500 hover:bg-amber-600 disabled:bg-stone-300 dark:disabled:bg-stone-600 text-white text-sm font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            {isCreating ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <Sparkles size={16} />
            )}
            Create
          </button>
        </div>
      </div>

      {/* Resume Project */}
      <div className="p-4 border-b border-stone-200 dark:border-stone-700">
        <div className="flex items-center gap-2 mb-3">
          <Database size={16} className="text-amber-500" />
          <h3 className="text-sm font-medium text-stone-700 dark:text-stone-300">Resume</h3>
        </div>

        <div className="relative">
          <button
            onClick={() => {
              setIsDropdownOpen(!isDropdownOpen);
              loadAllProjects().then(setProjects);
            }}
            className="w-full px-3 py-2 text-sm rounded-lg border border-stone-200 dark:border-stone-600 bg-stone-50 dark:bg-stone-900 text-stone-800 dark:text-stone-200 text-left flex items-center justify-between"
          >
            <span className="truncate">
              {selectProjectId
                ? projects.find(p => p.project_id === selectProjectId)?.topic?.slice(0, 20) + '...'
                : 'Select project'}
            </span>
            <ChevronDown size={14} className={`transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`} />
          </button>

          {isDropdownOpen && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-stone-800 border border-stone-200 dark:border-stone-600 rounded-lg shadow-lg max-h-32 overflow-auto z-10">
              {projects.length === 0 ? (
                <div className="px-3 py-2 text-xs text-stone-500">No projects found</div>
              ) : (
                projects.map(project => (
                  <button
                    key={project.project_id}
                    onClick={() => {
                      setSelectProjectId(project.project_id);
                      setIsDropdownOpen(false);
                    }}
                    className="w-full px-3 py-2 text-left hover:bg-amber-50 dark:hover:bg-stone-700 text-xs text-stone-700 dark:text-stone-300 truncate"
                  >
                    {project.topic}
                  </button>
                ))
              )}
            </div>
          )}
        </div>

        {selectProjectId && (
          <button
            onClick={handleLoadProject}
            className="w-full mt-2 py-2 px-3 bg-stone-200 dark:bg-stone-700 hover:bg-stone-300 dark:hover:bg-stone-600 text-stone-700 dark:text-stone-200 text-sm font-medium rounded-lg transition-colors"
          >
            Load
          </button>
        )}
      </div>

      {/* Import Project */}
      <div className="p-4 border-b border-stone-200 dark:border-stone-700">
        <div className="flex items-center gap-2 mb-3">
          <Upload size={16} className="text-amber-500" />
          <h3 className="text-sm font-medium text-stone-700 dark:text-stone-300">Import</h3>
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
          className="w-full py-2 px-3 border border-dashed border-stone-300 dark:border-stone-600 hover:border-amber-400 dark:hover:border-amber-500 rounded-lg text-stone-600 dark:text-stone-400 text-sm transition-colors flex items-center justify-center gap-2"
        >
          {isImporting ? (
            <Loader2 size={14} className="animate-spin" />
          ) : (
            <FileText size={14} />
          )}
          Import JSON
        </button>
      </div>

      {/* Document Upload */}
      <div className="p-4 flex-1 overflow-auto">
        <div className="flex items-center gap-2 mb-3">
          <FolderOpen size={16} className="text-amber-500" />
          <h3 className="text-sm font-medium text-stone-700 dark:text-stone-300">Documents</h3>
        </div>

        <div
          onDragOver={e => e.preventDefault()}
          onDrop={handleFileDrop}
          className="border border-dashed border-stone-300 dark:border-stone-600 rounded-lg p-4 text-center hover:border-amber-400 dark:hover:border-amber-500 transition-colors"
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
            <div className="flex items-center justify-center gap-2">
              <Loader2 size={14} className="animate-spin text-amber-500" />
              <span className="text-xs text-stone-500">Uploading...</span>
            </div>
          ) : (
            <>
              <Upload size={20} className="mx-auto text-stone-400 mb-2" />
              <button
                onClick={() => fileInputRef.current?.click()}
                className="text-xs text-amber-600 dark:text-amber-400 hover:underline"
              >
                Drop files or browse
              </button>
              <p className="text-[10px] text-stone-400 mt-1">PDF, TXT, CSV, DOCX</p>
            </>
          )}
        </div>

        {uploadedFiles.length > 0 && (
          <div className="mt-3 space-y-1">
            {uploadedFiles.map((file, i) => (
              <div
                key={i}
                className="flex items-center gap-1.5 px-2 py-1.5 bg-stone-100 dark:bg-stone-800 rounded text-xs"
              >
                <File size={12} className="text-amber-500 flex-shrink-0" />
                <span className="text-stone-700 dark:text-stone-300 truncate">{file.name}</span>
              </div>
            ))}
          </div>
        )}

        {uploadedFiles.length > 0 && (
          <button
            onClick={handleIndexDocuments}
            disabled={isIndexing || !activeProject}
            className="w-full mt-3 py-2 px-3 bg-amber-500 hover:bg-amber-600 disabled:bg-stone-300 dark:disabled:bg-stone-600 text-white text-sm font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            {isIndexing ? (
              <>
                <Loader2 size={14} className="animate-spin" />
                Indexing...
              </>
            ) : (
              <>
                <Database size={14} />
                Index Docs
              </>
            )}
          </button>
        )}

        {documentStatus && (
          <div className="mt-2 flex items-center gap-1.5 text-xs">
            {documentStatus.includes('failed') ? (
              <AlertCircle size={12} className="text-red-500" />
            ) : (
              <CheckCircle2 size={12} className="text-green-500" />
            )}
            <span className="text-stone-500 dark:text-stone-400">{documentStatus}</span>
          </div>
        )}
      </div>

      {/* Theme toggle */}
      <div className="p-4 border-t border-stone-200 dark:border-stone-700">
        <button
          onClick={toggleTheme}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-stone-600 dark:text-stone-400 hover:bg-stone-100 dark:hover:bg-stone-800 transition-colors"
        >
          {theme === 'light' ? <Moon size={16} /> : <Sun size={16} />}
          <span className="text-sm">{theme === 'light' ? 'Dark' : 'Light'} Mode</span>
        </button>
      </div>
    </div>
  );

  return (
    <>
      {/* Mobile Header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-50 bg-amber-50/95 dark:bg-stone-900/95 backdrop-blur-sm border-b border-stone-200 dark:border-stone-700 px-4 py-3 flex items-center justify-between">
        <h1 className="text-lg font-display font-semibold text-amber-600 dark:text-amber-500">
          ResearchEngine
        </h1>
        <button
          onClick={() => setIsMobileOpen(!isMobileOpen)}
          className="p-2 rounded-lg text-stone-600 dark:text-stone-400 hover:bg-stone-100 dark:hover:bg-stone-800 transition-colors"
        >
          {isMobileOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Mobile Drawer */}
      {isMobileOpen && (
        <div className="lg:hidden fixed inset-0 z-40 pt-16">
          <div
            className="absolute inset-0 bg-black/20 dark:bg-black/40"
            onClick={() => setIsMobileOpen(false)}
          />
          <div className="absolute top-16 left-0 bottom-0 w-72 bg-amber-50 dark:bg-stone-900 border-r border-stone-200 dark:border-stone-700 overflow-auto">
            <SidebarContent />
          </div>
        </div>
      )}

      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex fixed left-0 top-0 bottom-0 w-72 bg-amber-50 dark:bg-stone-900 border-r border-stone-200 dark:border-stone-700 z-30">
        <SidebarContent />
      </aside>
    </>
  );
}
