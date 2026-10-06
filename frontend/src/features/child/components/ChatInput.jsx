import { useEffect, useRef, useState } from 'react';
import { Send } from 'lucide-react';
import { IconButton, TextField } from '../../../components/ui';

// A typed message is capped at 500 characters in the field (the agent also trims what reaches the
// model, but still checks the whole text for safety).
export const CHAT_INPUT_MAX_LENGTH = 500;

/**
 * ChatInput, 56px text field plus send button for chat mode.
 *
 * @param {Function} onSend    - called with message text on submit
 * @param {boolean}  disabled  - disables input + send button
 */
const ChatInput = ({
  onSend, disabled = false, autoFocus = false,
  placeholder = 'Tell Al-Sadiq something...', sendLabel = 'Send message', label = 'Chat', dir,
}) => {
  const [value, setValue] = useState('');
  const inputRef = useRef(null);

  useEffect(() => {
    if (!autoFocus || disabled) return;
    const timer = window.setTimeout(() => {
      inputRef.current?.focus();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [autoFocus, disabled]);

  const handleSend = () => {
    const trimmed = value.trim();
    if (trimmed && onSend) {
      onSend(trimmed);
      setValue('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <section className="flex w-full items-center gap-2" dir={dir}>
      <div className="min-w-0 flex-1">
        <TextField
          ref={inputRef}
          id="chatInput"
          aria-label={label}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder={placeholder}
          autoComplete="off"
          maxLength={CHAT_INPUT_MAX_LENGTH}
        />
      </div>
      <IconButton
        label={sendLabel}
        variant="primary"
        onClick={handleSend}
        disabled={disabled || !value.trim()}
        icon={<Send aria-hidden="true" className="size-6" />}
      />
    </section>
  );
};

export default ChatInput;
