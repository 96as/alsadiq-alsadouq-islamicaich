import { useRef, useLayoutEffect } from 'react';
import ChatBubble from './ChatBubble';
import { stringsFor } from '../../../i18n'; // i18n

const ChatMessageList = ({ messages, lang, empty = null, emptyText }) => {
  const chat = stringsFor(lang).chat;
  const scrollRef = useRef(null);

  // Scroll the list container only. scrollIntoView on a sentinel can scroll the
  // visual viewport / ancestors on mobile Safari and leave a gap under the bottom nav.
  useLayoutEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [messages]);

  if (messages.length === 0) {
    if (empty) return empty;
    return (
      <section className="flex min-h-0 flex-1 items-center justify-center overflow-hidden px-4">
        <p className="text-body text-center text-text-muted">
          {emptyText ?? chat.emptyHint}
        </p>
      </section>
    );
  }

  return (
    <section
      ref={scrollRef}
      aria-label={chat.messagesLabel}
      className="flex min-h-0 flex-1 flex-col overflow-y-auto overscroll-contain [overflow-anchor:none] px-4 pt-4 pb-2"
    >
      {messages.map((msg, i) => (
        <ChatBubble
          key={msg.streamId ?? `${msg.timestamp}-${i}`}
          sender={msg.sender}
          content={msg.content}
          timestamp={msg.timestamp}
          streaming={msg.streaming}
          lang={lang}
        />
      ))}
    </section>
  );
};

export default ChatMessageList;
