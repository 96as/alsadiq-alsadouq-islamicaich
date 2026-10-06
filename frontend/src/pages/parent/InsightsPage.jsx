import { useCallback, useEffect, useId, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Award,
  CalendarCheck,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Clock,
  Flame,
  Lightbulb,
  Sparkles,
  TrendingUp,
  Users,
  XCircle,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { AiLabel, QuestionsToDiscuss, SourcesDiscussed, Title as SectionTitle, ValuesThisWeek } from '../../features/parent/components/InsightsTrust'; // task 04
import { badgeImageUrlForLabel } from '../../features/parent/data/badgeImages';
import { PARENT_SHELL } from '../../features/parent/parentShell';
import { ROUTES } from '../../routes';
import { fetchAlerts } from '../../services/alertService';
import { fetchChildQuestsAsParent, verifyQuest } from '../../services/gamificationService';
import { fetchChildDashboard, fetchChildInsights } from '../../services/reportingService';
import { Button, Card, EmptyState, Pill, ProgressBar } from '../../components/ui';
import { cx, FOCUS_RING } from '../../components/ui/cx';
import { localName, num, shortDate, useLang, useStrings } from '../../i18n'; // i18n
import { groupAlertsByChild } from './AlertsPage';
import { normalizeReference } from '../../features/child/sources/useSourceCards';

function BadgeGrid({ badges }) {
  const strings = useStrings();
  const s = strings.parent.insights;
  const nameOf = (b) => strings.badgeCatalog[b]?.[0] || b;
  return (
    <ul className="flex flex-wrap items-start gap-x-6 gap-y-4">
      {badges.map((b) => {
        const src = badgeImageUrlForLabel(b);
        if (src) {
          return (
            <li
              key={b}
              className="flex w-24 shrink-0 flex-col items-center text-center sm:w-28"
            >
              <div className="relative flex size-14 items-center justify-center">
                <img src={src} alt="" className="size-full max-h-full max-w-full object-contain" />
              </div>
              <p dir="auto" className="mt-2 text-label text-text">{nameOf(b)}</p>
            </li>
          );
        }
        return (
          <li
            key={b}
            className="flex min-h-22 w-24 flex-col items-center justify-center rounded-2xl border border-dashed border-border bg-surface-alt px-2 py-3 sm:w-28"
          >
            <span dir="auto" className="text-center text-label text-text">{nameOf(b)}</span>
            <span className="mt-1 text-caption text-text-muted">{s.comingSoon}</span>
          </li>
        );
      })}
    </ul>
  );
}

/** One collapsible block of a child's week: a full-width 44px+ row with a rotating chevron and a count pill. */
function Section({ title, count, defaultOpen = false, children }) {
  const lang = useLang();
  return (
    <details open={defaultOpen} className="group border-t border-border">
      <summary
        className={cx(
          'flex min-h-11 cursor-pointer list-none items-center gap-2 py-2 [&::-webkit-details-marker]:hidden',
          FOCUS_RING,
        )}
      >
        <ChevronDown
          aria-hidden="true"
          className="size-5 shrink-0 text-text-muted motion-safe:transition-transform motion-safe:duration-200 group-open:rotate-180"
        />
        <span className="min-w-0 flex-1 text-heading text-text">{title}</span>
        {count != null ? <Pill>{num(count, lang)}</Pill> : null}
      </summary>
      <div className="pb-4 ps-7">{children}</div>
    </details>
  );
}

function StatChip({ icon, label, children }) {
  const Icon = icon;
  return (
    <Pill>
      <Icon className="size-4 shrink-0" aria-hidden="true" />
      <span className="sr-only">{label}: </span>
      {children}
    </Pill>
  );
}

function QuestVerificationPanel({ quests, onVerify, busyIds }) {
  const s = useStrings().parent.insights;
  if (!quests.length) return <p className="text-body text-text-muted">{s.noQuestsWaiting}</p>;
  return (
    <div>
      <ul className="space-y-3">
        {quests.map((q) => {
          const busy = busyIds.includes(q.id);
          return (
            <li key={q.id} className="rounded-2xl border border-border bg-info-soft px-4 py-4">
              <div className="flex flex-wrap items-center gap-2">
                <p dir="auto" className="text-heading text-text">{q.title}</p>
                <Pill variant="info">{s.questPoints(q.reward_points)}</Pill>
              </div>
              <p dir="auto" className="mt-1 text-body text-text-muted">{q.description}</p>
              {q.proof_note ? (
                <p dir="auto" className="mt-2 rounded-xl bg-surface px-3 py-2 text-body italic text-text">
                  &ldquo;{q.proof_note}&rdquo;
                </p>
              ) : null}
              <div className="mt-3 flex flex-wrap gap-2">
                <Button
                  size="sm"
                  disabled={busy}
                  onClick={() => onVerify(q.id, 'approve')}
                  icon={<CheckCircle2 aria-hidden="true" className="size-4" />}
                >
                  {busy ? s.saving : s.confirmDone}
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  disabled={busy}
                  onClick={() => onVerify(q.id, 'reject')}
                  icon={<XCircle aria-hidden="true" className="size-4" />}
                >
                  {s.notYet}
                </Button>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

const ChildInsightsSection = ({ nickname, childId, defaultOpen, alertCount }) => {
  const lang = useLang();
  const strings = useStrings();
  const s = strings.parent.insights;
  const common = strings.common;
  const [data, setData] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [pendingQuests, setPendingQuests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [retrySeed, setRetrySeed] = useState(0);
  const [busyIds, setBusyIds] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [open, setOpen] = useState(defaultOpen);
  const panelId = useId();

  const loadPendingQuests = useCallback(async () => {
    try {
      const quests = await fetchChildQuestsAsParent(childId, 'pending_verification');
      setPendingQuests(quests);
    } catch {
      setPendingQuests([]);
    }
  }, [childId]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError('');
      try {
        const [insightsRes, dashboardRes, questsRes] = await Promise.all([
          fetchChildInsights(childId),
          fetchChildDashboard(childId).catch(() => null),
          fetchChildQuestsAsParent(childId, 'pending_verification').catch(() => []),
        ]);
        if (cancelled) return;
        setData(insightsRes);
        setDashboard(dashboardRes);
        setPendingQuests(questsRes);
      } catch (err) {
        console.error(`Failed to load insights for child ${childId}:`, err);
        if (!cancelled) {
          setError(s.loadError);
          setData(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [childId, retrySeed, s.loadError]);

  const handleVerify = useCallback(async (progressId, action) => {
    setBusyIds((prev) => [...prev, progressId]);
    try {
      await verifyQuest(progressId, action);
      await loadPendingQuests();
      // Refresh stats so the completed quest reflects immediately.
      fetchChildDashboard(childId).then(setDashboard).catch(() => {});
    } catch (err) {
      console.error('Quest verification failed:', err);
    } finally {
      setBusyIds((prev) => prev.filter((id) => id !== progressId));
    }
  }, [childId, loadPendingQuests]);

  if (loading) {
    return (
      <Card as="section" padding="lg">
        <p className="text-body text-text-muted" role="status">{s.loading(nickname)}</p>
      </Card>
    );
  }

  if (error && !data) {
    return (
      <Card as="section" padding="lg">
        <EmptyState
          icon={Sparkles}
          title={common.somethingWrong}
          message={error}
          action={
            <Button size="sm" onClick={() => setRetrySeed((prev) => prev + 1)}>
              {common.retry}
            </Button>
          }
        />
      </Card>
    );
  }

  const summary = data?.summary || '';
  const badges = data?.badges ?? [];
  const suggestedTopics = data?.suggested_topics ?? [];
  const history = (data?.history ?? []).slice(1); // first item is the current summary
  const level = dashboard?.level;
  const streak = dashboard?.streak;
  const sessions = dashboard?.sessions;
  const questStats = dashboard?.quests;

  const meta = [
    level ? s.levelShort(level.level_number) : null,
    sessions ? s.weekMeta(sessions.this_week) : null,
  ].filter(Boolean).join(' · ');
  const waiting = pendingQuests.length;
  const labels = data?.labels || {};
  const pickLabel = (label) => label?.[lang] || label?.en || '';
  const valuesTitle = pickLabel(labels.values_this_week);
  const questionsTitle = pickLabel(labels.questions_title);
  const values = data?.values_this_week;
  const questions = data?.questions_to_discuss;
  const drawableSources = (data?.sources || []).filter((raw) => normalizeReference(raw)).length;

  return (
    <Card as="section" padding="md">
      {/* The child's name stays a heading (disclosure pattern: the button lives inside the h2). */}
      <h2 className="m-0">
        <button
          type="button"
          aria-expanded={open}
          aria-controls={panelId}
          onClick={() => setOpen((v) => !v)}
          className={cx('flex min-h-11 w-full cursor-pointer items-start gap-3 rounded-2xl text-start', FOCUS_RING)}
        >
          <span className="grid size-10 shrink-0 place-items-center rounded-2xl bg-primary-soft text-primary-strong">
            <Sparkles className="size-5" aria-hidden="true" />
          </span>
          <span className="min-w-0 flex-1">
            <span dir="auto" className="block truncate text-title text-text">{nickname}</span>
            {meta ? <span className="block text-label text-text-muted">{meta}</span> : null}
            <span className="mt-1 flex flex-wrap gap-2 empty:hidden">
              {waiting > 0 ? <Pill variant="info">{s.waiting(waiting)}</Pill> : null}
              {alertCount > 0 ? <Pill variant="danger">{s.alertsChip(alertCount)}</Pill> : null}
              {!open && streak?.current > 0 ? <Pill variant="warning" icon={<Flame className="size-4" aria-hidden="true" />}>{s.streakChip(streak.current)}</Pill> : null}
            </span>
          </span>
          <ChevronDown
            aria-hidden="true"
            className={cx('mt-2.5 size-5 shrink-0 text-text-muted motion-safe:transition-transform motion-safe:duration-200', open && 'rotate-180')}
          />
        </button>
      </h2>

      {open ? (
        <div id={panelId} className="mt-4">
          {dashboard ? (
            <div className="flex flex-wrap gap-2">
              <StatChip icon={TrendingUp} label={s.statLevel}>
                {level ? s.levelValue(level.level_number, localName(lang === 'ar' ? strings.levels : null, level.level_name)) : '—'}
              </StatChip>
              <StatChip icon={Flame} label={s.statStreak}>{streak ? s.streakValue(streak.current) : '—'}</StatChip>
              <StatChip icon={Clock} label={s.statWeek}>
                {sessions ? s.weekChip(sessions.this_week, sessions.talk_minutes_this_week) : '—'}
              </StatChip>
              <StatChip icon={Award} label={s.statQuests}>{questStats ? s.questsDoneChip(questStats.completed) : '—'}</StatChip>
            </div>
          ) : null}

          {level ? (
            <div className="mt-3">
              <p className="mb-1 text-label text-text-muted">{s.levelHint(level.total_points, level.progress_pct)}</p>
              <ProgressBar
                progress={Number(level.progress_pct) || 0}
                label={s.progressLabel(nickname)}
              />
            </div>
          ) : null}

          <div className="mt-4 rounded-2xl bg-surface-alt px-4 py-3">
            {summary ? <AiLabel label={data?.summary_label} /> : null}
            <p dir="auto" className="line-clamp-2 text-body text-text">
              {summary || s.noSummary}
            </p>
          </div>

          <div className="mt-4">
            <Section title={s.questsWaiting} count={waiting} defaultOpen={waiting > 0}>
              <QuestVerificationPanel
                quests={pendingQuests}
                onVerify={handleVerify}
                busyIds={busyIds}
              />
            </Section>

            <Section title={s.summary}>
              {summary ? <AiLabel label={data?.summary_label} /> : null}
              <p dir="auto" className="text-body text-text">
                {summary || s.noSummary}
              </p>
              {history.length > 0 ? (
                <div className="mt-4">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setShowHistory((v) => !v)}
                    aria-expanded={showHistory}
                    icon={<CalendarCheck aria-hidden="true" className="size-4" />}
                  >
                    {showHistory ? s.hideHistory : s.showHistory(history.length)}
                  </Button>
                  {showHistory ? (
                    <div className="mt-3">
                      <AiLabel label={data?.summary_label} />
                      <ul className="space-y-3">
                        {history.map((h) => (
                          <li key={h.week_start} className="rounded-2xl bg-surface-alt px-4 py-3">
                            <p className="text-label text-text-muted">{s.weekOf(shortDate(h.week_start, lang))}</p>
                            <p dir="auto" className="mt-1 text-body text-text">{h.summary}</p>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                </div>
              ) : null}
            </Section>

            {/* Same rule as SourcesDiscussed: the list is empty (it then says so), or at least one source can be drawn. */}
            {Array.isArray(data?.sources) && (data.sources.length === 0 || drawableSources > 0) ? (
              <Section title={s.sourcesTitle} count={drawableSources}>
                <SourcesDiscussed data={data} bare />
              </Section>
            ) : null}

            {questionsTitle && Array.isArray(questions) && questions.length > 0 ? (
              <Section title={questionsTitle} count={questions.length}>
                <QuestionsToDiscuss items={questions} title={labels.questions_title} bare />
              </Section>
            ) : null}

            {valuesTitle && Array.isArray(values) && values.length > 0 ? (
              <Section title={valuesTitle} count={values.length}>
                <ValuesThisWeek values={values} title={labels.values_this_week} bare />
              </Section>
            ) : null}

            {/* Only the count: alert text stays on the Alerts page. */}
            <Link
              to={ROUTES.PARENT_ALERTS}
              className={cx('flex min-h-11 items-center gap-2 border-t border-border py-2', FOCUS_RING)}
            >
              <span className="min-w-0 flex-1 text-heading text-text">{s.alertsTitle}</span>
              {alertCount != null ? (
                <Pill variant={alertCount > 0 ? 'danger' : 'neutral'}>
                  {alertCount > 0 ? s.alertsChip(alertCount) : s.alertsNone}
                </Pill>
              ) : null}
              <span className="text-label text-primary-strong">{s.alertsView}</span>
              <ChevronRight aria-hidden="true" className="size-5 shrink-0 text-primary-strong rtl:rotate-180" />
            </Link>

            <Section title={s.badgesAndTopics}>
              <SectionTitle>{s.currentBadges}</SectionTitle>
              {badges.length > 0 ? <BadgeGrid badges={badges} /> : <p className="text-body text-text-muted">{s.noBadges}</p>}

              <div className="mt-6">
                <SectionTitle>{s.topicsTitle}</SectionTitle>
                {suggestedTopics.length > 0 ? (
                  <>
                    <AiLabel label={data?.labels?.suggested_topics} />
                    <ul className="max-w-3xl space-y-2 lg:max-w-none">
                      {suggestedTopics.map((topic, idx) => (
                        <li
                          key={idx}
                          className="flex items-start gap-3 rounded-2xl bg-accent-soft px-4 py-3"
                        >
                          <Lightbulb className="mt-0.5 size-5 shrink-0 text-text" aria-hidden="true" />
                          <span dir="auto" className="text-body text-text">{topic}</span>
                        </li>
                      ))}
                    </ul>
                  </>
                ) : (
                  <p className="text-body text-text-muted">
                    {s.noTopics}
                  </p>
                )}
              </div>
            </Section>
          </div>
        </div>
      ) : null}
    </Card>
  );
};

const ParentInsightsPage = () => {
  const { user, loading: authLoading } = useAuth();
  const s = useStrings().parent.insights;
  const common = useStrings().common;
  const displayChildren = useMemo(() => {
    if (authLoading) return user?.children ?? [];
    return user?.children ?? [];
  }, [authLoading, user]);

  // One alerts fetch for the page; a failure just leaves the per-child alert chips out.
  const [alerts, setAlerts] = useState(null);
  useEffect(() => {
    let cancelled = false;
    fetchAlerts()
      .then((data) => { if (!cancelled) setAlerts(Array.isArray(data) ? data : null); })
      .catch(() => { if (!cancelled) setAlerts(null); });
    return () => { cancelled = true; };
  }, []);
  const unreadByChild = useMemo(() => {
    if (!alerts) return null;
    return new Map(
      groupAlertsByChild(alerts, displayChildren, '').map((g) => [g.key, g.alerts.filter((a) => !a.is_read).length]),
    );
  }, [alerts, displayChildren]);

  return (
    <div className={`flex-1 flex flex-col min-h-0 pt-4 pb-2 ${PARENT_SHELL}`}>
      <header className="shrink-0 mb-6 w-full">
        <h1 className="text-title text-text">{s.title}</h1>
        <p className="mt-2 max-w-3xl text-body text-text-muted">
          {s.intro}
        </p>
      </header>

      <div className="flex-1 overflow-y-auto min-h-0 pb-6 space-y-4 w-full">
        {displayChildren.length === 0 ? (
          <Card padding="lg" className="max-w-3xl lg:max-w-none">
            <EmptyState
              icon={Users}
              title={s.emptyTitle}
              message={s.emptyMessage}
            />
          </Card>
        ) : (
          displayChildren.map((c) => (
            <ChildInsightsSection
              key={c.id}
              childId={c.id}
              defaultOpen={displayChildren.length === 1}
              alertCount={unreadByChild ? unreadByChild.get(`child-${c.id}`) ?? 0 : null}
              nickname={c.nickname || c.username || common.unknownChild(c.id)}
            />
          ))
        )}
      </div>
    </div>
  );
};

export default ParentInsightsPage;
