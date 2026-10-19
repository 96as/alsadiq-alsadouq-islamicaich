"""
Notes Section for the file:
- Speak first, record points after (task 08, "fewer LLM rounds"). No livekit import here.

- The problem. The model used to call record_engagement BEFORE its words, or after them. In
  livekit-agents any tool call makes the framework run a SECOND LLM round with the tool result
  (about 1 to 1.5 s more, and often an extra sentence the child did not need). A points change
  does not need the model to say anything more.

- The fix has two halves.
  1. The prompt (agent_class._GAMIFICATION_DIRECTIVES) tells the model to say its reply first
     and call record_engagement after the words, in the same turn.
  2. This module: when the ONLY tool calls of a turn are record_engagement, and the child has
     already heard (or read) the reply in this turn, and the points did not cause a level up,
     the follow-up round is cancelled with event.cancel_tool_reply(). The tool still runs; the
     app still shows the points live. Nothing more is generated.

- What is never cancelled (the second round runs as before):
    * any other tool (flag_safety_concern, get_islamic_reference, complete_conversation_quest,
      list_my_quests): the model may need to say something about their result;
    * a tool call made BEFORE any words (the model must still answer the child);
    * a level up (the tool result asks the model to celebrate in words).
  A mixed turn (record_engagement together with another tool) is never cancelled either.

- "The reply was heard" means: the agent state went to "speaking" in this turn, or an assistant
  message with text was added in this turn. A turn starts when a child message is added to
  the chat (livekit adds it just before the reply starts thinking), or when the agent state
  goes to "thinking" from "listening" or "idle" (the move to "thinking" from "speaking" is the
  pause while tools run and does not start a new turn). The child-message rule covers a turn
  that starts while the agent is still "speaking" (the first seconds of the greeting, when
  livekit's echo warm-up turns interruptions off), so the greeting's words never count as the
  answer to the child's first line. Starting a new turn too often only keeps the old second
  round, which is the safe side.

- This is safe if the livekit event shape changes: every handler swallows its own errors and a
  missing cancel_tool_reply simply leaves the old behaviour (a second round).
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# Tools whose result never needs a spoken follow-up by itself.
SILENT_TOOLS = frozenset({"record_engagement"})


class SpeakFirstGate:
    def __init__(self, *, level_up_note: str) -> None:
        self._level_up_note = level_up_note
        self._heard_reply = False
        self.cancelled_rounds = 0

    def attach(self, session) -> None:
        session.on("agent_state_changed", self.on_agent_state_changed)
        session.on("conversation_item_added", self.on_conversation_item_added)
        session.on("function_tools_executed", self.on_function_tools_executed)

    def on_agent_state_changed(self, event) -> None:
        try:
            new_state = getattr(event, "new_state", None)
            old_state = getattr(event, "old_state", None)
            if new_state == "thinking" and old_state in ("listening", "idle", None):
                self._heard_reply = False
            elif new_state == "speaking":
                self._heard_reply = True
        except Exception:
            logger.debug("speak first: agent_state_changed failed", exc_info=True)

    def on_conversation_item_added(self, event) -> None:
        try:
            item = getattr(event, "item", None)
            role = getattr(item, "role", None)
            if role == "user":
                self._heard_reply = False  # a new turn: nothing of it has been heard yet
                return
            if role != "assistant":
                return
            text = getattr(item, "text_content", None)
            if text is None:
                content = getattr(item, "content", None)
                text = " ".join(c for c in (content or []) if isinstance(c, str))
            if (text or "").strip():
                self._heard_reply = True
        except Exception:
            logger.debug("speak first: conversation_item_added failed", exc_info=True)

    def on_function_tools_executed(self, event) -> None:
        try:
            calls = list(getattr(event, "function_calls", []) or [])
            if not calls:
                return
            names = {getattr(call, "name", None) for call in calls}
            if not names <= SILENT_TOOLS:
                return
            if not self._heard_reply:
                return
            for output in getattr(event, "function_call_outputs", []) or []:
                text = str(getattr(output, "output", "") or "")
                if self._level_up_note and self._level_up_note in text:
                    return
            event.cancel_tool_reply()
            self.cancelled_rounds += 1
        except Exception:
            logger.debug("speak first: function_tools_executed failed", exc_info=True)


def attach_speak_first(session, *, level_up_note: str) -> SpeakFirstGate:
    gate = SpeakFirstGate(level_up_note=level_up_note)
    gate.attach(session)
    return gate


__all__ = ["SILENT_TOOLS", "SpeakFirstGate", "attach_speak_first"]
