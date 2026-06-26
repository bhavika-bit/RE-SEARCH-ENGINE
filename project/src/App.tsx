import { ThemeProvider } from './contexts/ThemeContext';
import { ProjectProvider } from './contexts/ProjectContext';
import LeftSidebar from './components/LeftSidebar';
import RightSidebar from './components/RightSidebar';
import CenterContent from './components/CenterContent';

function App() {
  return (
    <ThemeProvider>
      <ProjectProvider>
        <div className="min-h-screen bg-amber-50 dark:bg-stone-900 transition-colors duration-200">
          <LeftSidebar />
          <RightSidebar />
          <main className="lg:pl-72 lg:pr-80 pt-16 lg:pt-0">
            <div className="h-screen lg:h-auto">
              <CenterContent />
            </div>
          </main>
        </div>
      </ProjectProvider>
    </ThemeProvider>
  );
}

export default App;
