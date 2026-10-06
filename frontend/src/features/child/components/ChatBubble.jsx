import { clockTime } from '../../../i18n'; // i18n

/**
 * ChatBubble, one chat message. Child bubbles are solid strong green with
 * on-strong text; Sadiq's bubbles are warm surface-alt. Both pass AA in
 * light and dark mode.
 */
const ChatBubble = ({ sender, content, timestamp, streaming = false, lang }) => {
  const isChild = sender === 'child';
  const time = clockTime(timestamp, lang); // i18n: Arabic-Indic digits in Arabic, same clock either way

  return (
    <div className={`flex ${isChild ? 'justify-end' : 'justify-start'} mb-3`}>
      <div
        className={`max-w-[85%] rounded-3xl px-4 py-3 ${
          isChild
            ? 'rounded-ee-md bg-primary-strong text-on-strong'
            : 'rounded-es-md border border-border bg-surface-alt text-text'
        } ${streaming ? 'opacity-90' : ''}`}
      >
        <p dir="auto" className="text-body whitespace-pre-wrap break-words text-start">{content}</p>
        <p
          className={`mt-1 text-caption ${
            isChild ? 'text-end text-on-strong' : 'text-start text-text-muted'
          }`}
        >
          {time}
        </p>
      </div>
    </div>
  );
};

export default ChatBubble;
