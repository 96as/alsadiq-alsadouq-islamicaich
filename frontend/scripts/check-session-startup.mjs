// Run: node frontend/scripts/check-session-startup.mjs (native Node, no dependencies).
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import vm from 'node:vm';

const [pageSource, roomSource, focusSource] = await Promise.all([
  readFile(new URL('../src/pages/child/ConversationPage.jsx', import.meta.url), 'utf8'),
  readFile(new URL('../src/hooks/useLiveKitRoom.js', import.meta.url), 'utf8'),
  readFile(new URL('../src/features/auth/useDialogFocus.js', import.meta.url), 'utf8'),
]);
const withoutImports = (source) => source.replace(/^import[\s\S]*?;\r?\n/gm, '')
  .replaceAll('export default function', 'function').replaceAll('import.meta.env', 'env');
// Execute all page hooks/handlers; leave JSX rendering to browser QA.
const pageLogic = withoutImports(pageSource).split('  // i18n: Arabic digits in Arabic,')[0] + `
  return { sessionState, sessionId, error, showExitModal, exitDialogRef,
    exitStayRef: typeof exitStayRef === 'undefined' ? null : exitStayRef,
    closeExitModal: typeof closeExitModal === 'undefined' ? null : closeExitModal,
    handleStartSession, handleEndSession, handleMicTap, setSessionState, lk };
};`;

function deferred() {
  let resolve, reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}

function setup(options = {}) {
  const slots = [], pendingEffects = [], listeners = new Map(), rooms = [], ends = [], requests = [], writes = [];
  let cursor = 0, mounted = true, dirty = true, api, starts = 0;
  const same = (a, b) => a && b && a.length === b.length && a.every((value, i) => Object.is(value, b[i]));
  const audioElements = new Set();
  const document = { body: { appendChild: (el) => audioElements.add(el), contains: (el) => audioElements.has(el) } };
  const element = () => ({ focus() { document.activeElement = this; } });
  const trigger = element(), leave = element(), stay = element();
  document.activeElement = trigger;
  const window = {
    addEventListener(type, handler) {
      if (!listeners.has(type)) listeners.set(type, new Set());
      listeners.get(type).add(handler);
    },
    removeEventListener(type, handler) { listeners.get(type)?.delete(handler); },
    setTimeout: () => 1, clearTimeout() {}, history: { pushState() {} },
  };
  class Room {
    constructor() {
      rooms.push(this);
      this.handlers = new Map();
      this.remoteParticipants = new Map();
      this.micCalls = this.disconnects = this.trackStops = 0;
      this.connected = this.micActive = false;
      this.localParticipant = {
        trackPublications: new Map([['microphone', { track: { stop: () => {
          this.trackStops++;
          this.micActive = false;
        } } }]]),
        setMicrophoneEnabled: async (enabled) => {
          if (enabled) {
            this.micCalls++;
            await options.microphone?.promise;
            if (options.micError) throw options.micError;
          }
          this.micActive = enabled;
        },
        getTrackPublication() {}, sendText: async () => {}, on() {}, // avatar-integ: on() for the child-speaking signal
      };
    }
    on(type, handler) { this.handlers.set(type, handler); }
    removeAllListeners() { this.handlers.clear(); }
    registerTextStreamHandler() {}
    async connect() {
      await options.connection?.promise;
      if (options.connectError) throw options.connectError;
      this.connected = true;
      this.handlers.get('ConnectionStateChanged')?.('connected');
    }
    async disconnect() {
      this.disconnects++;
      if (options.disconnection) await options.disconnection.promise;
      if (options.disconnectError) throw options.disconnectError;
      this.connected = this.micActive = false;
    }
  }
  const sourceCards = { cards: [], addReference() {}, clearReferences() {} };
  const navigation = { setHidden() {} };
  const context = vm.createContext({
    AbortController, TextDecoder, window, document, Room,
    RoomEvent: Object.fromEntries(['ConnectionStateChanged', 'ParticipantConnected', 'ParticipantDisconnected',
      'TrackSubscribed', 'TrackUnsubscribed', 'DataReceived'].map((key) => [key, key])),
    ParticipantEvent: { IsSpeakingChanged: 'IsSpeakingChanged' },
    Track: { Kind: { Audio: 'audio' }, Source: { Microphone: 'microphone' } },
    ConnectionState: { Connected: 'connected', Reconnecting: 'reconnecting', Disconnected: 'disconnected' },
    env: { DEV: false, VITE_API_BASE_URL: 'https://api.example.test' },
    localStorage: { getItem: () => null },
    fetch: async (url, init) => { requests.push({ url, ...init }); },
    fetchLevel: async () => null,
    startSession: async () => {
      starts++;
      if (options.apiError) throw options.apiError;
      return options.allocation ? options.allocation.promise
        : { session_id: `session-${starts}`, livekit_token: 'mock-token', livekit_url: 'wss://example.test' };
    },
    endSession: async (id) => { ends.push(id); if (options.endError) throw options.endError; },
    useSourceCards: () => sourceCards, useNavVisibility: () => navigation,
    // avatar-integ: demo-mvp's voice-state collaborators, stubbed (rendering is browser QA).
    lazy: () => null, Suspense: null,
    useAuth: () => ({ user: null, startDemoSession() {}, refreshProfile() {} }),
    isDemoSession: () => false, readDemoLang: () => 'en', writeDemoLang() {}, resetOrStartDemo: async () => ({}),
    isForestEnabled: () => false, patchChildProfile: async () => ({}),
    // i18n: the Home quest hook is stubbed (rendering is browser QA; the i18n suite covers the strings).
    useHomeQuest: () => null, num: (n) => String(n), pct: (n) => `${n}%`, stringsFor: () => ({ levels: {} }),
    // avatar-integ: avatar-studio and 06-avatar-context collaborators of useLiveKitRoom, stubbed (their own suites cover them).
    TimelineSync: class { agentState() {} push() {} },
    createVisemeDriver: () => ({ read: () => null, dispose() {} }),
    createAvatarContextStore: () => new Proxy({ getContext: () => null }, { get: (target, key) => target[key] ?? (() => {}) }),
    ROUTES: { CHILD_HOME: '/' },
    voiceCopy: () => ({ dir: 'ltr', lang: 'en' }),
    clockEndFromStart: () => ({ endsAt: null, totalSeconds: 0 }),
    describeStartFailure: (err) => ({ kind: 'error', message: err?.message || 'error' }),
    useSessionClock: () => ({ active: false, phase: 'idle', secondsLeft: 0 }),
    useState(initial) {
      const i = cursor++;
      if (!slots[i]) {
        slots[i] = { value: typeof initial === 'function' ? initial() : initial, set(value) { // avatar-integ: lazy initializers run once, as in React
          const next = typeof value === 'function' ? value(slots[i].value) : value;
          writes.push({ mounted, value: next });
          if (!Object.is(next, slots[i].value)) { slots[i].value = next; dirty = true; }
        } };
      }
      return [slots[i].value, slots[i].set];
    },
    useRef(initial) { return slots[cursor++] ??= { current: initial }; },
    useCallback(callback, deps) {
      const i = cursor++;
      if (!same(slots[i]?.deps, deps)) slots[i] = { callback, deps };
      return slots[i].callback;
    },
    useEffect(effect, deps) {
      const i = cursor++;
      if (!same(slots[i]?.deps, deps)) {
        const previous = slots[i];
        slots[i] = { deps, cleanup: previous?.cleanup };
        pendingEffects.push(() => { previous?.cleanup?.(); slots[i].cleanup = effect(); });
      }
    },
  });
  vm.runInContext(withoutImports(focusSource), context, { filename: 'useDialogFocus.js' });
  vm.runInContext(withoutImports(roomSource), context, { filename: 'useLiveKitRoom.js' });
  vm.runInContext(pageLogic, context, { filename: 'ConversationPage.jsx' });
  function render() {
    while (mounted && dirty) {
      dirty = false;
      cursor = 0;
      api = vm.runInContext('ConversationPage()', context);
      if (api.showExitModal) {
        api.exitDialogRef.current = { querySelector: () => leave, querySelectorAll: () => [leave, stay] };
        if (api.exitStayRef) api.exitStayRef.current = stay;
      }
      pendingEffects.splice(0).forEach((run) => run());
    }
  }
  render();
  return {
    get api() { return api; }, get starts() { return starts; },
    rooms, ends, requests, writes, document, trigger, leave, stay, audioElements,
    async flush() { await new Promise(setImmediate); render(); },
    fire(type, event = {}) { [...(listeners.get(type) ?? [])].forEach((handler) => handler(event)); },
    unmount() { mounted = false; slots.forEach((slot) => slot.cleanup?.()); },
  };
}

for (const action of ['unmount', 'pagehide']) {
  const cancel = (app) => action === 'unmount' ? app.unmount() : app.fire('pagehide');
  test(`${action} before allocation rolls back the late session without opening LiveKit`, async () => {
    const allocation = deferred(), app = setup({ allocation });
    const startup = app.api.handleStartSession();
    await app.flush();
    cancel(app);
    allocation.resolve({ session_id: 'late-session', livekit_token: 'mock-token', livekit_url: 'mock-url' });
    await startup;
    assert.equal(app.rooms.length, 0);
    assert.deepEqual(app.ends, ['late-session']);
    assert.equal(app.requests.length, 0);
    assert.equal(app.writes.some(({ value }) => value === 'connected' || value === 'error'), false);
    app.unmount();
  });

  for (const stage of ['connection', 'microphone']) {
    test(`${action} during ${stage} ends the allocation and leaves no room/microphone`, async () => {
      const gate = deferred(), app = setup({ [stage]: gate });
      const startup = app.api.handleStartSession();
      await app.flush();
      const room = app.rooms[0];
      assert.equal(room.micCalls, stage === 'microphone' ? 1 : 0);
      cancel(app);
      assert.equal(room.connected, false);
      assert.equal(app.ends.length + app.requests.length, 1, 'end immediately, even if the pending step never settles');
      gate.resolve();
      await startup;
      assert.equal(room.connected, false);
      assert.equal(room.micActive, false);
      assert.equal(room.micCalls, stage === 'microphone' ? 1 : 0);
      assert.equal(app.writes.some(({ value }) => value === 'error'), false);
      if (action === 'pagehide') {
        assert.match(app.requests[0].url, /\/sessions\/session-1\/end\/$/);
        assert.equal(app.requests[0].keepalive, true);
      }
      app.unmount();
      assert.equal(app.ends.length + app.requests.length, 1, 'no duplicate server end after cancellation');
    });
  }
}

for (const failure of ['apiError', 'connectError', 'micError', 'endError', 'disconnectError']) {
  test(`${failure} rolls back startup and allows a fresh attempt`, async () => {
    const options = { [failure]: new Error(failure) };
    if (failure === 'endError' || failure === 'disconnectError') options.micError = new Error('microphone failed');
    const app = setup(options);
    await app.api.handleStartSession();
    await app.flush();
    assert.equal(app.api.sessionState, 'error');
    assert.equal(app.api.sessionId, null);
    assert.ok(app.api.error);
    assert.deepEqual(app.ends, failure === 'apiError' ? [] : ['session-1']);
    app.rooms.forEach((room) => {
      assert.equal(room.connected, failure === 'disconnectError');
      assert.equal(room.micActive, false);
    });
    delete options[failure];
    delete options.micError;
    app.api.setSessionState('idle'); // The existing Retry button returns to idle.
    await app.flush();
    await app.api.handleStartSession();
    await app.flush();
    assert.equal(app.api.sessionState, 'connected');
    assert.equal(app.api.sessionId, 'session-2');
    app.unmount();
    assert.deepEqual(app.ends, failure === 'apiError' ? ['session-2'] : ['session-1', 'session-2']);
  });
}

test('disconnect rejection stops local media, clears audio/state, and retains ownership for retry', async () => {
  const options = {}, app = setup(options);
  await app.api.handleStartSession();
  await app.flush();
  const room = app.rooms[0];
  const audio = { remove() { app.audioElements.delete(this); } };
  room.handlers.get('TrackSubscribed')({ kind: 'audio', attach: () => audio });
  const speakingHandlers = new Map();
  room.handlers.get('ParticipantConnected')({
    on: (type, handler) => speakingHandlers.set(type, handler),
    removeAllListeners: (type) => speakingHandlers.delete(type),
  });
  speakingHandlers.get('IsSpeakingChanged')(true);
  app.api.lk.setSpeakerMuted(true);
  await app.flush();
  assert.equal(app.api.lk.agentSpeaking, true);
  assert.equal(app.api.lk.isSpeakerMuted, true);
  options.disconnectError = new Error('sendLeave failed');
  await assert.rejects(app.api.lk.disconnect(), /sendLeave failed/);
  await app.flush();
  assert.equal(room.connected, true, 'SDK transport remains unresolved after rejection');
  assert.equal(room.micActive, false, 'fallback must stop the microphone independently of SDK disconnect');
  assert.ok(room.trackStops > 0);
  assert.equal(app.audioElements.size, 0);
  assert.equal(speakingHandlers.size, 0);
  assert.equal(app.api.lk.connectionState, 'disconnected');
  assert.equal(app.api.lk.agentConnected, false);
  assert.equal(app.api.lk.agentSpeaking, false);
  assert.equal(app.api.lk.isMicMuted, false);
  assert.equal(app.api.lk.isSpeakerMuted, false);
  await assert.rejects(app.api.lk.connect('new-token', 'new-url'), /sendLeave failed/);
  assert.equal(app.rooms.length, 1, 'failed prior room must not be overwritten');
  assert.ok(room.disconnects >= 2, 'retry must still own the original room');
  delete options.disconnectError;
  options.disconnection = deferred();
  const retry = app.api.lk.connect('new-token', 'new-url');
  await app.flush();
  assert.equal(app.rooms.length, 1, 'wait for prior disconnect before creating a replacement');
  options.disconnection.resolve();
  await retry;
  assert.equal(room.connected, false);
  assert.equal(app.rooms.length, 2);
  app.unmount();
  await app.flush();
  assert.equal(app.rooms[1].micActive, false);
});

test('manual End completes UI after disconnect rejection and unmount retries without unhandled rejection', async () => {
  const options = {}, app = setup(options);
  await app.api.handleStartSession();
  await app.flush();
  options.disconnectError = new Error('engine.close failed');
  await app.api.handleEndSession();
  await app.flush();
  assert.equal(app.api.sessionState, 'idle');
  assert.equal(app.api.sessionId, null);
  assert.equal(app.rooms[0].micActive, false);
  assert.equal(app.rooms[0].connected, true);
  assert.deepEqual(app.ends, ['session-1']);
  app.unmount();
  await app.flush();
  assert.equal(app.rooms[0].disconnects, 2);
  assert.equal(app.rooms[0].micActive, false);
  assert.deepEqual(app.ends, ['session-1']);
});

for (const action of ['unmount', 'pagehide']) {
  for (const stage of ['connection', 'microphone']) {
    test(`${action} during ${stage} stays cancelled when SDK disconnect rejects`, async () => {
      const gate = deferred(), options = { [stage]: gate, disconnectError: new Error('disconnect failed') };
      const app = setup(options);
      const startup = app.api.handleStartSession();
      await app.flush();
      if (action === 'unmount') app.unmount(); else app.fire('pagehide');
      await app.flush();
      gate.resolve();
      await startup;
      await app.flush();
      const room = app.rooms[0];
      assert.equal(room.micCalls, stage === 'microphone' ? 1 : 0);
      assert.equal(room.micActive, false);
      assert.equal(app.ends.length + app.requests.length, 1);
      assert.equal(app.writes.some(({ value }) => value === 'error'), false);
      delete options.disconnectError;
      await app.api.lk.disconnect();
      assert.equal(room.connected, false, 'cancelled room remains owned for later cleanup');
      app.unmount();
      await app.flush();
    });
  }
}

for (const action of ['manual', 'unmount', 'pagehide']) {
  test(`successful startup preserves ${action} ending`, async () => {
    const app = setup();
    const startup = app.api.handleStartSession();
    await app.api.handleStartSession(); // Rapid double activation must allocate only once.
    await startup;
    await app.flush();
    assert.equal(app.starts, 1);
    assert.equal(app.api.sessionState, 'connected');
    assert.equal(app.rooms[0].micActive, true);
    if (action === 'manual') {
      await app.api.handleEndSession();
      await app.flush();
      assert.equal(app.api.sessionState, 'idle');
      assert.equal(app.api.sessionId, null);
    } else if (action === 'pagehide') app.fire('pagehide');
    app.unmount();
    assert.equal(app.rooms[0].connected, false);
    assert.equal(app.rooms[0].micActive, false);
    assert.equal(app.ends.length + app.requests.length, 1);
    if (action === 'pagehide') assert.equal(app.requests[0].keepalive, true);
  });
}

test('exit dialog traps Tab, closes on Escape/Stay, and restores focus across rerenders', async () => {
  assert.match(pageSource, /import useDialogFocus from ['"]\.\.\/\.\.\/features\/auth\/useDialogFocus['"]/);
  assert.match(pageSource, /ref=\{exitDialogRef\}/);
  assert.match(pageSource, /<Button ref=\{exitStayRef\}[^>]*onClick=\{closeExitModal\}/);
  const app = setup();
  await app.api.handleStartSession();
  await app.flush();
  app.fire('popstate');
  await app.flush();
  assert.equal(app.document.activeElement, app.stay);
  const onClose = app.api.closeExitModal;
  const key = (key, shiftKey = false) => {
    const event = { key, shiftKey, prevented: false, preventDefault() { this.prevented = true; } };
    app.fire('keydown', event);
    return event;
  };
  assert.equal(key('Tab').prevented, true);
  assert.equal(app.document.activeElement, app.leave);
  app.api.handleMicTap();
  await app.flush();
  assert.equal(app.api.closeExitModal, onClose);
  assert.equal(app.document.activeElement, app.leave, 'unrelated renders must not reset dialog focus');
  assert.equal(key('Tab', true).prevented, true);
  assert.equal(app.document.activeElement, app.stay);
  assert.equal(key('Escape').prevented, true);
  await app.flush();
  assert.equal(app.api.showExitModal, false);
  assert.equal(app.document.activeElement, app.trigger);
  app.fire('popstate');
  await app.flush();
  app.api.closeExitModal();
  await app.flush();
  assert.equal(app.document.activeElement, app.trigger);
  app.unmount();
});
