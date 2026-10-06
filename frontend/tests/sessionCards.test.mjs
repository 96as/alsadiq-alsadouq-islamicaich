// hk-14: the session source-card reducer (history vs visible vs pinned). Run: npm run test:session
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { EMPTY_SESSION, HISTORY_CAP, MAX_VISIBLE, sessionCardsReducer as r } from '../src/features/child/sources/sessionCards.js';

const add = (state, id) => r(state, { type: 'add', card: { id: String(id), arabic_text: `t${id}` } });
const ids = (state) => state.visible;

test('MAX_VISIBLE matches MAX_SOURCE_CARDS', () => {
  const src = readFileSync(new URL('../src/features/child/sources/useSourceCards.js', import.meta.url), 'utf8');
  assert.equal(Number(/MAX_SOURCE_CARDS = (\d+)/.exec(src)[1]), MAX_VISIBLE);
});

test('visible keeps the newest 3, history keeps them all, de-duplicated', () => {
  let s = EMPTY_SESSION;
  for (const i of [1, 2, 3, 4]) s = add(s, i);
  assert.deepEqual(ids(s), ['4', '3', '2']);
  assert.deepEqual(s.history.map((c) => c.id), ['4', '3', '2', '1']);
  s = add(s, 2); // re-sent: back to the front, no duplicate
  assert.deepEqual(ids(s), ['2', '4', '3']);
  assert.equal(s.history.length, 4);
});

test('dismiss closes one card but keeps it in history; a re-sent id shows again', () => {
  let s = add(add(EMPTY_SESSION, 1), 2);
  s = r(s, { type: 'dismiss', id: '2' });
  assert.deepEqual(ids(s), ['1']);
  assert.equal(s.history.length, 2);
  s = add(s, 2);
  assert.deepEqual(ids(s), ['2', '1']);
});

test('reopen shows every history card, pinned; new cards do not push pinned ones out; clear resets', () => {
  let s = EMPTY_SESSION;
  for (const i of [1, 2, 3, 4, 5]) s = add(s, i);
  s = r(s, { type: 'reopen' });
  assert.deepEqual(ids(s), ['5', '4', '3', '2', '1']);
  assert.deepEqual([...s.pinned].sort(), ['1', '2', '3', '4', '5']);
  s = add(s, 6);
  assert.deepEqual(ids(s), ['6', '5', '4', '3', '2', '1']);
  assert.ok(!s.pinned.includes('6')); // the new card still auto-dismisses
  s = add(s, 3); // a re-sent pinned card is fresh again
  assert.ok(!s.pinned.includes('3'));
  assert.deepEqual(r(s, { type: 'clear' }), EMPTY_SESSION);
});

test('history is capped and visible never points outside it', () => {
  let s = EMPTY_SESSION;
  for (let i = 1; i <= HISTORY_CAP + 5; i++) s = add(s, i);
  assert.equal(s.history.length, HISTORY_CAP);
  s = r(s, { type: 'reopen' });
  s = add(s, 99);
  assert.ok(s.visible.every((id) => s.history.some((c) => c.id === id)));
});
