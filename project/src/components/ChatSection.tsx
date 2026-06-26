import { useState, useRef, useEffect } from 'react';
import { MessageSquare, Send, Trash2, Download, User, Bot } from 'lucide-react';
import { useProject } from '../contexts/ProjectContext';
import { sendChatMessage, exportProject } from '../services/api';
import { getTopicTheme } from '../utils/topicTheme';
import { Message } from '../services/api';

export default function ChatSection() {
  const { activeProject, chatHistory, addMessage, clearChat } = useProject();
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

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

  const handleExport = async () => {
    if (!activeProject) return;
    const data = await exportProject(activeProject.project_id);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat_${activeProject.project_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <section id="chat" className="scroll-mt-20 lg:scroll-mt-8 min-h-screen py-12 lg:py-16">
      {/* Themed Header */}
      {activeProject && topicTheme && (
        <div
          className={`rounded-2xl p-4 mb-6 flex items-center gap-3`}
          style={{
            background: `linear-gradient(135deg, ${topicTheme.gradientFrom}20, ${topicTheme.gradientTo}10)`,
            borderLeft: `4px solid ${topicTheme.accentColor}`,
          }}
        >
          <topicTheme.icon size={24} style={{ color: topicTheme.accentColor }} />
          <div>
            <h3 className="font-medium text-stone-800 dark:text-stone-200">{activeProject.topic}</h3>
            <p className="text-sm text-stone-500 dark:text-stone-400">Research Chat</p>
          </div>
        </div>
      )}

      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-amber-100 dark:bg-amber-900/30 rounded-lg">
          <MessageSquare
            className="text-amber-600 dark:text-amber-500"
            size={24}
            style={topicTheme ? { color: topicTheme.accentColor } : undefined}
          />
        </div>
        <h2 className="text-2xl font-display font-semibold text-stone-800 dark:text-stone-100">
          Chat
        </h2>
      </div>

      {!activeProject ? (
        <div className="bg-white dark:bg-stone-800/50 rounded-2xl p-12 border border-stone-200 dark:border-stone-700 text-center">
          <MessageSquare size={48} className="mx-auto text-stone-300 dark:text-stone-600 mb-4" />
          <p className="text-stone-500 dark:text-stone-400">
            Create or load a project to start chatting
          </p>
        </div>
      ) : (
        <div className="bg-white dark:bg-stone-800/50 rounded-2xl border border-stone-200 dark:border-stone-700 overflow-hidden">
          {/* Chat Actions */}
          <div className="px-4 py-3 border-b border-stone-200 dark:border-stone-700 flex items-center gap-2">
            <button
              onClick={clearChat}
              className="flex items-center gap-2 px-3 py-1.5 text-sm text-stone-600 dark:text-stone-400 hover:bg-stone-100 dark:hover:bg-stone-700 rounded-lg transition-colors"
            >
              <Trash2 size={16} />
              Clear
            </button>
            <button
              onClick={handleExport}
              className="flex items-center gap-2 px-3 py-1.5 text-sm text-stone-600 dark:text-stone-400 hover:bg-stone-100 dark:hover:bg-stone-700 rounded-lg transition-colors"
            >
              <Download size={16} />
              Export
            </button>
          </div>

          {/* Messages */}
          <div className="h-96 overflow-y-auto p-4 space-y-4">
            {chatHistory.length === 0 ? (
              <div className="text-center py-12">
                <Bot size={48} className="mx-auto text-stone-300 dark:text-stone-600 mb-4" />
                <p className="text-stone-500 dark:text-stone-400">
                  Start a conversation about your research
                </p>
              </div>
            ) : (
              chatHistory.map(message => (
                <div
                  key={message.id}
                  className={`flex gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
                >
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                      message.role === 'user'
                        ? 'bg-amber-100 dark:bg-amber-900/30'
                        : 'bg-stone-100 dark:bg-stone-700'
                    }`}
                  >
                    {message.role === 'user' ? (
                      <User size={16} className="text-amber-600 dark:text-amber-400" />
                    ) : (
                      <Bot
                        size={16}
                        style={topicTheme ? { color: topicTheme.accentColor } : undefined}
                        className="text-stone-600 dark:text-stone-400"
                      />
                    )}
                  </div>
                  <div
                    className={`max-w-[70%] px-4 py-3 rounded-2xl ${
                      message.role === 'user'
                        ? 'bg-amber-500 text-white'
                        : 'bg-stone-100 dark:bg-stone-700 text-stone-800 dark:text-stone-200'
                    }`}
                    style={
                      message.role === 'assistant' && topicTheme
                        ? {
                            backgroundColor: `${topicTheme.accentColor}15`,
                            borderLeft: `2px solid ${topicTheme.accentColor}`,
                          }
                        : undefined
                    }
                  >
                    <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                  </div>
                </div>
              ))
            )}
            {isLoading && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-stone-100 dark:bg-stone-700 flex items-center justify-center">
                  <Bot size={16} className="text-stone-600 dark:text-stone-400" />
                </div>
                <div className="bg-stone-100 dark:bg-stone-700 px-4 py-3 rounded-2xl">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-stone-400 rounded-full animate-bounce" />
                    <div
                      className="w-2 h-2 bg-stone-400 rounded-full animate-bounce"
                      style={{ animationDelay: '0.1s' }}
                    />
                    <div
                      className="w-2 h-2 bg-stone-400 rounded-full animate-bounce"
                      style={{ animationDelay: '0.2s' }}
                    />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="px-4 py-3 border-t border-stone-200 dark:border-stone-700">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about your research..."
                className="flex-1 px-4 py-2.5 rounded-xl border border-stone-200 dark:border-stone-600 bg-stone-50 dark:bg-stone-900 text-stone-800 dark:text-stone-200 placeholder-stone-400 focus:outline-none focus:ring-2 focus:ring-amber-500 dark:focus:ring-amber-400 transition-all"
              />
              <button
                onClick={handleSend}
                disabled={!input.trim() || isLoading}
                className="px-4 py-2.5 bg-amber-500 hover:bg-amber-600 disabled:bg-stone-300 dark:disabled:bg-stone-600 text-white font-medium rounded-xl transition-colors flex items-center gap-2"
              >
                <Send size={18} />
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
