import { Globe } from 'lucide-react';
import { useLang, useStrings } from '../../../i18n';
import { writeDemoLang } from '../../../services/demoService';
import { FOCUS_RING } from '../../../components/ui/cx';

/** Compact language switch for the parent shell: shows the OTHER language's short name; the label is in that language. */
export default function ParentLangButton() {
  const lang = useLang();
  const d = useStrings().parent.display;
  const next = lang === 'ar' ? 'en' : 'ar';
  return (
    <button
      type="button"
      lang={next}
      aria-label={`${d.switchTo} (${d.switchShort})`}
      onClick={() => writeDemoLang(next)}
      className={`inline-flex min-h-11 min-w-11 cursor-pointer items-center justify-center gap-1.5 rounded-full border border-border bg-surface px-3 text-label text-text hover:bg-surface-alt ${FOCUS_RING}`}
    >
      <Globe aria-hidden="true" className="size-4" />
      <span aria-hidden="true">{d.switchShort}</span>
    </button>
  );
}
