/**
 * The small, always-loaded half of the sound feature (a few bytes). sound.js is only fetched after the
 * visitor presses the sound pill; until then `play`, `stop` and `setTime` do nothing and no AudioContext
 * exists.
 *
 *   soundBus.play(name)   a soft UI sound: 'pop' | 'hop' | 'lantern' | 'page' | 'tweet'
 *   soundBus.stop()       ends the forest sounds for good (a voice session is starting)
 *   soundBus.setTime(t)   the time of day, so the bed follows it
 */
export const soundBus = {
  play: null,
  stop: null,
  setTime: null,
};

/** Set once a voice session has begun in this tab: the forest sounds stay off afterwards. */
const KEY = 'sadiq_voice_started';

export const voiceStarted = () => {
  try {
    return window.sessionStorage.getItem(KEY) === '1';
  } catch {
    return false;
  }
};

export const markVoiceStarted = () => {
  try {
    window.sessionStorage.setItem(KEY, '1');
  } catch {
    // no storage: the bus stop below still ends the sounds for this page load
  }
  soundBus.stop?.();
};
