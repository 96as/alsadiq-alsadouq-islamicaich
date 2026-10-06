import { useState } from 'react';
import { Eye, EyeOff, Mic, Plus } from 'lucide-react';
import { Button, Card, EmptyState, IconButton, Pill, ProgressBar, TextField } from '../../components/ui';
import SourceCard from '../../features/child/sources/SourceCard';
import { buildMockReference } from '../../features/child/sources/mockReference';
import { normalizeReference } from '../../features/child/sources/useSourceCards'; // cards-spec (05)

// Placeholder payloads only (never real scripture). The verse has a fake audio_url
// so the play control renders; it will show "unavailable" if pressed.
const MOCK_VERSE = normalizeReference(buildMockReference('verse-explained')); // cards-spec (05): the real rule set
const MOCK_HADITH = normalizeReference(buildMockReference('hadith-hadeeth'));

const COLUMNS = [
  { title: 'Child light', theme: 'child', dark: false },
  { title: 'Child dark', theme: 'child', dark: true },
  { title: 'Parent light', theme: 'parent', dark: false },
  { title: 'Parent dark', theme: 'parent', dark: true },
];

const VARIANTS = ['primary', 'secondary', 'danger', 'ghost'];
const PILLS = ['success', 'info', 'warning', 'danger', 'neutral'];
const SWATCHES = [
  'bg-primary', 'bg-primary-soft', 'bg-primary-strong', 'bg-accent', 'bg-accent-soft',
  'bg-danger', 'bg-danger-soft', 'bg-danger-strong', 'bg-info', 'bg-info-soft', 'bg-celebration',
];

function Column({ title, theme, dark }) {
  const [show, setShow] = useState(false);
  const body = (
    <div data-theme={theme} className="flex flex-col gap-4 bg-bg p-4 text-text">
      <h2 className="text-title">{title}</h2>
      <p className="font-quran text-title" lang="ar" dir="rtl">
        نص قرآني تجريبي
      </p>
      <p className="text-display">Display</p>
      <p className="text-heading">Heading 19</p>
      <p className="text-body">Body 16, the quick brown fox.</p>
      <p className="text-label">Label 14</p>
      <p className="text-caption text-text-muted">Caption 12 muted</p>

      <div className="flex flex-wrap gap-1">
        {SWATCHES.map((s) => (
          <span key={s} title={s} className={`size-8 rounded-xl border border-border ${s}`} />
        ))}
      </div>

      <Card className="flex flex-col gap-3">
        <h3 className="text-heading">Buttons lg</h3>
        {VARIANTS.map((v) => (
          <Button key={v} variant={v}>{v}</Button>
        ))}
        <Button icon={<Plus aria-hidden="true" className="size-5" />}>With icon</Button>
        <Button loading>Loading</Button>
        <Button disabled>Disabled</Button>
      </Card>

      <Card className="flex flex-col items-start gap-3">
        <h3 className="text-heading">Buttons sm</h3>
        {VARIANTS.map((v) => (
          <Button key={v} variant={v} size="sm">{v}</Button>
        ))}
        <div className="flex gap-2">
          <IconButton label="Microphone" variant="primary" icon={<Mic aria-hidden="true" className="size-6" />} />
          <IconButton label="Add" icon={<Plus aria-hidden="true" className="size-6" />} />
          <IconButton label="Add ghost" variant="ghost" icon={<Plus aria-hidden="true" className="size-6" />} />
        </div>
      </Card>

      <Card padding="lg" className="flex flex-col gap-3">
        <div className="flex flex-wrap gap-2">
          {PILLS.map((v) => (
            <Pill key={v} variant={v}>{v}</Pill>
          ))}
        </div>
        <ProgressBar progress={65} label="Quest progress" />
        <TextField label="Name" placeholder="Type here" />
        <TextField
          label="Password"
          type={show ? 'text' : 'password'}
          defaultValue="secret"
          endAdornment={
            <IconButton
              label={show ? 'Hide password' : 'Show password'}
              variant="ghost"
              className="border-0"
              onClick={() => setShow((s) => !s)}
              icon={show ? <EyeOff aria-hidden="true" className="size-5" /> : <Eye aria-hidden="true" className="size-5" />}
            />
          }
        />
        <TextField label="With error" error="This field is required" defaultValue="x" />
      </Card>

      <Card>
        <EmptyState
          title="Nothing here yet"
          message="Come back after your first chat."
          action={<Button size="sm" variant="secondary">Start</Button>}
        />
      </Card>

      <h2 className="text-title">Source cards</h2>
      <SourceCard card={MOCK_VERSE} />
      <SourceCard card={MOCK_HADITH} />
    </div>
  );
  return dark ? <div data-color-mode="dark">{body}</div> : body;
}

/** DEV-only page at /dev/ui: every UI primitive in the four palettes. View with the app in light mode (an ancestor data-color-mode=dark on html would darken every column). */
export default function UiPreview() {
  return (
    <div className="h-full overflow-auto">
      <div className="grid min-w-[1200px] grid-cols-4">
        {COLUMNS.map((c) => (
          <Column key={c.title} {...c} />
        ))}
      </div>
    </div>
  );
}
