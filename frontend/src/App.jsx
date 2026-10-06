import { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ThemePreferenceProvider } from './context/ThemePreferenceProvider';
import { ROUTES } from './routes';
import ErrorBoundary from './components/ErrorBoundary';
import ProtectedRoute from './guards/ProtectedRoute';
import RoleGuard from './guards/RoleGuard';
import GuestRoute from './guards/GuestRoute';
import Login from './pages/Login';
import Register from './pages/Register';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import NotFound from './pages/NotFound';
import Privacy from './pages/Privacy'; // cards-spec (05)
import DemoLanding from './pages/DemoLanding';
import { DEMO_MODE } from './services/demoService';
import { ROUTER_BASENAME } from './utils/assetUrl';
import ChildApp from './pages/ChildApp';
import ChildQuestProgressLayout from './pages/child/ChildQuestProgressLayout';
import ParentApp from './pages/ParentApp';

import ChildConversationPage from './pages/child/ConversationPage';
import ChildQuestsPage from './pages/child/QuestsPage';
import ChildBadgesPage from './pages/child/BadgesPage';
import ChildSettingsPage from './pages/child/SettingsPage';

import ParentConversationPage from './pages/parent/ConversationPage';
import ParentChildSummaryPage from './pages/parent/ChildConversationSummaryPage';
import ParentInsightsPage from './pages/parent/InsightsPage';
import ParentAlertsPage from './pages/parent/AlertsPage';
import ParentSettingsPage from './pages/parent/SettingsPage';

// DEV-only UI preview; the constant condition lets Vite drop it from production builds.
const UiPreview = import.meta.env.DEV ? lazy(() => import('./pages/dev/UiPreview')) : null;
// Dev-only preview of the forest scene. The DEV and VITE_SHOWCASE checks are replaced
// at build time, so in a normal production build the page and its code are dropped.
// The showcase build (VITE_SHOWCASE=1) keeps them and adds the index page.
const ForestPreviewPage = (import.meta.env.DEV || import.meta.env.VITE_SHOWCASE === '1')
  ? lazy(() => import('./features/child/components/forest/ForestPreviewPage'))
  : null;
const ShowcaseIndex = import.meta.env.VITE_SHOWCASE === '1'
  ? lazy(() => import('./pages/ShowcaseIndex'))
  : null;
const MeadowShowcase = import.meta.env.VITE_SHOWCASE === '1'
  ? lazy(() => import('./pages/MeadowShowcase'))
  : null;

// Dev-only preview of the painted-meadow mode (the default voice scene).
const MeadowPreviewPage = import.meta.env.DEV
  ? lazy(() => import('./features/child/components/ambient/MeadowPreviewPage'))
  : null;

// Dev-only lip-sync lab: plays the audition clips and shows the viseme weights live.
const LipsyncDevPage = import.meta.env.DEV
  ? lazy(() => import('./features/child/components/avatar/lipsync/dev/LipsyncDevPage'))
  : null;

function App() {
  return (
    <AuthProvider>
      <ThemePreferenceProvider>
        <div className="flex min-h-0 flex-1 flex-col">
          <Router basename={ROUTER_BASENAME}>
            <ErrorBoundary>
              {ShowcaseIndex ? (
                // Showcase build: only the preview pages are mounted. No login and no app
                // routes, so nothing here can reach a backend.
                <Routes>
                  <Route
                    path="/"
                    element={(
                      <Suspense fallback={null}>
                        <ShowcaseIndex />
                      </Suspense>
                    )}
                  />
                  <Route
                    path="/dev/forest"
                    element={(
                      <Suspense fallback={null}>
                        <ForestPreviewPage />
                      </Suspense>
                    )}
                  />
                  <Route
                    path="/meadow"
                    element={(
                      <Suspense fallback={null}>
                        <MeadowShowcase />
                      </Suspense>
                    )}
                  />
                  <Route path="/landing" element={<DemoLanding />} />
                  <Route path={ROUTES.PRIVACY} element={<Privacy />} /> {/* cards-spec (05): public */}
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              ) : (
              <Routes>
                {ForestPreviewPage ? (
                  <Route
                    path="/dev/forest"
                    element={(
                      <Suspense fallback={null}>
                        <ForestPreviewPage />
                      </Suspense>
                    )}
                  />
                ) : null}
                {MeadowPreviewPage ? (
                  <Route
                    path="/dev/meadow"
                    element={(
                      <Suspense fallback={null}>
                        <MeadowPreviewPage />
                      </Suspense>
                    )}
                  />
                ) : null}
                {LipsyncDevPage ? (
                  <Route
                    path="/dev/lipsync"
                    element={(
                      <Suspense fallback={null}>
                        <LipsyncDevPage />
                      </Suspense>
                    )}
                  />
                ) : null}

                {/* Always-accessible route — works whether logged in or not */}
                <Route path={ROUTES.RESET_PASSWORD} element={<ResetPassword />} />
                {/* cards-spec (05): the privacy policy, outside every guard (a signed-in parent must not be bounced from it) */}
                <Route path={ROUTES.PRIVACY} element={<Privacy />} />

                {/* Public routes — redirects to home if already logged in */}
                <Route element={<GuestRoute />}>
                  <Route path={ROUTES.LOGIN} element={<Login />} />
                  <Route path={ROUTES.REGISTER} element={<Register />} />
                  <Route path={ROUTES.FORGOT_PASSWORD} element={<ForgotPassword />} />
                </Route>

                {/* Protected routes — must be logged in */}
                <Route element={<ProtectedRoute />}>
                  <Route element={<RoleGuard allowedRole="child" />}>
                    <Route path={ROUTES.CHILD_HOME} element={<ChildApp />}>
                      <Route index element={<ChildConversationPage />} />
                      <Route element={<ChildQuestProgressLayout />}>
                        <Route path="quests" element={<ChildQuestsPage />} />
                        <Route path="badges" element={<ChildBadgesPage />} />
                      </Route>
                      <Route path="settings" element={<ChildSettingsPage />} />
                    </Route>
                  </Route>

                  <Route element={<RoleGuard allowedRole="parent" />}>
                    <Route path={ROUTES.PARENT_HOME} element={<ParentApp />}>
                      <Route index element={<ParentConversationPage />} />
                      <Route path="children/:childId/summary" element={<ParentChildSummaryPage />} />
                      <Route path="insights" element={<ParentInsightsPage />} />
                      <Route path="quests" element={<Navigate to="/parent/insights" replace />} />
                      <Route path="alerts" element={<ParentAlertsPage />} />
                      <Route path="badges" element={<Navigate to="/parent/alerts" replace />} />
                      <Route path="settings" element={<ParentSettingsPage />} />
                    </Route>
                  </Route>
                </Route>

                {import.meta.env.DEV && (
                  <Route
                    path="/dev/ui"
                    element={
                      <Suspense fallback={null}>
                        <UiPreview />
                      </Suspense>
                    }
                  />
                )}

                {/* One-click demo landing only when the build sets VITE_DEMO_MODE=1. */}
                <Route
                  path="/"
                  element={DEMO_MODE ? <DemoLanding /> : <Navigate to={ROUTES.LOGIN} />}
                />
                <Route path="*" element={<NotFound />} />
              </Routes>
              )}
            </ErrorBoundary>
          </Router>
        </div>
      </ThemePreferenceProvider>
    </AuthProvider>
  );
}

export default App;
