// A stand-in for src/hooks/useLiveKitRoom.js for the browser click-test (scripts/meadow-click-test.py), which serves it
// in place of the real module so the connected call screen can be driven without a LiveKit server. Synthetic only:
// no audio, no network. The agent "speaks" on a timer so the call screen can be seen in both states.
import { useCallback, useEffect, useRef, useState } from 'react';

export default function useLiveKitRoom() {
  const [connectionState, setConnectionState] = useState('disconnected');
  const [isMicMuted, setMicMuted] = useState(false);
  const [isSpeakerMuted, setSpeakerMutedState] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [agentSpeaking, setAgentSpeaking] = useState(false);
  const levelRef = useRef(0);

  useEffect(() => {
    if (connectionState !== 'connected') return undefined;
    const id = setInterval(() => setAgentSpeaking((v) => !v), 2500);
    return () => clearInterval(id);
  }, [connectionState]);

  useEffect(() => {
    levelRef.current = agentSpeaking ? 0.5 : 0;
  }, [agentSpeaking]);

  const connect = useCallback(async () => {
    setConnectionState('connecting');
    await new Promise((r) => setTimeout(r, 900));
    setConnectionState('connected');
  }, []);
  const disconnect = useCallback(async () => {
    setConnectionState('disconnected');
    setAgentSpeaking(false);
  }, []);
  const toggleMic = useCallback(() => setMicMuted((v) => !v), []);
  const setMicEnabled = useCallback((on) => setMicMuted(!on), []);
  const toggleSpeaker = useCallback(() => setSpeakerMutedState((v) => !v), []);
  const setSpeakerMuted = useCallback((v) => setSpeakerMutedState(Boolean(v)), []);
  // Same shape and promise as the real hook (ConversationPage calls sendTextMessage(text).catch(...)).
  const sendTextMessage = useCallback(async (text) => {
    setChatMessages((m) => [...m, { sender: 'child', content: text, timestamp: Date.now() }]);
  }, []);
  const getAgentAudioLevel = useCallback(() => levelRef.current, []);
  const getAgentLipsync = useCallback(() => null, []);
  const getAvatarContext = useCallback(() => null, []);
  const setAvatarLang = useCallback(() => {}, []);
  const onGamificationEvent = useCallback(() => {}, []);
  const onReference = useCallback(() => {}, []);

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
    agentConnected: connectionState === 'connected',
    agentSpeaking,
    agentState: agentSpeaking ? 'speaking' : 'listening',
    voiceError: null,
    sessionLimit: null,
    getAgentAudioLevel,
    getAgentLipsync,
    getAvatarContext,
    setAvatarLang,
    onGamificationEvent,
    onReference,
  };
}
