import { useState, useCallback, useEffect, useRef, Suspense, lazy } from 'react';
import {
  Volume2, VolumeX, MessagesSquare, Sparkles,
  Mic, MicOff, Phone, PhoneOff, Loader2, Wifi, WifiOff, Hand,
} from 'lucide-react';
import { Button, Card, IconButton, Pill } from '../../components/ui';
import GamificationToasts from '../../features/child/components/GamificationToasts';
import LevelCard from '../../features/child/components/LevelCard';
import ChatInput from '../../features/child/components/ChatInput';
import ChatMessageList from '../../features/child/components/ChatMessageList';
import { useNavVisibility } from '../../features/child/components/navVisibility';
import VoiceMode from '../../features/child/components/VoiceMode';
import SourceRail from '../../features/child/sources/SourceRail';
import AiChip from '../../features/child/ai/AiChip'; // cards-spec (05)
import useSourceCards from '../../features/child/sources/useSourceCards';
import { cx, FOCUS_RING } from '../../components/ui/cx';
import useDialogFocus from '../../features/auth/useDialogFocus';
import ClockChip from '../../features/child/voice/ClockChip';
import NoticeToast from '../../features/child/voice/NoticeToast';
import StatusCard from '../../features/child/voice/StatusCard';
import {
  EndCard, ErrorCard, IdleCard, RefusedCard, StartingView, TextChatEmpty, VoiceRestingCard,
} from '../../features/child/voice/VoiceScreens';
import useSessionClock from '../../features/child/voice/useSessionClock';
import { clockEndFromStart, describeStartFailure } from '../../features/child/voice/voiceGuards';
import { voiceCopy } from '../../features/child/voice/copy';
import '../../features/child/voice/voiceui.css';
import ChildIdleStage from '../../features/child/components/ChildIdleStage';
import useHomeQuest from '../../features/child/quests/useHomeQuest'; // i18n: the real quest title on the Home card
import MeadowStage from '../../features/child/components/MeadowStage'; // avatar-integ: the painted meadow, alive, with Sadiq walking on the path (the default stage)
import LevelBar from '../../features/child/components/LevelBar'; // avatar-integ: the call screen's level bar (WebUI photo 1)
import useLiveKitRoom from '../../hooks/useLiveKitRoom';
import { useAuth } from '../../context/AuthContext';
import { startSession, endSession } from '../../services/conversationService';
import { patchChildProfile } from '../../services/authService';
import { fetchLevel } from '../../services/gamificationService';
import {
  isDemoSession, readDemoLang, resetOrStartDemo, writeDemoLang,
} from '../../services/demoService';
import { ROUTES } from '../../routes';
import { num, pct, stringsFor } from '../../i18n'; // i18n // avatar-integ
import { isForestEnabled } from '../../features/child/components/forest/forestFlag';

// The forest scene (task 06b) is opt-in: ?forest=1 or VITE_FOREST_SCENE=1. Off by default.
const ForestStage = lazy(() => import('../../features/child/components/forest/ForestStage'));

// How long the child can read the last words after the agent says the chat is over.
const END_READ_MS_TEXT = 3500;
const END_READ_MS_VOICE = 1200;
// If the agent never says it (a crash), the screen closes this long after the clock ran out.
const END_FORCE_AFTER_MS = 40000;
// The "one minute left" note stays this long.
const ONE_MINUTE_TOAST_MS = 9000;

const HOLD_TO_TALK_KEY = 'sadiq_hold_to_talk'; // hk-14
const HOLD_RELEASE_MS = 300;

const NO_SESSION = { voiceMode: 'eleven', notice: null, clock: { endsAt: null, totalSeconds: 0 }, afterVoiceError: false };

/** 'ar' | 'en' from a profile's language_preference, or null when unknown. */
const profileLanguage = (value) => {
  if (!value) return null;
  return String(value).toLowerCase().startsWith('en') ? 'en' : 'ar';
};

// DEV only: exposes window.__mockReference(kind) (see MOCK_KINDS in sources/mockReference.js) so the source cards can be
// tried before the agent sends real `reference` events. The constant condition lets
// Vite drop it (and the placeholder module) from production builds.
const installMockReference = import.meta.env.DEV
  ? (handler) => {
      let cancelled = false;
      import('../../features/child/sources/mockReference').then(({ buildMockReference }) => {
        if (cancelled) return;
        window.__mockReference = (kind = 'verse') => handler(buildMockReference(kind));
      });
      return () => {
        cancelled = true;
        delete window.__mockReference;
      };
    }
  : null;

const ConversationPage = () => {
  // idle | connecting | refused | error | connected | ending | ended
  const [sessionState, setSessionState] = useState('idle');
  // avatar-integ: sessionId is only read by scripts/check-session-startup.mjs (the ref is the live copy).
  // eslint-disable-next-line no-unused-vars
  const [sessionId, setSessionId] = useState(null);
  const [session, setSession] = useState(NO_SESSION);
  const [error, setError] = useState(null);
  const [refusal, setRefusal] = useState(null);
  const [isChatMode, setIsChatMode] = useState(false);
  const [levelData, setLevelData] = useState(null);
  const [showConnectingDelayHint, setShowConnectingDelayHint] = useState(false);
  const [sessionBanner, setSessionBanner] = useState(false);
  const [micTapFeedback, setMicTapFeedback] = useState(false);
  // hk-14: hold-to-talk (off by default, remembered on this device). `held` = the child is pressing the mic (or its 300 ms tail).
  const [holdToTalk, setHoldToTalk] = useState(() => {
    try { return localStorage.getItem(HOLD_TO_TALK_KEY) === '1'; } catch { return false; }
  });
  const [held, setHeld] = useState(false);
  const heldRef = useRef(false);
  const muteTimerRef = useRef(null);
  const [showExitModal, setShowExitModal] = useState(false);
  const [gamToasts, setGamToasts] = useState([]);
  const [noticeClosed, setNoticeClosed] = useState(false);
  const [timeToastClosed, setTimeToastClosed] = useState(false);
  const [restBusy, setRestBusy] = useState(false);
  const [endBusy, setEndBusy] = useState(false);
  const [endError, setEndError] = useState('');
  const { user, startDemoSession, refreshProfile } = useAuth();
  const homeQuest = useHomeQuest();
  // Sadiq speaks the language on the child's profile. A demo starts in the landing's language;
  // a child's own account starts in the profile's, until the child picks one here.
  const profileLang = profileLanguage(user?.profile?.language_preference);
  const [lang, setLang] = useState(() => (!isDemoSession() && profileLang) || readDemoLang());
  const langPickedRef = useRef(false);
  const [hasTalked, setHasTalked] = useState(false);
  const idleControl = useRef(null);
  const gamToastIdRef = useRef(0);
  const closeExitModal = useCallback(() => setShowExitModal(false), []);
  const { dialogRef: exitDialogRef, initialRef: exitStayRef } = useDialogFocus(showExitModal, closeExitModal);

  const sessionIdRef = useRef(null);
  const startupRef = useRef(null);
  const pageHideFiredRef = useRef(false);
  const finishedRef = useRef(false);

  const { cards: sourceCards, history: sourceHistory, pinned: pinnedCards, addReference, dismiss: dismissCard, reopen: reopenCards, clearReferences } = useSourceCards();

  const t = voiceCopy(lang);
  const demo = isDemoSession();
  const textMode = session.voiceMode === 'text';

  const [forestOn] = useState(isForestEnabled);
  // The lip-sync vowel model, the avatar context and the search hologram all follow the child's language. // avatar-integ
  const lk = useLiveKitRoom({ lang });
  const { disconnect, setMicEnabled } = lk;
  const setAvatarLang = lk.setAvatarLang;
  useEffect(() => {
    setAvatarLang(lang);
  }, [setAvatarLang, lang]);
  const { setHidden: setNavHidden } = useNavVisibility();

  const connected = sessionState === 'connected';
  const clock = useSessionClock({
    endsAt: connected ? session.clock.endsAt : null,
    signal: connected ? lk.sessionLimit : null,
  });
  const clockPhase = clock.phase;
  const limitSaid = connected ? lk.sessionLimit?.phase : null;

  const toggleLang = useCallback(() => {
    langPickedRef.current = true;
    setLang((prev) => {
      const next = prev === 'ar' ? 'en' : 'ar';
      writeDemoLang(next);
      return next;
    });
  }, []);

  // The profile arrives after the first render: follow it until the child picks a language.
  useEffect(() => {
    if (demo || langPickedRef.current || !profileLang) return;
    setLang(profileLang);
    writeDemoLang(profileLang); // qa: keep the nav and toasts on the same language as this page
  }, [demo, profileLang]);

  // Warm the avatar while the child is on the idle screen: this fetches the lazy Avatar
  // chunk, and Avatar.jsx calls useGLTF.preload on load, so the model is already
  // downloaded when the session connects. If the download fails, Avatar renders nothing
  // (the background stays) and clears the cached error so the next session retries.
  useEffect(() => {
    import('../../features/child/components/avatar/Avatar').catch(() => {});
  }, []);

  useEffect(() => {
    fetchLevel()
      .then(setLevelData)
      .catch(() => {});
  }, []);

  useEffect(() => {
    setNavHidden(['connecting', 'connected', 'ending'].includes(sessionState));
  }, [sessionState, setNavHidden]);

  useEffect(() => () => setNavHidden(false), [setNavHidden]);

  useEffect(() => {
    if (sessionState !== 'connecting') return undefined;
    const timer = window.setTimeout(() => {
      setShowConnectingDelayHint(true);
    }, 8000);
    return () => {
      window.clearTimeout(timer);
      setShowConnectingDelayHint(false);
    };
  }, [sessionState]);

  useEffect(() => {
    if (sessionState !== 'connected') return undefined;
    if (lk.connectionState !== 'disconnected') return undefined;
    const timer = window.setTimeout(() => setSessionBanner(true), 30000);
    return () => window.clearTimeout(timer);
  }, [lk.connectionState, sessionState]);

  useEffect(() => {
    return () => {
      startupRef.current?.abort();
      const sid = sessionIdRef.current;
      sessionIdRef.current = null;
      if (sid && !pageHideFiredRef.current) {
        endSession(sid).catch(() => {});
      }
    };
  }, []);

  useEffect(() => {
    const handlePageHide = () => {
      pageHideFiredRef.current = true;
      startupRef.current?.abort();
      disconnect().catch(() => {});
      const sid = sessionIdRef.current;
      sessionIdRef.current = null;
      if (!sid) return;

      const token = localStorage.getItem('access_token');
      const baseUrl = import.meta.env.VITE_API_BASE_URL;

      fetch(`${baseUrl}/api/conversation/sessions/${sid}/end/`, {
        method: 'POST',
        keepalive: true,
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      }).catch(() => {});
    };

    window.addEventListener('pagehide', handlePageHide);
    return () => window.removeEventListener('pagehide', handlePageHide);
  }, [disconnect]);

  useEffect(() => {
    if (sessionState !== 'connected') return undefined;
    const handler = (e) => {
      e.preventDefault();
      e.returnValue = '';
    };
    window.addEventListener('beforeunload', handler);
    return () => window.removeEventListener('beforeunload', handler);
  }, [sessionState]);

  useEffect(() => {
    if (sessionState !== 'connected') return undefined;
    window.history.pushState({ sessionGuard: true }, '');
    const handlePopState = () => {
      window.history.pushState({ sessionGuard: true }, '');
      setShowExitModal(true);
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, [sessionState]);

  const refreshLevel = useCallback(() => {
    fetchLevel().then(setLevelData).catch(() => {});
  }, []);

  const dismissGamToast = useCallback((id) => {
    setGamToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  // Live gamification updates pushed by the agent over the data channel:
  // refresh the level bar instantly and surface point/quest/level toasts.
  const handleGamificationEvent = useCallback((ev) => {
    if (!ev) return;

    if (typeof ev.total_points === 'number') {
      setLevelData((prev) => ({
        ...(prev || {}),
        total_points: ev.total_points,
        level_number: ev.level_number,
        level_name: ev.level_name,
        progress_pct: ev.progress_pct,
      }));
    }

    const nextId = () => {
      gamToastIdRef.current += 1;
      return gamToastIdRef.current;
    };

    const pointToasts =
      ev.type === 'points'
        ? [{ id: nextId(), kind: 'points', delta: ev.delta, subtitle: ev.reason || '' }]
        : [];
    const questToasts =
      ev.type === 'quest_completed'
        ? [
            {
              id: nextId(),
              kind: 'quest',
              questTitle: ev.quest_title,
              subtitle: `+${ev.reward_points} points`,
            },
            ...(ev.new_badges || []).map((b) => ({
              id: nextId(),
              kind: 'quest',
              questTitle: `Badge earned: ${b.name}`,
              subtitle: '',
            })),
          ]
        : [];
    const levelToasts = ev.leveled_up
      ? [
          {
            id: nextId(),
            kind: 'levelup',
            levelNumber: ev.level_number,
            levelName: ev.level_name,
            subtitle: 'Keep going!',
          },
        ]
      : [];

    const newToasts = [...pointToasts, ...questToasts, ...levelToasts];
    if (newToasts.length) {
      setGamToasts((prev) => [...prev, ...newToasts].slice(-4));
    }
  }, []);

  const { onGamificationEvent, onReference } = lk;
  useEffect(
    () => onGamificationEvent(handleGamificationEvent),
    [onGamificationEvent, handleGamificationEvent],
  );

  // Source cards (verse / hadith) pushed by the agent on the `reference` topic.
  useEffect(() => onReference(addReference), [onReference, addReference]);

  useEffect(
    () => (installMockReference ? installMockReference(addReference) : undefined),
    [addReference],
  );

  // Close the server side and the room, whatever the reason. Never throws.
  const closeSession = useCallback(async () => {
    const sid = sessionIdRef.current;
    if (sid) {
      try { await endSession(sid); } catch { /* the agent may have ended it already */ }
    }
    try { await lk.disconnect(); } catch { /* already closed */ }
    setSessionId(null);
    sessionIdRef.current = null;
  }, [lk]);

  // avatar-integ: 05's cancellable startup (AbortController + rollback of a late allocation)
  // carrying demo-mvp's options (text-only retry, voice mode, notice, session clock).
  const handleStartSession = useCallback(async ({ textOnly = false, afterVoiceError = false } = {}) => {
    if (startupRef.current) return;
    const startup = new AbortController();
    startupRef.current = startup;
    finishedRef.current = false;
    setSessionState('connecting');
    setError(null);
    setRefusal(null);
    setSessionBanner(false);
    setNoticeClosed(false);
    setTimeToastClosed(false);
    setShowExitModal(false);
    clearReferences();
    let sid = null;
    try {
      // Sadiq greets in the profile's language. If this screen shows the other one (the child
      // tapped the language pill, or the demo landing was in English), save it first so the
      // voice and the words on screen match. Best effort: on failure Sadiq keeps the old one.
      if (profileLang && profileLang !== lang) {
        try {
          await patchChildProfile({ language_preference: lang });
          refreshProfile();
        } catch { /* keep going in the profile's language */ }
      }
      if (startup.signal.aborted) return;
      const data = await startSession({ textOnly });
      sid = data.session_id;
      if (startup.signal.aborted) {
        await endSession(sid).catch(() => {});
        return;
      }
      const receivedAt = Date.now();
      const voiceMode = data.voice_mode || 'eleven';
      setSessionId(sid);
      sessionIdRef.current = sid;
      setSession({
        voiceMode,
        notice: data.notice || null,
        clock: clockEndFromStart(data, receivedAt),
        afterVoiceError,
      });
      setIsChatMode(voiceMode === 'text');
      // Hold-to-talk publishes the mic already muted: the permission prompt comes now (not mid-hold) and no audio is sent
      // before the first hold.
      await lk.connect(data.livekit_token, data.livekit_url, startup.signal, {
        micEnabled: voiceMode !== 'text',
        publishMuted: holdToTalk,
      });
      if (startup.signal.aborted) return;
      if (voiceMode === 'text') lk.setSpeakerMuted(true);
      setSessionState('connected');
    } catch (err) {
      await disconnect().catch(() => {});
      if (sid && sessionIdRef.current === sid) {
        sessionIdRef.current = null;
        await endSession(sid).catch(() => {});
      }
      if (!startup.signal.aborted) {
        setSessionId(null);
        setSession(NO_SESSION);
        const info = describeStartFailure(err, t, lang);
        if (info.kind === 'refused') {
          setRefusal(info);
          setSessionState('refused');
        } else {
          setError(info.message);
          setSessionState('error');
        }
      }
    } finally {
      if (startupRef.current === startup) startupRef.current = null;
    }
  }, [lk, disconnect, t, lang, profileLang, refreshProfile, clearReferences, holdToTalk]);

  const handleEndSession = useCallback(async () => {
    if (sessionState !== 'connected') return;
    setSessionState('ending');
    await closeSession();
    setIsChatMode(false);
    refreshLevel();
    setSession(NO_SESSION);
    setHasTalked(true);
    setSessionState('idle');
  }, [sessionState, closeSession, refreshLevel]);

  // The time limit is up: the agent said goodbye (session_ended), or the room closed after
  // the clock ran out, or nothing came at all. Show the warm end screen.
  const finishSession = useCallback(async () => {
    if (finishedRef.current) return;
    finishedRef.current = true;
    setEndBusy(false);
    setEndError('');
    await closeSession();
    setIsChatMode(false);
    refreshLevel();
    setSessionState('ended');
  }, [closeSession, refreshLevel]);

  // The timers below must not restart on every render (the clock re-renders each second and
  // finishSession changes with the room), so they call it through a ref.
  const finishRef = useRef(finishSession);
  useEffect(() => { finishRef.current = finishSession; }, [finishSession]);

  useEffect(() => {
    if (!connected) return undefined;
    const closed = lk.connectionState === 'disconnected';
    // The agent may close the room right behind session_ended (the message can be lost), so a
    // closed room once the ending began counts as the end too.
    const ending = limitSaid === 'ending' || clockPhase === 'ending' || clockPhase === 'over';
    if (limitSaid !== 'ended' && !(ending && closed)) return undefined;
    const wait = textMode ? END_READ_MS_TEXT : END_READ_MS_VOICE;
    const timer = window.setTimeout(() => { finishRef.current(); }, wait);
    return () => window.clearTimeout(timer);
  }, [connected, limitSaid, clockPhase, lk.connectionState, textMode]);

  useEffect(() => {
    if (!connected || !session.clock.endsAt) return undefined;
    const wait = Math.max(0, session.clock.endsAt + END_FORCE_AFTER_MS - Date.now());
    const timer = window.setTimeout(() => { finishRef.current(); }, wait);
    return () => window.clearTimeout(timer);
  }, [connected, session.clock.endsAt]);

  // The one-minute note shows by itself and goes away by itself.
  useEffect(() => {
    if (clockPhase !== 'warn') return undefined;
    const timer = window.setTimeout(() => setTimeToastClosed(true), ONE_MINUTE_TOAST_MS);
    return () => window.clearTimeout(timer);
  }, [clockPhase]);

  // Sadiq's voice failed: end this room and, if the child agrees, open a text-only one.
  const handleRestChat = useCallback(async () => {
    setRestBusy(true);
    await closeSession();
    setRestBusy(false);
    handleStartSession({ textOnly: true, afterVoiceError: true });
  }, [closeSession, handleStartSession]);

  const handleRestBack = useCallback(async () => {
    setRestBusy(true);
    await closeSession();
    setRestBusy(false);
    setIsChatMode(false);
    setSession(NO_SESSION);
    setSessionState('idle');
  }, [closeSession]);

  const handleDemoStartOver = useCallback(async () => {
    setEndBusy(true);
    setEndError('');
    try {
      const payload = await resetOrStartDemo();
      await startDemoSession(payload, 'child');
      // A full load gives every screen a clean slate (chat, level, summaries).
      window.location.assign(ROUTES.CHILD_HOME);
    } catch {
      setEndError(t.startOverFailed);
      setEndBusy(false);
    }
  }, [startDemoSession, t]);

  // hk-14: hold-to-talk. Press = mic on at once; release = mic off after 300 ms (a press inside that gap cancels it).
  const holdActive = holdToTalk && !isChatMode && !textMode;
  const releaseHold = useCallback(() => {
    window.clearTimeout(muteTimerRef.current);
    muteTimerRef.current = null;
    heldRef.current = false;
    setHeld(false);
  }, []);
  const pressStart = useCallback(() => {
    window.clearTimeout(muteTimerRef.current);
    muteTimerRef.current = null;
    if (heldRef.current) return;
    heldRef.current = true;
    setHeld(true);
    setMicEnabled(true);
  }, [setMicEnabled]);
  const pressEnd = useCallback(() => {
    if (!heldRef.current) return;
    window.clearTimeout(muteTimerRef.current);
    muteTimerRef.current = window.setTimeout(() => {
      muteTimerRef.current = null;
      heldRef.current = false;
      setHeld(false);
      setMicEnabled(false);
    }, HOLD_RELEASE_MS);
  }, [setMicEnabled]);
  const toggleHoldToTalk = useCallback(() => {
    const next = !holdToTalk;
    setHoldToTalk(next);
    try { localStorage.setItem(HOLD_TO_TALK_KEY, next ? '1' : '0'); } catch { /* private mode: not remembered */ }
    releaseHold();
    if (!isChatMode && !textMode) setMicEnabled(!next); // ON: start muted. OFF: the mic comes back.
  }, [holdToTalk, isChatMode, textMode, releaseHold, setMicEnabled]);
  useEffect(() => () => window.clearTimeout(muteTimerRef.current), []);
  // A hold in progress when the session ends would leave the next session's first press doing nothing.
  useEffect(() => { if (!connected) releaseHold(); }, [connected, releaseHold]);
  // Desktop: hold Space to talk (not while typing, and not when Space should press another focused control).
  useEffect(() => {
    if (!holdActive || !connected) return undefined;
    const ignore = (e) => {
      const el = e.target;
      if (!(el instanceof Element)) return false;
      if (el.closest('input, textarea, select, [contenteditable=""], [contenteditable="true"]')) return true;
      return Boolean(el.closest('button, a[href], [role="button"]')) && !el.closest('[data-hold-mic], [data-hold-toggle]');
    };
    const down = (e) => {
      if (e.code !== 'Space' || ignore(e)) return;
      e.preventDefault(); // no page scroll, no button click
      if (!e.repeat) pressStart();
    };
    const up = (e) => {
      if (e.code !== 'Space' || ignore(e)) return;
      e.preventDefault();
      pressEnd();
    };
    window.addEventListener('keydown', down);
    window.addEventListener('keyup', up);
    window.addEventListener('blur', pressEnd); // the key-up never arrives once the window loses focus
    return () => {
      window.removeEventListener('keydown', down);
      window.removeEventListener('keyup', up);
      window.removeEventListener('blur', pressEnd);
    };
  }, [holdActive, connected, pressStart, pressEnd]);

  const handleModeToggle = useCallback(async () => {
    const enteringChat = !isChatMode;
    setIsChatMode(enteringChat);
    releaseHold();
    await lk.setMicEnabled(!enteringChat && !holdToTalk);
    // Chat = read-first; voice = hear the agent. Restore audio when switching back to voice.
    lk.setSpeakerMuted(enteringChat);
  }, [isChatMode, lk, holdToTalk, releaseHold]);

  // A send into a room that is closing must not throw into the page (ChatInput does not await).
  const handleSendMessage = useCallback(
    (text) => { lk.sendTextMessage(text).catch(() => {}); },
    [lk],
  );

  const handleMicTap = useCallback(() => {
    if (holdToTalk && !isChatMode && !textMode) return; // hold-to-talk: the mic is pressed, not tapped
    setMicTapFeedback(true);
    lk.toggleMic();
    window.setTimeout(() => setMicTapFeedback(false), 180);
  }, [lk, holdToTalk, isChatMode, textMode]);

  // i18n: Arabic digits in Arabic, and the backend's English level name shown in Arabic when we know it.
  const levelNames = stringsFor(lang).levels;
  const levelName = levelData ? (lang === 'ar' ? levelNames[levelData.level_name] : levelData.level_name) : null;
  const levelTitle = levelData
    ? [t.level(num(levelData.level_number, lang)), levelName].filter(Boolean).join(lang === 'ar' ? ' · ' : ' ')
    : t.level(num(1, lang));
  const levelProgress = levelData?.progress_pct ?? 0;
  const levelPercent = pct(Math.round(levelProgress), lang);

  // avatar-integ: the painted meadow is the default stage (the forest is opt-in, ?forest=1). Home: Sadiq walks up the path; the talk
  // starts: the camera eases ONCE into the call framing and stays steady. 'talk' is the call framing, anything else is Home.
  const meadowOn = !forestOn;
  const meadowVoice = meadowOn && !isChatMode;
  // With the forest on, one persistent stage sits behind every screen so the
  // camera can glide from the idle shot to the talking shot.
  const stageFor = (node, phase, hidden = false, stageProps = {}) => { // cards-spec (05): was withForest; the AI chip wraps it below
    if (meadowOn) {
      return (
        <MeadowStage
          phase={phase === 'talk' ? 'call' : 'home'}
          hidden={hidden}
          avatarSpeaking={lk.agentSpeaking}
          agentState={lk.agentState}
          getAudioLevel={lk.getAgentAudioLevel}
          getLipsync={lk.getAgentLipsync}
          getAvatarContext={lk.getAvatarContext}
          lang={lang}
          walkControlRef={stageProps.walkControlRef}
        >
          {node}
        </MeadowStage>
      );
    }
    if (!forestOn) return node;
    return (
      <Suspense fallback={node}>
        <ForestStage
          phase={phase}
          hidden={hidden}
          avatarSpeaking={lk.agentSpeaking}
          agentState={lk.agentState}
          getAudioLevel={lk.getAgentAudioLevel}
          getLipsync={lk.getAgentLipsync} // avatar-integ
          getAvatarContext={lk.getAvatarContext} // 06-avatar-context
          lang={lang} // 06-avatar-context
          {...stageProps}
        >
          {node}
        </ForestStage>
      </Suspense>
    );
  };

  // cards-spec (05): every session state (connecting, connected, ended, refused, error) and both modes go through here,
  // so this is the single place for the permanent AI chip. It is position: fixed, so it never scrolls away.
  const withForest = (node, phase, hidden = false, stageProps = {}) => (
    <>
      {stageFor(node, phase, hidden, stageProps)}
      <AiChip lang={lang} />
    </>
  );

  // With the forest on, cards sit below the avatar (phones) or beside it (desktop), not on top of it.
  const forestPlace = forestOn ? 'items-end pb-6 lg:items-center lg:justify-end lg:pe-[8%]' : 'items-center';

  const topLevelCard = (
    <header className="relative z-20 shrink-0 px-4 pt-4">
      <div className="mx-auto flex w-full max-w-2xl items-center justify-center">
        <LevelCard
          title={levelTitle}
          progress={levelProgress}
          percentLabel={levelPercent}
          dir={t.dir}
          progressLabel={t.progress}
        />
      </div>
    </header>
  );

  // The idle screen and the cards share one forest stage: same walk-in, same control ref.
  const stageBase = { walkControlRef: idleControl, walkPreset: 'landing' };

  // A screen that is not the chat: the level card on top, one card below.
  const cardScreen = (card, phase = 'wide') => withForest(
    <div className="flex min-h-0 flex-1 flex-col overflow-x-hidden">
      {topLevelCard}
      <section className={`flex min-h-0 flex-1 justify-center overflow-y-auto ${forestPlace}`}>
        {card}
      </section>
    </div>,
    phase,
    false,
    stageBase,
  );

  // ── Idle and starting: the child idle screen (Arabic first, in the demo forest) ──
  if (sessionState === 'idle' || sessionState === 'connecting') {
    return withForest(
      <ChildIdleStage
        status={sessionState}
        ended={hasTalked}
        slow={showConnectingDelayHint}
        levelData={levelData}
        quest={homeQuest}
        lang={lang}
        onToggleLang={toggleLang}
        langLabel={t.langToggleLabel}
        onStart={() => handleStartSession()}
        controlRef={idleControl}
        forest={forestOn}
        meadow={meadowOn} // avatar-integ
      />,
      meadowOn && sessionState === 'connecting' ? 'talk' : 'wide', // avatar-integ: the camera eases into the call framing when the talk starts
      false,
      { ...stageBase, interactive: true },
    );
  }

  // ── Ending ──
  if (sessionState === 'ending') {
    return cardScreen(<StartingView t={t} slow={false} />, meadowOn ? 'talk' : 'wide'); // avatar-integ: the goodbye stays in the call framing
  }

  // ── Refused: the daily cap, a throttle, the voice switched off, a busy room ──
  if (sessionState === 'refused' && refusal) {
    const retryable = refusal.code === 'rate_limited' || refusal.code === 'busy';
    return cardScreen(
      <RefusedCard
        t={t}
        refusal={refusal}
        onBack={() => (retryable ? handleStartSession() : setSessionState('idle'))}
        onChat={refusal.code === 'busy' ? () => handleStartSession({ textOnly: true }) : undefined}
      />,
    );
  }

  // Error: retry prompt
  if (sessionState === 'error') {
    return cardScreen(
      <ErrorCard t={t} message={error || t.genericError} onRetry={() => handleStartSession()} />,
    );
  }

  // ── Ended: the time limit and the goodbye ──
  if (sessionState === 'ended') {
    return cardScreen(
      <EndCard
        t={t}
        demo={demo}
        busy={endBusy}
        error={endError}
        onStartOver={handleDemoStartOver}
        onAgain={() => handleStartSession()}
      />,
    );
  }

  const isMidSessionDisconnected = connected && lk.connectionState === 'disconnected' && limitSaid !== 'ended' && limitSaid !== 'ending' && clockPhase !== 'ending' && clockPhase !== 'over';
  const showClock = clock.active && !lk.voiceError;
  // The known notice uses this screen's words (they name Sadiq the same way as the rest of it).
  const noticeText = session.notice
    ? (session.notice.code === 'voice_resting' ? t.voiceResting : (session.notice[lang] || ''))
    : (session.afterVoiceError ? t.voiceResting : '');
  // The goodbye has begun: the agent takes no new turns, so the chat box closes too (a line
  // typed now would get no answer).
  const goodbyeTime = limitSaid === 'ending' || limitSaid === 'ended'
    || clockPhase === 'ending' || clockPhase === 'over';
  const showNotice = Boolean(noticeText) && !noticeClosed && !lk.voiceError;
  const showTimeToast = clockPhase === 'warn' && !timeToastClosed && !lk.voiceError;
  // Notes to the child: in voice mode they float over the scene, in the text chat they sit
  // above the messages so they never cover a bubble.
  const toasts = (showNotice || showTimeToast) ? (
    <>
      {showNotice ? (
        <div className="pointer-events-auto">
          <NoticeToast kind="rest" onClose={() => setNoticeClosed(true)} closeLabel={t.noticeClose} dir={t.dir} lang={t.lang}>
            {noticeText}
          </NoticeToast>
        </div>
      ) : null}
      {showTimeToast ? (
        <div className="pointer-events-auto">
          <NoticeToast kind="time" onClose={() => setTimeToastClosed(true)} closeLabel={t.noticeClose} dir={t.dir} lang={t.lang}>
            {t.oneMinute}
          </NoticeToast>
        </div>
      ) : null}
    </>
  ) : null;

  // hk-14: the paused mic, unmistakable: a banner while the mic is off in voice mode (never in text or chat mode).
  const voiceMuted = !isChatMode && !textMode && lk.isMicMuted && lk.agentConnected && lk.connectionState === 'connected';
  const micBannerText = voiceMuted ? (holdToTalk ? t.holdBanner : t.micPausedBanner) : '';
  // Visual only: the words are announced by one live region that stays mounted (srMicStatus), since a region that is
  // inserted with its text is often not read out.
  const micBanner = voiceMuted ? (
    <span
      aria-hidden="true"
      className="inline-flex items-center gap-2 rounded-full bg-accent px-4 py-2 text-body font-semibold text-on-accent shadow-[0_4px_16px_var(--color-shadow)] max-sm:me-auto max-sm:max-w-[calc(100%-6.5rem)] max-sm:text-label"
    >
      {holdToTalk ? <Hand className="size-5" /> : <MicOff className="size-5" />}
      {micBannerText}
    </span>
  ) : null;
  // In hold-to-talk the hint stays put while the child talks, so it is not announced again after every turn.
  const srMicStatus = <p role="status" className="sr-only">{holdActive && connected ? t.holdBanner : micBannerText}</p>;

  // Status pill for the avatar stage: opaque soft fills, always AA.
  let status;
  if (lk.connectionState === 'connecting') {
    status = (
      <Pill variant="info" role="status" icon={<Loader2 aria-hidden="true" className="size-4 motion-safe:animate-spin" />}>
        {t.statusConnecting}
      </Pill>
    );
  } else if (lk.connectionState === 'disconnected') {
    status = (
      <Pill variant="danger" role="status" icon={<WifiOff aria-hidden="true" className="size-4" />}>
        {t.statusDisconnected}
      </Pill>
    );
  } else if (!lk.agentConnected) {
    status = (
      <Pill variant="neutral" role="status" icon={<Wifi aria-hidden="true" className="size-4" />}>
        {t.statusWaiting}
      </Pill>
    );
  } else if (voiceMuted) {
    status = meadowVoice ? null : micBanner; // on the meadow the banner sits in the stage (VoiceMode status below)
  } else if (lk.agentSpeaking) {
    status = (
      <Pill variant="success" icon={<Volume2 aria-hidden="true" className="size-4" />}>
        {t.statusSpeaking}
      </Pill>
    );
  } else if (lk.isMicMuted) {
    status = (
      <Pill variant="warning" icon={<MicOff aria-hidden="true" className="size-4" />}>
        {t.statusMicOff}
      </Pill>
    );
  } else {
    status = (
      <Pill variant="success" icon={<Mic aria-hidden="true" className="size-4" />}>
        {t.statusListening}
      </Pill>
    );
  }

  // hk-14: the mic key's props. Normal mode: tap to mute or unmute. Hold-to-talk: press and hold (touch-action none and
  // no context menu, so a long press on a phone does not select text or open a menu).
  // Not held but the mic is live (a mute that failed): the word follows the mic, like the icon does.
  const micWord = holdActive
    ? (held ? t.micLabelHeld : (lk.isMicMuted ? t.micLabelHold : t.micLabelOn))
    : (lk.isMicMuted ? t.micLabelPaused : t.micLabelOn);
  const micProps = holdActive
    ? {
      'data-hold-mic': '',
      'data-hold': 'true',
      'data-held': held ? 'true' : undefined,
      'aria-pressed': held,
      'aria-label': t.holdBanner,
      title: t.holdBanner,
      // Pointer capture keeps the hold while a finger drifts off the key; the release still ends it.
      onPointerDown: (e) => {
        if (e.button !== 0) return;
        try { e.currentTarget.setPointerCapture(e.pointerId); } catch { /* the hold works without it */ }
        pressStart();
      },
      onPointerUp: pressEnd,
      onPointerCancel: pressEnd,
      onLostPointerCapture: pressEnd,
      onBlur: pressEnd, // Enter held, then focus moved away: the key-up never comes
      // Enter on the focused key holds like Space does.
      onKeyDown: (e) => {
        if (e.key !== 'Enter') return;
        e.preventDefault();
        if (!e.repeat) pressStart();
      },
      onKeyUp: (e) => {
        if (e.key !== 'Enter') return;
        e.preventDefault();
        pressEnd();
      },
      onContextMenu: (e) => e.preventDefault(),
    }
    : {
      'data-hold-mic': '',
      'aria-label': lk.isMicMuted ? t.micOff : t.micOn,
      title: lk.isMicMuted ? t.micOff : t.micOn,
      onClick: handleMicTap,
    };

  const speakerButton = (label) => (
    <IconButton
      label={label}
      onClick={lk.toggleSpeaker}
      icon={
        lk.isSpeakerMuted
          ? <VolumeX aria-hidden="true" className="size-6" />
          : <Volume2 aria-hidden="true" className="size-6" />
      }
    />
  );

  // ── Connected: active session ──
  return withForest(
    <div className="relative flex min-h-0 flex-1 flex-col" dir={t.dir} lang={t.lang}>
      <GamificationToasts toasts={gamToasts} onDone={dismissGamToast} />

      {lk.voiceError ? (
        <div className="vu-scrim">
          <VoiceRestingCard
            t={t}
            canChat={lk.voiceError.code !== 'voice_off'}
            busy={restBusy}
            onChat={handleRestChat}
            onBack={handleRestBack}
          />
        </div>
      ) : null}

      {showExitModal ? (
        <div
          ref={exitDialogRef}
          className="absolute inset-0 z-50 flex items-center justify-center bg-black/50 px-6"
          role="dialog"
          aria-modal="true"
          aria-labelledby="exit-title"
        >
          <Card padding="lg" className="w-full max-w-sm text-center">
            <p id="exit-title" className="text-title text-text">{t.exitTitle}</p>
            <p className="mt-2 text-body text-text-muted">{t.exitBody}</p>
            <div className="mt-6 flex flex-col gap-3">
              <Button onClick={() => { closeExitModal(); handleEndSession(); }}>
                {t.exitYes}
              </Button>
              <Button ref={exitStayRef} variant="secondary" onClick={closeExitModal}>
                {t.exitNo}
              </Button>
            </div>
          </Card>
        </div>
      ) : null}

      {sessionBanner || isMidSessionDisconnected ? (
        <div className="absolute inset-x-0 top-0 z-40 px-4 pt-4">
          <Card className="mx-auto flex max-w-2xl flex-wrap items-center justify-between gap-3" role="alert">
            <p className="min-w-0 flex-1 text-body text-text">{t.dropped}</p>
            <Button
              onClick={() => {
                setSessionBanner(false);
                handleEndSession();
              }}
            >
              {t.newSession}
            </Button>
          </Card>
        </div>
      ) : null}

      {meadowOn ? (
        <>
          {/* avatar-integ: WebUI photo 1. The clock and the status on one side, the Voice | Chat pill on the other. Chat mode keeps the same header (i18n: parity with the call). */}
          <header className="mc-top">
            <div className="mc-top-start">
              {isChatMode ? (
                <button type="button" className="mc-btn mc-end mc-end-mini" aria-label={t.endSession} title={t.endSession} onClick={handleEndSession}>
                  <Phone aria-hidden="true" style={{ transform: 'rotate(135deg)' }} />
                </button>
              ) : null}
              {showClock ? (
                <ClockChip
                  secondsLeft={clock.secondsLeft}
                  totalSeconds={session.clock.totalSeconds}
                  phase={clockPhase === 'over' ? 'ending' : clockPhase}
                  t={t}
                  lang={lang}
                />
              ) : null}
              {status}
            </div>
            {textMode ? null : (
              <div className="mc-seg" role="group" aria-label={t.chatTitle}>
                <button type="button" aria-pressed={!isChatMode} onClick={isChatMode ? handleModeToggle : undefined}>{t.modeVoice}</button>
                <button type="button" aria-pressed={isChatMode} onClick={isChatMode ? undefined : handleModeToggle}>{t.modeChat}</button>
              </div>
            )}
          </header>
          {isChatMode ? (
            <div className="mc-chat-level">
              <LevelCard title={levelTitle} progress={levelProgress} percentLabel={levelPercent} dir={t.dir} progressLabel={t.progress} />
            </div>
          ) : (
            <LevelBar levelData={levelData} lang={lang} />
          )}
        </>
      ) : (
      <header className="relative z-30 shrink-0 px-4 pe-[4.75rem] pt-4"> {/* cards-spec (05): pe-[4.75rem] leaves room for the permanent AI chip */}
        <div className="flex items-center justify-between gap-3">
          <div className="flex flex-col items-center gap-1">
            <IconButton
              label={t.endSession}
              variant="secondary"
              onClick={handleEndSession}
              icon={<PhoneOff aria-hidden="true" className="size-6" />}
            />
            <span className="text-label text-text">{t.endLabel}</span>
          </div>

          <LevelCard title={levelTitle} progress={levelProgress} percentLabel={levelPercent} dir={t.dir} progressLabel={t.progress} />

          {textMode ? (
            <div className="size-14 shrink-0" aria-hidden="true" />
          ) : (
            <IconButton
              label={isChatMode ? t.toVoice : t.toChat}
              onClick={handleModeToggle}
              icon={
                isChatMode
                  ? <Sparkles aria-hidden="true" className="size-6" />
                  : <MessagesSquare aria-hidden="true" className="size-6" />
              }
            />
          )}
        </div>
        {showClock ? (
          <div className="mt-2 flex justify-center">
            <ClockChip
              secondsLeft={clock.secondsLeft}
              totalSeconds={session.clock.totalSeconds}
              phase={clockPhase === 'over' ? 'ending' : clockPhase}
              t={t}
              lang={lang}
            />
          </div>
        ) : null}
      </header>
      )}

      {!isChatMode && toasts ? (
        <div
          className={`pointer-events-none absolute inset-x-0 z-40 flex flex-col items-center gap-2 px-4 ${showClock ? 'top-[8.5rem]' : 'top-24'}`}
        >
          {toasts}
        </div>
      ) : null}

      {/* Main stage + source rail: side by side on lg+, stacked on phones. */}
      <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto p-4 lg:flex-row lg:overflow-visible">
        <div className="flex min-h-0 flex-1 flex-col gap-4">
          {isChatMode ? (
            <div className="flex min-h-[18rem] flex-1 flex-col overflow-hidden rounded-4xl border border-border bg-surface shadow-[0_4px_16px_var(--color-shadow)]">
              {meadowOn ? null : <div className="flex shrink-0 justify-center pt-3">{status}</div>}
              {toasts ? <div className="relative z-30 flex shrink-0 flex-col items-center gap-2 px-4 pt-2">{toasts}</div> : null}
              <ChatMessageList
                messages={lk.chatMessages}
                lang={lang}
                empty={<TextChatEmpty t={t} onPick={handleSendMessage} />}
              />
              <div className="flex shrink-0 items-center gap-3 border-t border-border p-3">
                {textMode ? null : speakerButton(lk.isSpeakerMuted ? t.unmute : t.mute)}
                <div className="min-w-0 flex-1">
                  <ChatInput
                    onSend={handleSendMessage}
                    autoFocus
                    disabled={goodbyeTime}
                    placeholder={goodbyeTime ? t.ending : t.chatPlaceholder}
                    sendLabel={t.chatSend}
                    label={t.chatTitle}
                    dir={t.dir}
                  />
                </div>
              </div>
            </div>
          ) : (
            <VoiceMode
              agentSpeaking={lk.agentSpeaking}
              agentState={lk.agentState}
              getAudioLevel={lk.getAgentAudioLevel}
              getLipsync={lk.getAgentLipsync} // avatar-integ
              getAvatarContext={lk.getAvatarContext} // 06-avatar-context
              lang={lang} // 06-avatar-context
              forest={forestOn}
              staged={meadowOn} // avatar-integ
              status={meadowVoice ? micBanner : status}
            >
              {meadowVoice ? (
                <>
                  {srMicStatus}
                  {/* avatar-integ: WebUI photo 1: mic, the red end key, the speaker. hk-14: a word under each key, and the hold-to-talk switch. */}
                  <div className="mc-ctl">
                    <button
                      type="button"
                      className="mc-btn"
                      data-muted={lk.isMicMuted ? 'true' : 'false'}
                      data-tap={micTapFeedback ? 'true' : undefined}
                      {...micProps}
                    >
                      {lk.isMicMuted ? <MicOff aria-hidden="true" /> : <Mic aria-hidden="true" />}
                    </button>
                    <span className="mc-lbl">{micWord}</span>
                  </div>
                  <div className="mc-ctl">
                    <button type="button" className="mc-btn mc-end" aria-label={t.endSession} title={t.endSession} onClick={handleEndSession}>
                      <Phone aria-hidden="true" style={{ transform: 'rotate(135deg)' }} />
                    </button>
                    <span className="mc-lbl">{t.endLabel}</span>
                  </div>
                  <div className="mc-ctl">
                    <button
                      type="button"
                      className="mc-btn"
                      data-muted={lk.isSpeakerMuted ? 'true' : 'false'}
                      aria-label={lk.isSpeakerMuted ? t.unmute : t.mute}
                      title={lk.isSpeakerMuted ? t.unmute : t.mute}
                      onClick={lk.toggleSpeaker}
                    >
                      {lk.isSpeakerMuted ? <VolumeX aria-hidden="true" /> : <Volume2 aria-hidden="true" />}
                    </button>
                    <span className="mc-lbl">{t.soundLabel}</span>
                  </div>
                  {textMode ? null : (
                    <div className="mc-ctl mc-ctl-sm">
                      <button
                        type="button"
                        className="mc-btn mc-btn-sm"
                        data-on={holdToTalk ? 'true' : 'false'}
                        aria-pressed={holdToTalk}
                        data-hold-toggle=""
                        aria-label={t.holdToTalk}
                        title={t.holdToTalk}
                        onClick={toggleHoldToTalk}
                      >
                        <Hand aria-hidden="true" />
                      </button>
                      <span className="mc-lbl">{t.holdToTalk}</span>
                    </div>
                  )}
                </>
              ) : (
                <>
              {srMicStatus}
              <div className="flex flex-col items-center gap-1">
                {speakerButton(lk.isSpeakerMuted ? t.unmute : t.mute)}
                <span className="text-label text-text">{t.soundLabel}</span>
              </div>

              <div className="flex flex-col items-center gap-1">
                <button
                  type="button"
                  className={cx(
                    'inline-flex size-16 cursor-pointer items-center justify-center rounded-full select-none touch-none',
                    'transition-transform motion-safe:active:scale-95',
                    FOCUS_RING,
                    lk.isMicMuted ? 'bg-accent text-on-accent' : 'bg-primary text-on-primary',
                    (micTapFeedback || held) && 'scale-95 ring-4 ring-primary-soft',
                  )}
                  data-muted={lk.isMicMuted ? 'true' : 'false'}
                  {...micProps}
                >
                  {lk.isMicMuted
                    ? <MicOff aria-hidden="true" className="size-7" />
                    : <Mic aria-hidden="true" className="size-7" />}
                </button>
                <span className="text-label text-text">{micWord}</span>
              </div>

              {textMode ? (
                <div className="size-14" aria-hidden="true" />
              ) : (
                <div className="flex flex-col items-center gap-1">
                  <IconButton
                    label={t.holdToTalk}
                    variant={holdToTalk ? 'primary' : 'secondary'}
                    aria-pressed={holdToTalk}
                    data-hold-toggle=""
                    onClick={toggleHoldToTalk}
                    icon={<Hand aria-hidden="true" className="size-6" />}
                  />
                  <span className="text-label text-text">{t.holdToTalk}</span>
                </div>
              )}
                </>
              )}
            </VoiceMode>
          )}
        </div>

        {/* avatar-integ: on the meadow call the cards float (.mc-sources) so a verse or hadith card never pushes the
            call keys up over Sadiq or slides under the level rail; elsewhere the wrapper is display: contents. */}
        <div className={meadowVoice ? 'mc-sources' : 'contents'}>
          <SourceRail cards={sourceCards} history={sourceHistory} pinned={pinnedCards} onDismiss={dismissCard} onReopen={reopenCards} bare={meadowVoice} lang={lang} /> {/* cards-spec (05): lang */}
        </div>
      </div>
    </div>,
    'talk',
    isChatMode,
  );
};

export default ConversationPage;
