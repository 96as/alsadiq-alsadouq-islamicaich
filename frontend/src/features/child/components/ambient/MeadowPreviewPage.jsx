import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import VoiceMode from '../VoiceMode';

const STATES = ['initializing', 'listening', 'thinking', 'speaking'];
const fakeLevel = () => 0.04 + 0.1 * Math.abs(Math.sin(performance.now() / 110));

/**
 * Dev-only page (route /dev/meadow). The painted-meadow mode on its own: the same VoiceMode that
 * the child sees by default, full screen, with an agent-state switcher. ?panel=0 hides the panel.
 */
export default function MeadowPreviewPage() {
  const [params] = useSearchParams();
  const [state, setState] = useState(STATES.includes(params.get('s')) ? params.get('s') : 'listening');
  const showPanel = params.get('panel') !== '0';
  useEffect(() => {
    document.title = 'Meadow preview';
  }, []);
  return (
    <div className="fixed inset-0 flex flex-col bg-black">
      <VoiceMode agentSpeaking={state === 'speaking'} agentState={state} getAudioLevel={state === 'speaking' ? fakeLevel : undefined} />
      {showPanel && (
        <div className="absolute left-3 top-3 z-30 flex gap-2">
          {STATES.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setState(s)}
              className={`min-h-11 rounded-xl px-4 text-sm font-semibold ${state === s ? 'bg-white text-slate-900' : 'bg-black/45 text-white'}`}
            >
              {s}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
