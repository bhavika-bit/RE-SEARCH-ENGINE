import { useState, useEffect, useRef } from 'react';
import { FolderOpen, MessageSquare, Wrench, HelpCircle, Layers, Menu, X, Sun, Moon } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import { useProject } from '../contexts/ProjectContext';
import { getTopicTheme } from '../utils/topicTheme';

const navItems = [
  { id: 'project', label: 'Project', icon: FolderOpen },
  { id: 'chat', label: 'Chat', icon: MessageSquare },
  { id: 'tools', label: 'Tools', icon: Wrench },
  { id: 'quiz', label: 'Quiz', icon: HelpCircle },
  { id: 'flashcards', label: 'Flashcards', icon: Layers },
];

export default function Sidebar() {
  const { theme, toggleTheme } = useTheme();
  const { activeProject } = useProject();
  const [activeSection, setActiveSection] = useState('project');
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const observerRef = useRef<IntersectionObserver | null>(null);

  const topicTheme = activeProject ? getTopicTheme(activeProject.topic) : null;

  useEffect(() => {
    const sections = navItems.map(item => document.getElementById(item.id));

    observerRef.current = new IntersectionObserver(
      entries => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            setActiveSection(entry.target.id);
          }
        });
      },
      { rootMargin: '-20% 0px -70% 0px' }
    );

    sections.forEach(section => {
      if (section) observerRef.current?.observe(section);
    });

    return () => observerRef.current?.disconnect();
  }, []);

  const scrollToSection = (id: string) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
      setIsMobileOpen(false);
    }
  };

  const NavContent = () => (
    <>
      <div className="mb-8">
        <h1 className="text-xl font-display font-semibold text-amber-600 dark:text-amber-500">
          ResearchEngine
        </h1>
        <p className="text-xs text-stone-500 dark:text-stone-400 mt-1">RAG Research Mentor</p>
      </div>

      <nav className="flex-1">
        <ul className="space-y-1">
          {navItems.map(item => {
            const isActive = activeSection === item.id;
            const Icon = item.id === 'chat' && topicTheme ? topicTheme.icon : item.icon;
            const iconColor = item.id === 'chat' && topicTheme ? topicTheme.accentColor : undefined;

            return (
              <li key={item.id}>
                <button
                  onClick={() => scrollToSection(item.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 ${
                    isActive
                      ? 'bg-amber-100 dark:bg-stone-800 text-amber-700 dark:text-amber-400 font-medium'
                      : 'text-stone-600 dark:text-stone-400 hover:bg-stone-100 dark:hover:bg-stone-800'
                  }`}
                >
                  <Icon
                    size={20}
                    style={iconColor ? { color: iconColor } : undefined}
                    className={iconColor ? '' : 'text-amber-500 dark:text-amber-400'}
                  />
                  <span className="text-sm">{item.label}</span>
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="pt-4 border-t border-stone-200 dark:border-stone-700">
        <button
          onClick={toggleTheme}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-stone-600 dark:text-stone-400 hover:bg-stone-100 dark:hover:bg-stone-800 transition-colors"
        >
          {theme === 'light' ? (
            <>
              <Moon size={20} className="text-amber-500" />
              <span className="text-sm">Dark Mode</span>
            </>
          ) : (
            <>
              <Sun size={20} className="text-amber-400" />
              <span className="text-sm">Light Mode</span>
            </>
          )}
        </button>
      </div>
    </>
  );

  return (
    <>
      {/* Mobile Header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-50 bg-amber-50/95 dark:bg-stone-900/95 backdrop-blur-sm border-b border-stone-200 dark:border-stone-700 px-4 py-3 flex items-center justify-between">
        <h1 className="text-lg font-display font-semibold text-amber-600 dark:text-amber-500">
          ResearchEngine
        </h1>
        <div className="flex items-center gap-2">
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg text-stone-600 dark:text-stone-400 hover:bg-stone-100 dark:hover:bg-stone-800 transition-colors"
          >
            {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
          </button>
          <button
            onClick={() => setIsMobileOpen(!isMobileOpen)}
            className="p-2 rounded-lg text-stone-600 dark:text-stone-400 hover:bg-stone-100 dark:hover:bg-stone-800 transition-colors"
          >
            {isMobileOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {isMobileOpen && (
        <div className="lg:hidden fixed inset-0 z-40 pt-16">
          <div
            className="absolute inset-0 bg-black/20 dark:bg-black/40"
            onClick={() => setIsMobileOpen(false)}
          />
          <div className="absolute top-16 left-0 bottom-0 w-64 bg-amber-50 dark:bg-stone-900 p-4 flex flex-col border-r border-stone-200 dark:border-stone-700">
            <NavContent />
          </div>
        </div>
      )}

      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex fixed left-0 top-0 bottom-0 w-64 bg-amber-50 dark:bg-stone-900 border-r border-stone-200 dark:border-stone-700 p-4 flex-col z-30">
        <NavContent />
      </aside>
    </>
  );
}
