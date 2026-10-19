import { useEffect, useState } from 'react';
import { AlertTriangle, ChevronDown, ShieldCheck } from 'lucide-react';
import { Button, Card, EmptyState, Pill } from '../../components/ui';
import { useAuth } from '../../context/AuthContext';
import { PARENT_SHELL } from '../../features/parent/parentShell';
import { fetchAlerts, markAlertRead } from '../../services/alertService';
import { timeAgo, useLang, useStrings } from '../../i18n'; // i18n

function formatChildName(name, fallback = 'Child') {
  const cleanName = name?.trim();
  if (!cleanName) return fallback;
  return cleanName
    .split(' ')
    .map((part) => (part ? part[0].toUpperCase() + part.slice(1) : part))
    .join(' ');
}

function normalizeChildName(name) {
  return name?.trim().toLowerCase() || '';
}

// Shared with the Insights page (per-child alert counts).
// eslint-disable-next-line react-refresh/only-export-components
export function groupAlertsByChild(alerts, children, fallbackName) {
  const groupsByKey = new Map();
  const childKeyByName = new Map();

  children.forEach((child) => {
    const childKey = `child-${child.id}`;
    const childName = formatChildName(child.nickname || child.username, fallbackName);
    groupsByKey.set(childKey, {
      key: childKey,
      childName,
      alerts: [],
    });

    const nicknameKey = normalizeChildName(child.nickname);
    if (nicknameKey) childKeyByName.set(nicknameKey, childKey);

    const usernameKey = normalizeChildName(child.username);
    if (usernameKey) childKeyByName.set(usernameKey, childKey);
  });

  alerts.forEach((alert) => {
    const childName = formatChildName(alert.child_nickname, fallbackName);
    const childNameKey = normalizeChildName(alert.child_nickname);
    const childKey = childKeyByName.get(childNameKey) || `alert-${childNameKey || 'unknown-child'}`;
    const existing = groupsByKey.get(childKey);
    if (existing) {
      existing.alerts.push(alert);
      return;
    }
    groupsByKey.set(childKey, {
      key: childKey,
      childName,
      alerts: [alert],
    });
  });
  return Array.from(groupsByKey.values());
}

function toPanelId(key) {
  return `alerts-panel-${key.replace(/[^a-zA-Z0-9_-]/g, '-')}`;
}

const ParentAlertsPage = () => {
  const { user, loading: authLoading, refreshProfile } = useAuth();
  const lang = useLang();
  const strings = useStrings();
  const s = strings.parent.alerts;
  const common = strings.common;
  const [alerts, setAlerts] = useState([]);
  const [collapsedGroups, setCollapsedGroups] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionError, setActionError] = useState('');
  const [retrySeed, setRetrySeed] = useState(0);

  useEffect(() => {
    refreshProfile();
  }, [refreshProfile]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError('');
      try {
        const data = await fetchAlerts();
        if (!cancelled) setAlerts(data);
      } catch (err) {
        console.error('Failed to load alerts:', err);
        if (!cancelled) {
          setError(s.loadError);
          setAlerts([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [retrySeed, s.loadError]);

  const handleMarkRead = async (id) => {
    setActionError('');
    try {
      await markAlertRead(id);
      setAlerts((prev) => prev.map((a) => (a.id === id ? { ...a, is_read: true } : a)));
    } catch (err) {
      console.error('Failed to mark alert read:', err);
      setActionError(s.markError);
    }
  };

  const handleToggleGroup = (key) => {
    setCollapsedGroups((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  if (loading || authLoading) {
    return (
      <div className={`flex-1 flex flex-col min-h-0 pt-4 pb-2 ${PARENT_SHELL}`}>
        <p className="mt-10 text-center text-body text-text-muted" role="status">{s.loading}</p>
      </div>
    );
  }

  const displayAlerts = alerts;
  const displayChildren = user?.children ?? [];
  const alertGroups = groupAlertsByChild(displayAlerts, displayChildren, s.childDefault);

  return (
    <div className={`flex-1 flex flex-col min-h-0 pt-4 pb-2 ${PARENT_SHELL}`}>
      <header className="shrink-0 mb-6 w-full">
        <h1 className="text-title text-text">{s.title}</h1>
        <p className="mt-2 max-w-3xl text-body text-text-muted">
          {s.intro}
        </p>
      </header>

      <div className="flex-1 overflow-y-auto min-h-0 pb-6 w-full max-w-4xl lg:max-w-none">
        {error ? (
          <Card padding="lg">
            <EmptyState
              icon={AlertTriangle}
              title={common.somethingWrong}
              message={error}
              action={
                <Button size="sm" onClick={() => setRetrySeed((prev) => prev + 1)}>
                  {common.retry}
                </Button>
              }
            />
          </Card>
        ) : alertGroups.length === 0 ? (
          <Card padding="lg">
            <EmptyState
              icon={ShieldCheck}
              title={s.allClear}
              message={s.allClearMessage}
            />
          </Card>
        ) : (
          <div className="space-y-4">
            {alertGroups.map((group) => {
              const isCollapsed = Boolean(collapsedGroups[group.key]);
              const panelId = toPanelId(group.key);
              const unreadCount = group.alerts.filter((a) => !a.is_read).length;
              return (
                <Card as="section" key={group.key} padding="md" className="overflow-hidden p-0!">
                  <button
                    type="button"
                    onClick={() => handleToggleGroup(group.key)}
                    className="flex min-h-target w-full cursor-pointer items-center justify-between gap-3 bg-danger-soft px-4 py-3 text-start focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-primary-strong"
                    aria-expanded={!isCollapsed}
                    aria-controls={panelId}
                  >
                    <span className="flex min-w-0 items-center gap-3">
                      <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-surface text-danger-strong">
                        <AlertTriangle aria-hidden="true" className="size-5" />
                      </span>
                      <span className="min-w-0">
                        <span className="block truncate text-heading text-danger-strong">
                          {s.groupTitle(group.childName)}
                        </span>
                        <span className="block text-label text-text">
                          {unreadCount > 0 ? s.unread(unreadCount) : s.critical}
                        </span>
                      </span>
                    </span>
                    <ChevronDown
                      className={`size-5 shrink-0 text-text-muted motion-safe:transition-transform ${isCollapsed ? '-rotate-90' : 'rotate-0'}`}
                      aria-hidden="true"
                    />
                  </button>
                  {!isCollapsed ? (
                    <div id={panelId}>
                      {group.alerts.length > 0 ? (
                        <ul className="divide-y divide-border">
                          {group.alerts.map((a) => (
                            <li key={a.id} className="px-4 py-4">
                              <div className="flex flex-wrap items-center justify-between gap-2">
                                <div className="flex flex-wrap items-center gap-2">
                                  <Pill
                                    variant="danger"
                                    icon={<AlertTriangle aria-hidden="true" className="size-4" />}
                                  >
                                    <bdi dir="auto">{a.kind || a.category || s.safetyConcern}</bdi>
                                  </Pill>
                                  <Pill variant={a.is_read ? 'neutral' : 'warning'}>
                                    {a.is_read ? s.read : s.unreadPill}
                                  </Pill>
                                </div>
                                <span className="text-label tabular-nums text-text-muted">
                                  {timeAgo(a.created_at, lang)}
                                </span>
                              </div>
                              <p dir="auto" className="mt-3 text-body text-text">{a.description}</p>
                              {!a.is_read && (
                                <Button
                                  size="sm"
                                  variant="secondary"
                                  className="mt-3"
                                  onClick={() => handleMarkRead(a.id)}
                                >
                                  {s.markRead}
                                </Button>
                              )}
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <div className="px-4 py-5">
                          <p className="text-heading text-text">{s.noneNow}</p>
                          <p className="mt-1 text-label text-text-muted">
                            {s.noneFor(group.childName)}
                          </p>
                        </div>
                      )}
                      {actionError ? (
                        <p className="border-t border-border px-4 py-3 text-label text-danger-strong" role="alert">
                          {actionError}
                        </p>
                      ) : null}
                    </div>
                  ) : null}
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default ParentAlertsPage;
