// hotfix-2: the Safari proof, as a source check. Safari and iOS only start sound inside the user's tap
// and forget that permission at the first await, so speak() in useShowcaseVoice.js must call el.play()
// (and resume the audio context) BEFORE any await, fetch, state update or timer. This test reads the
// source of speak() and fails if that order changes. The e2e run also checks it in a real browser.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const src = readFileSync(new URL('../src/pages/useShowcaseVoice.js', import.meta.url), 'utf8');

function speakBody() {
  const start = src.indexOf('const speak = useCallback(');
  assert.ok(start > 0, 'speak() not found');
  const end = src.indexOf('// The "Tap to turn on sound" button', start);
  assert.ok(end > start, 'end of speak() not found');
  return src.slice(start, end);
}

// Strip comments so a word in a comment cannot fool the order check.
const code = (s) => s.replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/.*$/gm, '');

test('speak() is not an async function', () => {
  assert.ok(!/const speak = useCallback\(\s*async/.test(speakBody()));
  assert.ok(!/useCallback\(\s*async\s*\(clip/.test(speakBody()));
});

test('el.play() is called before any await, fetch, state update or timer', () => {
  const body = code(speakBody());
  const play = body.indexOf('el.play()');
  assert.ok(play > 0, 'no el.play() in speak()');
  const before = body.slice(0, play);
  for (const bad of ['await ', 'fetch(', 'setTimeout', 'requestAnimationFrame', 'nextFrame', 'setBlocked(', 'setPlaying(', 'setLang(', '.then(', 'onStart']) {
    assert.ok(!before.includes(bad), `"${bad}" comes before el.play() in speak()`);
  }
});

test('the audio context is resumed in the same tick, before play(), and not awaited first', () => {
  const body = code(speakBody());
  const play = body.indexOf('el.play()');
  const resume = body.indexOf('resume()');
  assert.ok(resume > 0 && resume < play, 'resume() must be called before el.play()');
  assert.ok(!/await\s+resume\(\)/.test(body.slice(0, play)), 'resume() must not be awaited before play()');
});

test('the lip-sync and state work comes after play()', () => {
  const body = code(speakBody());
  const play = body.indexOf('el.play()');
  for (const later of ['sink.push(', 'setPlaying(', 'cb.current.onStart', 'timelineMessages(']) {
    const i = body.indexOf(later);
    assert.ok(i > play, `${later} must come after el.play()`);
  }
});

test('a refused play() is surfaced, never swallowed', () => {
  const body = code(speakBody());
  assert.ok(body.includes('setBlocked({ clip, reason'), 'a rejected play() must set `blocked`');
  assert.ok(body.includes('console.warn'), 'a rejected play() must be logged');
});

test('the first gesture unlocks the audio context', () => {
  const c = code(src);
  assert.ok(c.includes("'pointerdown'") && c.includes('unlock()'), 'no pointerdown unlock');
});
