import { Component, Suspense, lazy, useEffect } from 'react';
import { Route, Routes, useLocation } from 'react-router-dom';
import { Shell } from './components/Shell';
import { InstallPrompt } from './components/InstallPrompt';
import { loadQuestions } from './data/loader';

// Lazy-load route components to keep initial bundle small.
const Home = lazy(() => import('./routes/Home').then((m) => ({ default: m.Home })));
const Subjects = lazy(() =>
  import('./routes/Subjects').then((m) => ({ default: m.Subjects })),
);
const TestRunner = lazy(() =>
  import('./routes/TestRunner').then((m) => ({ default: m.TestRunner })),
);
const Results = lazy(() =>
  import('./routes/Results').then((m) => ({ default: m.Results })),
);
const Dashboard = lazy(() =>
  import('./routes/Dashboard').then((m) => ({ default: m.Dashboard })),
);

export function App() {
  const location = useLocation();

  // Kick off data load as soon as the app boots.
  useEffect(() => {
    void loadQuestions();
  }, []);

  // Scroll to top on navigation for predictable UX.
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [location.pathname]);

  return (
    <Shell>
      <ErrorBoundary>
        <Suspense fallback={<RouteLoading />}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/exam/:examId" element={<Subjects />} />
            <Route
              path="/practice/:examId/:subjectId"
              element={<TestRunner />}
            />
            <Route path="/results/:attemptId" element={<Results />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Suspense>
      </ErrorBoundary>
      <InstallPrompt />
    </Shell>
  );
}

function RouteLoading() {
  return (
    <div className="card p-6 text-center text-neutral-500 dark:text-neutral-400 animate-pulse">
      Loading…
    </div>
  );
}

function NotFound() {
  return (
    <div className="card p-6 text-center">
      <h1 className="text-xl font-bold mb-2">Page not found</h1>
      <p className="text-neutral-600 dark:text-neutral-400">
        The page you're looking for doesn't exist.
      </p>
      <a href="/" className="btn-primary mt-4 inline-flex">
        Back home
      </a>
    </div>
  );
}

interface EBProps {
  children: React.ReactNode;
}
interface EBState {
  error: Error | null;
}

class ErrorBoundary extends Component<EBProps, EBState> {
  state: EBState = { error: null };
  static getDerivedStateFromError(error: Error): EBState {
    return { error };
  }
  componentDidCatch(error: Error) {
    // eslint-disable-next-line no-console
    console.error('App error:', error);
  }
  render() {
    if (this.state.error) {
      return (
        <div className="card p-6 text-center">
          <h1 className="text-xl font-bold mb-2">Something went wrong</h1>
          <p className="text-neutral-600 dark:text-neutral-400 mb-4">
            {this.state.error.message || 'Unknown error'}
          </p>
          <button
            type="button"
            className="btn-primary"
            onClick={() => {
              this.setState({ error: null });
              window.location.reload();
            }}
          >
            Reload
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
