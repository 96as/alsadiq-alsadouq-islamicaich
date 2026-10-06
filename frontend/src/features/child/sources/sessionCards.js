// hk-14: the session's source cards as a pure reducer (no React), so tests/sessionCards.test.mjs runs it as it is.
// `history` = every card shown this session (newest first, cap HISTORY_CAP); `visible` = ids on screen (max
// MAX_VISIBLE unless the child reopened them); `pinned` = ids that never auto-dismiss (reopened by the child).
// Cards are stored as given: this file never reads or changes their text.
export const MAX_VISIBLE = 3;
export const HISTORY_CAP = 20;

export const EMPTY_SESSION = { history: [], visible: [], pinned: [] };

export function sessionCardsReducer(state, action) {
  const { history, visible, pinned } = state;
  switch (action.type) {
    case 'add': { // a re-sent id becomes visible again, fresh (unpinned, so it auto-dismisses again)
      const card = action.card;
      const nextHistory = [card, ...history.filter((c) => c.id !== card.id)].slice(0, HISTORY_CAP);
      const nextPinned = pinned.filter((id) => id !== card.id);
      let unpinned = 0;
      const nextVisible = [card.id, ...visible.filter((id) => id !== card.id)].filter(
        (id) => nextPinned.includes(id) || ++unpinned <= MAX_VISIBLE,
      );
      return {
        history: nextHistory,
        visible: nextVisible.filter((id) => nextHistory.some((c) => c.id === id)),
        pinned: nextPinned.filter((id) => nextHistory.some((c) => c.id === id)),
      };
    }
    case 'dismiss':
      return { ...state, visible: visible.filter((id) => id !== action.id), pinned: pinned.filter((id) => id !== action.id) };
    case 'reopen': { // every history card, no auto-dismiss: the child asked for them
      const ids = history.map((c) => c.id);
      return { ...state, visible: ids, pinned: ids };
    }
    case 'clear':
      return EMPTY_SESSION;
    default:
      return state;
  }
}
