import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, UserRound, Users } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import AddChildModal from '../../features/parent/components/AddChildModal';
import { ROUTES, parentChildSummaryPath } from '../../routes';
import { PARENT_SHELL } from '../../features/parent/parentShell';
import { timeAgo, useLang, useStrings } from '../../i18n'; // i18n
import { Button, Card, EmptyState, Pill } from '../../components/ui';

const ChildRowCard = ({ child, onView, onSettings }) => {
  const lang = useLang();
  const s = useStrings().parent.children;
  return (
    <Card>
      <div className="flex items-start gap-3">
        <div
          className="grid size-12 shrink-0 place-items-center rounded-2xl bg-primary-soft text-primary-strong"
          aria-hidden="true"
        >
          <UserRound className="size-6" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <p dir="auto" className="truncate text-heading text-text">{child.nickname}</p>
            <Pill variant={child.is_active_in_app ? 'success' : 'neutral'}>
              {child.is_active_in_app ? s.inApp : s.away}
            </Pill>
          </div>
          <p className="mt-1 text-label text-text-muted">
            {s.lastActivity(timeAgo(child.last_activity_at, lang) || '—')}
          </p>
        </div>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <Button size="sm" onClick={() => onView(child.id)}>
          {s.view}
        </Button>
        <Button size="sm" variant="ghost" onClick={() => onSettings(child.id)}>
          {s.settings}
        </Button>
      </div>
    </Card>
  );
};

const ParentConversationPage = () => {
  const { user, refreshProfile, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const s = useStrings().parent.children;
  const [addOpen, setAddOpen] = useState(false);

  useEffect(() => {
    refreshProfile();
  }, [refreshProfile]);

  const displayChildren = useMemo(() => {
    if (authLoading) return user?.children ?? [];
    return user?.children ?? [];
  }, [authLoading, user]);

  const closeAdd = useCallback(() => setAddOpen(false), []);
  const openSummary = (id) => navigate(parentChildSummaryPath(id));
  const openSettings = (id) => navigate(`${ROUTES.PARENT_SETTINGS}?child=${id}`);

  return (
    <div className={`flex-1 flex flex-col min-h-0 pt-4 pb-2 ${PARENT_SHELL}`}>
      <header className="flex items-center justify-between gap-3 mb-6 shrink-0 w-full">
        <h1 className="text-title text-text">{s.title}</h1>
        <Button
          size="sm"
          onClick={() => setAddOpen(true)}
          icon={<Plus aria-hidden="true" className="size-4" />}
        >
          {s.add}
        </Button>
      </header>

      <div className="flex-1 overflow-y-auto min-h-0 pb-4 w-full">
        {displayChildren.length === 0 ? (
          <Card padding="lg" className="w-full max-w-3xl lg:max-w-none">
            <EmptyState
              icon={Users}
              title={s.emptyTitle}
              message={s.emptyMessage}
              action={
                <Button
                  size="sm"
                  onClick={() => setAddOpen(true)}
                  icon={<Plus aria-hidden="true" className="size-4" />}
                >
                  {s.add}
                </Button>
              }
            />
          </Card>
        ) : (
          <ul className="space-y-4 w-full max-w-4xl lg:max-w-none">
            {displayChildren.map((child) => (
              <li key={child.id}>
                <ChildRowCard
                  child={child}
                  onView={openSummary}
                  onSettings={openSettings}
                />
              </li>
            ))}
          </ul>
        )}
      </div>

      <AddChildModal
        open={addOpen}
        onClose={closeAdd}
        onCreated={() => refreshProfile()}
      />

    </div>
  );
};

export default ParentConversationPage;
