import { useState, useRef, useEffect, useCallback } from 'react';
import {
  CheckCircle2,
  MessageSquare,
  Send,
  User,
  Bot,
  Upload,
  File,
  FileText,
} from 'lucide-react';
import { useProject } from '../contexts/ProjectContext';
import { sendChatMessage, uploadDocuments } from '../services/api';
import { getTopicTheme } from '../utils/topicTheme';
import { Message } from '../services/api';

export default function CenterContent() {
  const { activeProject, chatHistory, addMessage, uploadedFiles, setUploadedFiles, setDocumentStatus } = useProject();
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const topicTheme = activeProject ? getTopicTheme(activeProject.topic) : null;

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  const handleSend = async () => {
    if (!input.trim() || !activeProject || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString(),
    };

    addMessage(userMessage);
    setInput('');
    setIsLoading(true);

    try {
      const response = await sendChatMessage(activeProject.project_id, input.trim(), chatHistory);
      addMessage(response);
    } catch (error) {
      console.error('Chat error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;

    setIsUploading(true);
    try {
      await uploadDocuments(files);
      setUploadedFiles([...uploadedFiles, ...files]);
      setDocumentStatus(`${files.length} file(s) uploaded`);

      const fileNames = files.map(f => f.name).join(', ');
      const systemMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'user',
        content: `[Uploaded files: ${fileNames}]`,
        timestamp: new Date().toISOString(),
      };
      addMessage(systemMessage);
    } catch (error) {
      console.error('Upload error:', error);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      const files = Array.from(e.dataTransfer.files).filter(
        f =>
          f.type === 'application/pdf' ||
          f.type === 'text/plain' ||
          f.type === 'text/csv' ||
          f.name.endsWith('.docx')
      );
      if (files.length === 0) return;

      setIsUploading(true);
      try {
        await uploadDocuments(files);
        setUploadedFiles([...uploadedFiles, ...files]);
        setDocumentStatus(`${files.length} file(s) uploaded`);

        const fileNames = files.map(f => f.name).join(', ');
        const systemMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'user',
          content: `[Uploaded files: ${fileNames}]`,
          timestamp: new Date().toISOString(),
        };
        addMessage(systemMessage);
      } catch (error) {
        console.error('Upload error:', error);
      } finally {
        setIsUploading(false);
      }
    },
    [addMessage, setUploadedFiles, setDocumentStatus, uploadedFiles]
  );

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  return (
    <div className="flex flex-col h-full">
      {/* Active Project Banner */}
      {activeProject && (
        <div className="bg-gradient-to-r from-amber-100 to-amber-50 dark:from-stone-800 dark:to-stone-800/50 border-b border-amber-200 dark:border-stone-700 p-4">
          <div className="flex items-start gap-3">
            <div className="p-2 bg-white dark:bg-stone-700 rounded-lg shadow-sm">
              <CheckCircle2 size={20} className="text-green-500" />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-medium text-stone-800 dark:text-stone-200 truncate">
                {activeProject.topic}
              </h3>
              <p className="text-sm text-stone-500 dark:text-stone-400 line-clamp-2 mt-1">
                {activeProject.problem_statement}
              </p>
              <div className="flex items-center gap-4 mt-2">
                <span className="text-xs text-stone-400">
                  ID: <span className="font-mono">{activeProject.project_id}</span>
                </span>
                <span className="text-xs text-stone-400">
                  Timeline: {activeProject.timeline}
                </span>
                {topicTheme && (
                  <div className="flex items-center gap-1.5">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: topicTheme.accentColor }}
                    />
                    <topicTheme.icon size={12} style={{ color: topicTheme.accentColor }} />
                    <span className="text-xs text-stone-500">{topicTheme.name}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Themed Header */}
      {activeProject && topicTheme && (
        <div
          className="px-4 py-3 flex items-center gap-3"
          style={{
            background: `linear-gradient(135deg, ${topicTheme.gradientFrom}15, ${topicTheme.gradientTo}08)`,
            borderBottom: `2px solid ${topicTheme.accentColor}40`,
          }}
        >
          <topicTheme.icon size={24} style={{ color: topicTheme.accentColor }} />
          <div>
            <h3 className="font-medium text-stone-800 dark:text-stone-200">Research Chat</h3>
            <p className="text-xs text-stone-500 dark:text-stone-400">Discuss your research with AI mentor</p>
          </div>
        </div>
      )}

      {/* Chat Section */}
      <div className="flex-1 flex flex-col min-h-0">
        {!activeProject ? (
          <div className="flex-1 flex items-center justify-center p-8">
            <div className="text-center max-w-md">
              <div className="w-20 h-20 mx-auto bg-amber-100 dark:bg-amber-900/30 rounded-2xl flex items-center justify-center mb-4">
                <MessageSquare size={40} className="text-amber-500" />
              </div>
              <h3 className="text-xl font-display font-semibold text-stone-800 dark:text-stone-200 mb-2">
                Welcome to ResearchEngine
              </h3>
              <p className="text-stone-500 dark:text-stone-400 text-sm">
                Create a new project or load an existing one from the left sidebar to start your research journey.
              </p>
            </div>
          </div>
        ) : (
          <>
            {/* Messages */}
            <div
              className="flex-1 overflow-y-auto p-4 space-y-4"
              onDragOver={handleDragOver}
              onDrop={handleDrop}
            >
              {chatHistory.length === 0 ? (
                <div className="text-center py-16">
                  <div className="w-16 h-16 mx-auto bg-stone-100 dark:bg-stone-800 rounded-2xl flex items-center justify-center mb-4">
                    <Bot size={32} className="text-stone-400" />
                  </div>
                  <p className="text-stone-500 dark:text-stone-400 mb-4">
                    Start a conversation about your research
                  </p>
                  <p className="text-xs text-stone-400">
                    You can also drag & drop files here to upload them
                  </p>
                </div>
              ) : (
                chatHistory.map(message => (
                  <div
                    key={message.id}
                    className={`flex gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
                  >
                    <div
                      className={`w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 ${
                        message.role === 'user'
                          ? 'bg-amber-100 dark:bg-amber-900/30'
                          : 'bg-stone-100 dark:bg-stone-700'
                      }`}
                    >
                      {message.role === 'user' ? (
                        <User size={18} className="text-amber-600 dark:text-amber-400" />
                      ) : (
                        <Bot
                          size={18}
                          style={topicTheme ? { color: topicTheme.accentColor } : undefined}
                          className="text-stone-600 dark:text-stone-400"
                        />
                      )}
                    </div>
                    <div
                      className={`max-w-[75%] px-4 py-3 rounded-2xl ${
                        message.content.startsWith('[Uploaded files:')
                          ? 'bg-stone-100 dark:bg-stone-700 text-stone-500 dark:text-stone-400 text-sm border border-dashed border-stone-300 dark:border-stone-600'
                          : message.role === 'user'
                          ? 'bg-amber-500 text-white'
                          : 'bg-stone-100 dark:bg-stone-700 text-stone-800 dark:text-stone-200'
                      }`}
                      style={
                        message.role === 'assistant' && topicTheme && !message.content.startsWith('[Uploaded files:')
                          ? {
                              backgroundColor: `${topicTheme.accentColor}12`,
                              borderLeft: `3px solid ${topicTheme.accentColor}`,
                            }
                          : undefined
                      }
                    >
                      {message.content.startsWith('[Uploaded files:') ? (
                        <div className="flex items-center gap-2">
                          <File size={14} />
                          <span>{message.content}</span>
                        </div>
                      ) : (
                        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                      )}
                    </div>
                  </div>
                ))
              )}
              {isLoading && (
                <div className="flex gap-3">
                  <div className="w-9 h-9 rounded-full bg-stone-100 dark:bg-stone-700 flex items-center justify-center">
                    <Bot size={18} className="text-stone-600 dark:text-stone-400" />
                  </div>
                  <div className="bg-stone-100 dark:bg-stone-700 px-4 py-3 rounded-2xl">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-stone-400 rounded-full animate-bounce" />
                      <div className="w-2 h-2 bg-stone-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                      <div className="w-2 h-2 bg-stone-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Drop zone indicator */}
            {isUploading && (
              <div className="absolute inset-0 bg-amber-500/10 flex items-center justify-center z-10">
                <div className="bg-white dark:bg-stone-800 rounded-2xl p-6 shadow-xl flex items-center gap-3">
                  <Upload size={24} className="text-amber-500 animate-pulse" />
                  <span className="font-medium text-stone-700 dark:text-stone-200">Uploading files...</span>
                </div>
              </div>
            )}

            {/* Input Area */}
            <div className="border-t border-stone-200 dark:border-stone-700 p-4 bg-white dark:bg-stone-800/50">
              {/* Uploading indicator */}
              {isUploading && (
                <div className="mb-3 px-3 py-2 bg-amber-50 dark:bg-amber-900/20 rounded-lg flex items-center gap-2">
                  <Upload size={14} className="text-amber-500 animate-pulse" />
                  <span className="text-sm text-amber-700 dark:text-amber-400">Uploading files...</span>
                </div>
              )}

              {/* File upload button */}
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.txt,.csv,.docx"
                multiple
                onChange={handleFileSelect}
                className="hidden"
              />

              <div className="flex gap-2">
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isUploading}
                  className="p-3 bg-stone-100 dark:bg-stone-700 hover:bg-stone-200 dark:hover:bg-stone-600 rounded-xl text-stone-600 dark:text-stone-400 transition-colors disabled:opacity-50"
                  title="Upload files"
                >
                  <FileText size={20} />
                </button>

                <div className="flex-1 relative">
                  <input
                    type="text"
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask about your research... (or drop files here)"
                    className="w-full px-4 py-3 pr-14 rounded-xl border border-stone-200 dark:border-stone-600 bg-stone-50 dark:bg-stone-900 text-stone-800 dark:text-stone-200 placeholder-stone-400 focus:outline-none focus:ring-2 focus:ring-amber-500 dark:focus:ring-amber-400 transition-all"
                  />
                  <button
                    onClick={handleSend}
                    disabled={!input.trim() || isLoading}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-amber-500 hover:bg-amber-600 disabled:bg-stone-300 dark:disabled:bg-stone-600 text-white rounded-lg transition-colors"
                  >
                    <Send size={18} />
                  </button>
                </div>
              </div>

              <p className="text-xs text-stone-400 mt-2 text-center">
                Press Enter to send. Drag & drop files anywhere to upload.
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
