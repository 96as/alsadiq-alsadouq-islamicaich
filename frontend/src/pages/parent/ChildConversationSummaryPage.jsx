import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, MessageCircle } from 'lucide-react';
import { fetchParentChildSummary } from '../../services/authService';
import { ROUTES } from '../../routes';
import { PARENT_SHELL } from '../../features/parent/parentShell';
import { clockTime, shortDate, timeAgo, useLang, useStrings } from '../../i18n'; // i18n
import { Button, Card, EmptyState, IconButton, Pill } from '../../components/ui';

const stamp = (iso, lang) => `${shortDate(iso, lang)} ${clockTime(iso, lang)}`;

const ChildConversationSummaryPage = () => {
  const { childId } = useParams();
  const navigate = useNavigate();
  const lang = useLang();
  const strings = useStrings();
  const s = strings.parent.summary;
  const common = strings.common;
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError('');
      try {
        const res = await fetchParentChildSummary(childId);
        if (!cancelled) setData(res);
      } catch (e) {
        if (!cancelled) {
          setError(e.response?.data?.detail || s.loadError);
          setData(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [childId, s.loadError]);

  const displayData = useMemo(() => {
    if (loading) return null;
    if (error) return null;
    if (!data) return null;
    return data;
  }, [loading, error, data]);

  const back = () => navigate(ROUTES.PARENT_HOME);

  return (
    <div className={`flex-1 flex flex-col min-h-0 pt-4 pb-2 ${PARENT_SHELL}`}>
      <header className="flex items-center gap-3 mb-4 shrink-0 w-full">
        <IconButton
          label={s.back}
          variant="ghost"
          onClick={back}
          icon={<ArrowLeft aria-hidden="true" className="size-5 rtl:rotate-180" />}
        />
        <div className="min-w-0 flex-1">
          <h1 dir="auto" className="truncate text-title text-text">
            {displayData?.child?.nickname || data?.child?.nickname || s.title}
          </h1>
          <p dir="ltr" className="truncate text-label text-text-muted text-start">
            {displayData?.child?.username || data?.child?.username
              ? `@${displayData?.child?.username || data?.child?.username}`
              : ' '}
          </p>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto min-h-0 pb-4 w-full">
        {loading && (
          <p className="py-12 text-center text-body text-text-muted" role="status">{s.loading}</p>
        )}
        {!loading && error && !displayData && (
          <Card padding="lg" className="w-full max-w-xl lg:max-w-none">
            <EmptyState
              icon={MessageCircle}
              title={common.somethingWrong}
              message={error}
              action={<Button size="sm" onClick={back}>{s.back2}</Button>}
            />
          </Card>
        )}
        {!loading && displayData && (
          <>
            <Card className="mb-4 w-full max-w-3xl lg:max-w-none">
              <p className="text-label text-text-muted">{s.lastActivity}</p>
              <p className="mt-1 text-body text-text">
                {timeAgo(displayData.last_activity_at, lang) || '—'}
                {displayData.last_activity_at && (
                  <span className="ms-2 text-text-muted">
                    ({stamp(displayData.last_activity_at, lang)})
                  </span>
                )}
              </p>
            </Card>

            <h2 className="mb-3 w-full max-w-3xl px-1 text-heading text-text lg:max-w-none">
              {s.recent}
            </h2>
            {displayData.sessions?.length === 0 ? (
              <Card padding="lg" className="w-full max-w-3xl lg:max-w-none">
                <EmptyState icon={MessageCircle} title={s.none} />
              </Card>
            ) : (
              <ul className="space-y-3 w-full max-w-3xl lg:max-w-none pb-4">
                {displayData.sessions.map((sess) => (
                  <li key={sess.id}>
                    <Card>
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="text-label text-text-muted">
                              {stamp(sess.started_at, lang)}
                            </span>
                            <Pill>{s.status[sess.status] || sess.status}</Pill>
                          </div>
                        </div>
                        <span className="shrink-0 text-label tabular-nums text-text-muted">
                          {s.messages(sess.message_count)}
                        </span>
                      </div>
                    </Card>
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default ChildConversationSummaryPage;
