import logging
from typing import Any

from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


@sync_to_async
def _save_message(db_session, sender, content, input_type='voice'):
    from conversation.models import Message

    return Message.objects.create(
        session=db_session,
        sender=sender,
        content=content,
        input_type=input_type,
    )


async def _persist_conversation_item(
    db_session,
    agent,
    item: Any,
    seen_item_ids: set[str],
    skipped_child_contents: set[str] | None = None,
):
    """Persist a committed LiveKit chat item long enough for reporting cleanup.

    LiveKit Agents emits ``conversation_item_added`` for user and assistant
    messages. Tool and unsupported roles are ignored.
    """
    item_id = (getattr(item, "id", None) or "").strip()
    if item_id and item_id in seen_item_ids:
        logger.info(
            "Skipped duplicate conversation item: session_id=%s, item_id=%s",
            db_session.id,
            item_id,
        )
        return None

    role = getattr(item, "role", None)
    sender = {
        "user": "child",
        "assistant": "system",
    }.get(role)
    if not sender:
        logger.info(
            "Skipped unsupported conversation item: session_id=%s, role=%s",
            db_session.id,
            role,
        )
        if item_id:
            seen_item_ids.add(item_id)
        return None

    content = (getattr(item, "text_content", "") or "").strip()
    if not content:
        logger.info(
            "Skipped empty conversation item: session_id=%s, role=%s, item_id=%s",
            db_session.id,
            role,
            item_id or "(none)",
        )
        if item_id:
            seen_item_ids.add(item_id)
        return None

    if sender == "child" and skipped_child_contents is not None:
        if content in skipped_child_contents:
            skipped_child_contents.remove(content)
            if item_id:
                seen_item_ids.add(item_id)
            logger.info(
                "Skipped already persisted child text item: session_id=%s, item_id=%s",
                db_session.id,
                item_id or "(none)",
            )
            return None

    if item_id:
        seen_item_ids.add(item_id)

    saved_msg = await _save_message(db_session, sender, content, "voice")
    if sender == "child":
        agent._last_child_message_id = saved_msg.id
        logger.info(
            "Saved child transcript: session_id=%s, msg_id=%s, item_id=%s",
            db_session.id,
            saved_msg.id,
            item_id or "(none)",
        )
    else:
        logger.info(
            "Saved assistant transcript: session_id=%s, msg_id=%s, item_id=%s",
            db_session.id,
            saved_msg.id,
            item_id or "(none)",
        )
    return saved_msg
