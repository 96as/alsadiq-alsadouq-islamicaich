import { useState, useRef, useCallback, useEffect } from 'react';
import {
    createLocalAudioTrack,
    Room,
    RoomEvent,
    ParticipantEvent,
    Track,
    ConnectionState,
} from 'livekit-client';
import { createVisemeDriver } from '../features/child/components/avatar/lipsync/visemeDriver.js';
import { TimelineSync } from '../features/child/components/avatar/lipsync/timelineSync.js';

const AUDIO_CAPTURE = { echoCancellation: true, noiseSuppression: true, autoGainControl: true };

// Text timings of the reply for the lip-sync (data topic lk.lipsync, sent by the agent when its
// LIPSYNC_TIMELINE is on). VITE_LIPSYNC_TIMELINE=0 ignores them: the mouth follows the audio only.
const LIPSYNC_TOPIC = 'lk.lipsync';
const LIPSYNC_TIMELINE_ON = import.meta.env?.VITE_LIPSYNC_TIMELINE !== '0';
// 06-avatar-context: the avatar's session signals (al.* attributes, transcript cues, events).
import { createAvatarContextStore } from '../features/child/components/avatar/context/avatarSignals.js';

/** Final flag is merged on stream trailer; only valid after readAll() completes. */
function isTranscriptionFinal(attrs) {
    if (!attrs) return false;
    const v = attrs['lk.transcription_final'];
    return v === true || v === 'true';
}

function resolveTranscriptionSender(room, attrs) {
    const trackId = attrs?.['lk.transcribed_track_id'];
    if (trackId) {
        const micPub = room.localParticipant.getTrackPublication(
            Track.Source.Microphone,
        );
        if (micPub?.trackSid === trackId) return 'child';
    }
    return 'agent';
}

// Data messages the agent publishes (docs/hackathon/demo-guards.md).
const VOICE_ERROR_TOPIC = 'voice_error';
const SESSION_LIMIT_TOPIC = 'session_limit';

function parseData(payload) {
    try {
        const data = JSON.parse(new TextDecoder().decode(payload));
        return data && typeof data === 'object' ? data : null;
    } catch {
        return null;
    }
}

const AGENT_STATE_ATTR = 'lk.agent.state';
const AGENT_STATES = new Set(['initializing', 'listening', 'thinking', 'speaking', 'idle']);

/** LiveKit agents 1.x publish listening, thinking or speaking on this participant attribute. */
function readAgentState(participant) {
    const value = participant?.attributes?.[AGENT_STATE_ATTR];
    return AGENT_STATES.has(value) ? value : 'initializing';
}

/**
 * @param {{lang?: 'ar'|'en'}} [options] lang picks the lip-sync vowel model: 'ar' (the default, the
 *   app's voice is Arabic) or 'en'.
 */
export default function useLiveKitRoom({ lang = 'ar' } = {}) {
    const langRef = useRef(lang);
    langRef.current = lang;
    const roomRef = useRef(null);
    const disconnectingRoomRef = useRef(null);
    const audioElRef = useRef(null);

    const [connectionState, setConnectionState] = useState('disconnected');
    const [isMicMuted, setIsMicMuted] = useState(false);
    const [isSpeakerMuted, setIsSpeakerMuted] = useState(false);
    const [chatMessages, setChatMessages] = useState([]);
    const [agentConnected, setAgentConnected] = useState(false);
    const [agentSpeaking, setAgentSpeaking] = useState(false);
    // 'initializing' until the agent publishes lk.agent.state; the avatar then falls back to agentSpeaking.
    const [agentState, setAgentState] = useState('initializing');
    // {code, provider} once the agent says the voice cannot be used (topic voice_error).
    const [voiceError, setVoiceError] = useState(null);
    // The session clock from the agent (topic session_limit):
    // {phase: 'ending', secondsLeft, at} 20 s before the end, {phase: 'ended', at} at the end.
    const [sessionLimit, setSessionLimit] = useState(null);
    // Web Audio analyser on the agent's voice track. It only reads the stream (it is never
    // connected to the speakers), so playback and the speaker mute are unaffected.
    const analyserRef = useRef(null);
    // Text timeline of the reply being spoken, shared with the lip-sync driver (null: switched off).
    const lipsyncTimelineRef = useRef(null);
    if (LIPSYNC_TIMELINE_ON && !lipsyncTimelineRef.current) lipsyncTimelineRef.current = new TimelineSync();
    useEffect(() => {
        // The timeline ends with the speech: tell it when the agent leaves "speaking".
        if (agentState !== 'initializing') {
            lipsyncTimelineRef.current?.agentState(agentState === 'speaking', performance.now());
        }
    }, [agentState]);
    // Subscribers for realtime gamification events pushed by the agent
    // (points/quest/level) over the LiveKit data channel.
    const gamificationHandlersRef = useRef(new Set());
    // Subscribers for source cards (verse/hadith) pushed on the `reference` topic.
    const referenceHandlersRef = useRef(new Set());
    const agentParticipantRef = useRef(null);
    // 06-avatar-context: read by the avatar every frame through the stable getter below, so the
    // signals never cause a React render.
    const [avatarStore] = useState(() => createAvatarContextStore());
    const getAvatarContext = avatarStore.getContext;

    const onReference = useCallback((handler) => {
        referenceHandlersRef.current.add(handler);
        return () => referenceHandlersRef.current.delete(handler);
    }, []);

    const onGamificationEvent = useCallback((handler) => {
        gamificationHandlersRef.current.add(handler);
        return () => gamificationHandlersRef.current.delete(handler);
    }, []);

    const closeAnalyser = useCallback(() => {
        const a = analyserRef.current;
        analyserRef.current = null;
        if (a) {
            try {
                a.lipsync?.dispose();
                a.source.disconnect();
                a.ctx.close();
            } catch {
                // Already closed.
            }
        }
    }, []);

    const openAnalyser = useCallback((track) => {
        closeAnalyser();
        const AudioContextCtor = window.AudioContext || window.webkitAudioContext;
        if (!AudioContextCtor || !track.mediaStream) return;
        try {
            const ctx = new AudioContextCtor();
            const source = ctx.createMediaStreamSource(track.mediaStream);
            const analyser = ctx.createAnalyser();
            analyser.fftSize = 1024;
            analyser.smoothingTimeConstant = 0;
            source.connect(analyser);
            ctx.resume().catch(() => {});
            // Lip-sync shares this context and source (its own listen-only analyser). It also
            // resumes the context on the next tap, which Safari and iOS require.
            const lipsync = createVisemeDriver({
                context: ctx,
                input: source,
                lang: langRef.current,
                timeline: lipsyncTimelineRef.current,
            });
            analyserRef.current = {
                track,
                ctx,
                source,
                analyser,
                lipsync,
                buf: new Float32Array(analyser.fftSize),
            };
        } catch {
            // No analyser: the avatar falls back to a synthetic jaw while speaking.
            analyserRef.current = null;
        }
    }, [closeAnalyser]);

    /**
     * Current RMS level (0 to about 0.5) of the agent's voice, or -1 when no analyser is
     * available. Called every frame by the avatar; it allocates nothing.
     */
    const getAgentAudioLevel = useCallback(() => {
        const a = analyserRef.current;
        if (!a || a.ctx.state !== 'running') return -1;
        a.analyser.getFloatTimeDomainData(a.buf);
        let sum = 0;
        for (let i = 0; i < a.buf.length; i++) sum += a.buf[i] * a.buf[i];
        return Math.sqrt(sum / a.buf.length);
    }, []);

    /**
     * Live viseme state of the agent's voice for the avatar's lip-sync (14 weights, see
     * features/child/components/avatar/lipsync), or null when unavailable. Allocation free.
     */
    const getAgentLipsync = useCallback(() => analyserRef.current?.lipsync?.read() ?? null, []);

    const handleTrackSubscribed = useCallback((track) => {
        if (track.kind === Track.Kind.Audio) {
            const el = track.attach();
            el.autoplay = true;
            audioElRef.current = el;
            document.body.appendChild(el);
            // The agent's voice is published as a microphone track; background audio
            // (livekit-agents BackgroundAudioPlayer) is not, and must not move the jaw.
            if (track.source === Track.Source.Microphone) openAnalyser(track);
        }
    }, [openAnalyser]);

    const handleTrackUnsubscribed = useCallback((track) => {
        if (analyserRef.current?.track === track) closeAnalyser();
        track.detach().forEach((el) => el.remove());
        if (audioElRef.current && !document.body.contains(audioElRef.current)) {
            audioElRef.current = null;
        }
    }, [closeAnalyser]);

    const disconnect = useCallback(async (room = roomRef.current) => {
        if (room) {
            if (roomRef.current === room) disconnectingRoomRef.current = room;
            room.removeAllListeners();
        }
        try {
            if (room) await room.disconnect();
            // Keep ownership on rejection so retry/unmount can finish SDK cleanup.
            if (roomRef.current === room) roomRef.current = null;
            if (disconnectingRoomRef.current === room) disconnectingRoomRef.current = null;
        } finally {
            // LiveKit can reject before handleDisconnect stops the local tracks.
            room?.localParticipant.trackPublications.forEach((publication) => {
                try { publication.track?.stop(); } catch { /* Continue cleaning other media. */ }
            });
            if (!roomRef.current || roomRef.current === room) {
                if (audioElRef.current) {
                    audioElRef.current.remove();
                    audioElRef.current = null;
                }
                agentParticipantRef.current?.removeAllListeners(ParticipantEvent.IsSpeakingChanged);
                agentParticipantRef.current = null;
                setConnectionState('disconnected');
                setAgentConnected(false);
                setAgentSpeaking(false);
                setAgentState('initializing');
                closeAnalyser();
                setIsMicMuted(false);
                setIsSpeakerMuted(false);
                setVoiceError(null);
                setSessionLimit(null);
            }
        }
    }, [closeAnalyser]);

    /**
     * Join the room. `signal` (optional AbortSignal) cancels a start that is still in flight.
     * micEnabled false is a text chat: the microphone is never opened, so the browser does
     * not ask for permission and nothing listens.
     */
    // publishMuted (hk-14b, hold-to-talk): the mic is published already muted, so no audio reaches the agent before the
    // first hold, and the permission prompt still comes at connect. setMicrophoneEnabled(true) later unmutes it.
    const connect = useCallback(async (token, url, signal, { micEnabled = true, publishMuted = false } = {}) => {
        if (signal?.aborted) return;
        if (roomRef.current) await disconnect();
        if (signal?.aborted) return;
        const room = new Room({
            adaptiveStream: true,
            dynacast: true,
            audioCaptureDefaults: AUDIO_CAPTURE,
        });
        roomRef.current = room;
        setConnectionState('connecting');
        setChatMessages([]);
        setVoiceError(null);
        setSessionLimit(null);

        room.on(RoomEvent.ConnectionStateChanged, (state) => {
            if (state === ConnectionState.Connected) setConnectionState('connected');
            else if (state === ConnectionState.Reconnecting) setConnectionState('connecting');
            else if (state === ConnectionState.Disconnected) {
                setConnectionState('disconnected');
                avatarStore.markDisconnected(); // 06-avatar-context
            }
        });

        room.on(RoomEvent.ParticipantConnected, (participant) => {
            setAgentConnected(true);
            // Subscribe to the agent's speaking state changes
            agentParticipantRef.current = participant;
            setAgentState(readAgentState(participant));
            // 06-avatar-context: the agent's al.* attributes at the moment it joined (no events).
            avatarStore.applySnapshot(participant.attributes);
            avatarStore.markConnected();
            participant.on(ParticipantEvent.IsSpeakingChanged, (speaking) => {
                setAgentSpeaking(speaking);
            });
        });
        room.on(RoomEvent.ParticipantAttributesChanged, (changed, participant) => {
            if (participant.isLocal) return;
            avatarStore.applyChanged(changed); // 06-avatar-context: only al.* keys matter
            if (!(AGENT_STATE_ATTR in changed)) return;
            setAgentState(readAgentState(participant));
        });
        room.on(RoomEvent.ParticipantDisconnected, () => {
            avatarStore.markDisconnected(); // 06-avatar-context
            if (agentParticipantRef.current) {
                agentParticipantRef.current.removeAllListeners(
                    ParticipantEvent.IsSpeakingChanged,
                );
                agentParticipantRef.current = null;
            }
            setAgentConnected(false);
            setAgentSpeaking(false);
            setAgentState('initializing');
        });
        room.on(RoomEvent.TrackSubscribed, handleTrackSubscribed);
        room.on(RoomEvent.TrackUnsubscribed, handleTrackUnsubscribed);

        room.on(RoomEvent.DataReceived, (payload, _participant, _kind, topic) => {
            // Malformed payloads are ignored rather than breaking the session UI.
            const data = parseData(payload);
            if (!data) return;
            if (topic === LIPSYNC_TOPIC) {
                // A malformed timeline is ignored: the mouth follows the audio.
                lipsyncTimelineRef.current?.push(data, performance.now());
                return;
            }
            if (topic === 'al.search') {
                // w3: the held web page's content (BEHAVIOUR-SPEC 6.8): a small JSON, kept out of the React state.
                if (payload.byteLength > 8192) return;
                avatarStore.onSearchMessage(data); // a malformed message is ignored: the panel keeps its procedural skin
                return;
            }
            if (topic === 'gamification') {
                avatarStore.onGamification(data); // 06-avatar-context: Happy / Celebrate
                gamificationHandlersRef.current.forEach((handler) => handler(data));
            } else if (topic === 'reference') {
                referenceHandlersRef.current.forEach((handler) => handler(data));
            } else if (topic === VOICE_ERROR_TOPIC) {
                setVoiceError({
                    code: typeof data.code === 'string' ? data.code : 'failed',
                    provider: typeof data.provider === 'string' ? data.provider : 'none',
                });
            } else if (topic === SESSION_LIMIT_TOPIC) {
                avatarStore.onSessionLimit(data); // 06-avatar-context: the goodbye cue
                if (data.type === 'session_ending') {
                    const left = Number(data.seconds_left);
                    setSessionLimit({
                        phase: 'ending',
                        secondsLeft: Number.isFinite(left) ? left : 20,
                        at: Date.now(),
                    });
                } else if (data.type === 'session_ended') {
                    setSessionLimit({ phase: 'ended', at: Date.now() });
                }
            }
        });

        room.registerTextStreamHandler(
            'lk.transcription',
            async (reader) => {
                const streamId = reader.info.id;
                const sender = resolveTranscriptionSender(
                    room,
                    reader.info?.attributes,
                );

                let acc = '';
                try {
                    // Stream chunks as they arrive so chat fills in while TTS plays (voice mode)
                    // or ahead of audio (chat mode with speaker muted).
                    for await (const chunk of reader) {
                        acc += chunk;
                        if (sender === 'agent') avatarStore.onAgentText(acc, { id: streamId }); // 06-avatar-context
                        setChatMessages((prev) => {
                            const i = prev.findIndex((m) => m.streamId === streamId);
                            const row = {
                                streamId,
                                sender,
                                content: acc,
                                timestamp: i === -1 ? Date.now() : prev[i].timestamp,
                                streaming: true,
                            };
                            if (i === -1) return [...prev, row];
                            const next = [...prev];
                            next[i] = { ...next[i], ...row };
                            return next;
                        });
                    }
                } catch {
                    setChatMessages((prev) => prev.filter((m) => m.streamId !== streamId));
                    return;
                }

                if (!isTranscriptionFinal(reader.info?.attributes)) {
                    setChatMessages((prev) => prev.filter((m) => m.streamId !== streamId));
                    return;
                }

                const trimmed = acc.trim();
                if (trimmed && sender === 'agent') avatarStore.onAgentText(trimmed, { id: streamId, final: true }); // 06-avatar-context
                if (!trimmed) {
                    setChatMessages((prev) => prev.filter((m) => m.streamId !== streamId));
                    return;
                }

                setChatMessages((prev) => {
                    const i = prev.findIndex((m) => m.streamId === streamId);
                    if (i === -1) {
                        return [
                            ...prev,
                            {
                                streamId,
                                sender,
                                content: trimmed,
                                timestamp: Date.now(),
                                streaming: false,
                            },
                        ];
                    }
                    const next = [...prev];
                    next[i] = {
                        ...next[i],
                        content: trimmed,
                        streaming: false,
                    };
                    return next;
                });
            },
        );

        await room.connect(url, token);
        if (signal?.aborted || roomRef.current !== room || disconnectingRoomRef.current === room) {
            await disconnect(room);
            return;
        }
        if (micEnabled) {
            if (publishMuted) {
                const track = await createLocalAudioTrack(AUDIO_CAPTURE);
                try {
                    await track.mute();
                    await room.localParticipant.publishTrack(track);
                } catch (e) {
                    track.stop(); // a failed publish must not leave the browser mic captured
                    throw e;
                }
            } else {
                await room.localParticipant.setMicrophoneEnabled(true);
            }
            if (signal?.aborted || roomRef.current !== room || disconnectingRoomRef.current === room) {
                await disconnect(room);
                return;
            }
            setIsMicMuted(publishMuted);
            // 06-avatar-context: the child's own speech, for the listening nods and the curious posture.
            room.localParticipant.on(ParticipantEvent.IsSpeakingChanged, (speaking) => {
                avatarStore.setChildSpeaking(speaking);
            });
        } else {
            setIsMicMuted(true);
        }

        if (room.remoteParticipants.size > 0) {
            setAgentConnected(true);
            // Catch the case where the agent was already in the room before we connected
            const existingAgent = [...room.remoteParticipants.values()][0];
            if (existingAgent) {
                agentParticipantRef.current = existingAgent;
                setAgentState(readAgentState(existingAgent));
                avatarStore.applySnapshot(existingAgent.attributes); // 06-avatar-context
                avatarStore.markConnected();
                existingAgent.on(ParticipantEvent.IsSpeakingChanged, (speaking) => {
                    setAgentSpeaking(speaking);
                });
            }
        }
    }, [disconnect, handleTrackSubscribed, handleTrackUnsubscribed, avatarStore]);

    const toggleMic = useCallback(async () => {
        const room = roomRef.current;
        if (!room || disconnectingRoomRef.current === room) return;
        const newMuted = !isMicMuted;
        setIsMicMuted(newMuted);
        try {
            await room.localParticipant.setMicrophoneEnabled(!newMuted);
        } catch {
            // Revert visual state if device permission or transport update fails.
            setIsMicMuted(!newMuted);
        }
    }, [isMicMuted]);

    const setMicEnabled = useCallback(async (enabled) => {
        const room = roomRef.current;
        if (!room || disconnectingRoomRef.current === room) return;
        setIsMicMuted(!enabled);
        try {
            await room.localParticipant.setMicrophoneEnabled(enabled);
        } catch {
            setIsMicMuted(enabled);
        }
    }, []);

    const setSpeakerMuted = useCallback((muted) => {
        if (audioElRef.current) {
            audioElRef.current.muted = muted;
        }
        setIsSpeakerMuted(muted);
    }, []);

    const toggleSpeaker = useCallback(() => {
        setSpeakerMuted(!isSpeakerMuted);
    }, [isSpeakerMuted, setSpeakerMuted]);

    const sendTextMessage = useCallback(async (text) => {
        const room = roomRef.current;
        if (!room) return;

        await room.localParticipant.sendText(text, { topic: 'lk.chat' });

        setChatMessages((prev) => [
            ...prev,
            { sender: 'child', content: text, timestamp: Date.now() },
        ]);
    }, []);

    useEffect(() => {
        return () => {
            disconnect().catch(() => {});
        };
    }, [disconnect]);

    return {
        connectionState,
        connect,
        disconnect,
        isMicMuted,
        toggleMic,
        setMicEnabled,
        isSpeakerMuted,
        toggleSpeaker,
        setSpeakerMuted,
        sendTextMessage,
        chatMessages,
        agentConnected,
        agentSpeaking,
        agentState,
        voiceError,
        sessionLimit,
        getAgentAudioLevel,
        getAgentLipsync,
        getAvatarContext, // 06-avatar-context
        setAvatarLang: avatarStore.setLang, // 06-avatar-context: 'ar' mirrors the hologram
        onGamificationEvent,
        onReference,
    };
}
