import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowUpRight, Hand, MoonStar, Sprout, Sun, TreePine, UserRound } from 'lucide-react';
import { assetUrl } from '../utils/assetUrl';
import '../features/demo/demo.css';
import './showcase.css';

/**
 * Index of the showcase build (VITE_SHOWCASE=1, served under /page/). A bilingual
 * card list that links to the preview pages. Nothing here talks to a server.
 * kind 'app' is a route inside this app; 'file' is a separate HTML entry in the build.
 */
const CARDS = [
  {
    id: 'meadow',
    icon: Sun,
    tag: { en: "The product's current look", ar: 'الشكل الحالي للمنتج' },
    en: { title: 'Meadow, current background', body: "The animated Al-Sadiq on the meadow background the child screen uses today. Switch idle, listening, thinking and speaking, then try wave, look around and blink." },
    ar: { title: 'المرج — الخلفية الحالية', body: 'الصديق المتحرّك على خلفية المرج التي تستخدمها شاشة الطفل اليوم. بدّل بين الهدوء والإصغاء والتفكير والكلام، وجرّب التلويح والنظر حوله والرمشة.' },
    open: { kind: 'app', to: '/meadow' },
    chips: [
      { en: 'Idle', ar: 'هادئ', kind: 'app', to: '/meadow?state=idle' },
      { en: 'Listening', ar: 'يصغي', kind: 'app', to: '/meadow?state=listening' },
      { en: 'Thinking', ar: 'يفكّر', kind: 'app', to: '/meadow?state=thinking' },
      { en: 'Speaking', ar: 'يتكلم', kind: 'app', to: '/meadow?state=speaking' },
    ],
  },
  {
    id: 'forest',
    icon: TreePine,
    tag: { en: 'Experiment, to discuss later', ar: 'تجربة للنقاش لاحقًا' },
    en: { title: 'Experiment: 3D forest (to discuss)', body: 'An experiment, not the current look: the 3D forest with the avatar walking in, waving and talking. Switch the time of day, press Speak, replay the walk.' },
    ar: { title: 'تجربة: الغابة ثلاثية الأبعاد (للنقاش)', body: 'تجربة وليست الشكل الحالي: الغابة ثلاثية الأبعاد والصديق يمشي ويلوّح ويتحدث. بدّل الوقت من اليوم واضغط تحدّث وأعد المشي.' },
    open: { kind: 'app', to: '/dev/forest' },
    chips: [
      { en: 'Morning', ar: 'الصباح', kind: 'app', to: '/dev/forest?t=morning' },
      { en: 'Noon', ar: 'الظهر', kind: 'app', to: '/dev/forest?t=noon' },
      { en: 'Maghrib', ar: 'المغرب', kind: 'app', to: '/dev/forest?t=maghrib' },
      { en: 'Night', ar: 'الليل', kind: 'app', to: '/dev/forest?t=night' },
      { en: 'In conversation', ar: 'في الحديث', kind: 'app', to: '/dev/forest?phase=talk' },
    ],
  },
  {
    id: 'landing',
    icon: Sprout,
    en: { title: 'Landing page', body: 'The public landing: the live forest, the walk-in, bubbles on tap, Arabic and English. The demo button needs the live server.' },
    ar: { title: 'صفحة الهبوط', body: 'صفحة البداية العامة: الغابة الحيّة والمشي والفقاعات عند اللمس بالعربية والإنجليزية. زر التجربة يحتاج الخادم المباشر.' },
    open: { kind: 'app', to: '/landing' },
    chips: [],
  },
  {
    id: 'avatar-states',
    icon: UserRound,
    en: { title: 'Avatar states', body: 'The avatar alone, switching between idle, listening, thinking and speaking, with a walk-in replay.' },
    ar: { title: 'حالات الصديق', body: 'الصديق وحده وهو ينتقل بين الهدوء والإصغاء والتفكير والكلام، مع إعادة المشي.' },
    open: { kind: 'file', to: '/avatar-component-preview.html' },
    chips: [
      { en: 'Idle', ar: 'هادئ', kind: 'file', to: '/avatar-component-preview.html?state=idle' },
      { en: 'Listening', ar: 'يصغي', kind: 'file', to: '/avatar-component-preview.html?state=listening' },
      { en: 'Thinking', ar: 'يفكّر', kind: 'file', to: '/avatar-component-preview.html?state=thinking' },
      { en: 'Speaking', ar: 'يتكلم', kind: 'file', to: '/avatar-component-preview.html?state=speaking' },
      { en: 'Walk-in', ar: 'المشي', kind: 'file', to: '/avatar-component-preview.html?walk=1' },
    ],
  },
  {
    id: 'avatar-views',
    icon: Hand,
    en: { title: 'Model views', body: 'The raw avatar model from three camera angles, the way it is lit in the app.' },
    ar: { title: 'زوايا النموذج', body: 'نموذج الصديق من ثلاث زوايا للكاميرا، بالإضاءة نفسها في التطبيق.' },
    open: { kind: 'file', to: '/avatar-preview.html' },
    chips: [
      { en: 'Front', ar: 'أمامي', kind: 'file', to: '/avatar-preview.html?view=front' },
      { en: 'Three quarter', ar: 'ثلاثة أرباع', kind: 'file', to: '/avatar-preview.html?view=three' },
      { en: 'Face', ar: 'الوجه', kind: 'file', to: '/avatar-preview.html?view=face' },
    ],
  },
];

function Go({ target, className, children, ...rest }) {
  if (target.kind === 'app') {
    return <Link to={target.to} className={className} {...rest}>{children}</Link>;
  }
  return <a href={assetUrl(target.to)} className={className} {...rest}>{children}</a>;
}

export default function ShowcaseIndex() {
  useEffect(() => {
    const prev = document.title;
    document.title = 'Al-Sadiq Showcase';
    return () => { document.title = prev; };
  }, []);

  return (
    <div className="demo-landing showcase fixed inset-0 overflow-y-auto overflow-x-hidden" lang="en">
      <div className="mx-auto flex min-h-full w-full max-w-[1120px] flex-col px-4 pb-10 sm:px-8">
        <header className="showcase-hero flex flex-col gap-4 pb-6 pt-8 sm:pt-12">
          <div className="flex items-center gap-3">
            <span
              className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl text-white"
              style={{ background: 'linear-gradient(145deg, #1d6b3c, #0f2d1c)', boxShadow: '0 6px 14px -6px rgba(15,45,28,.7)' }}
              aria-hidden="true"
            >
              <MoonStar className="h-6 w-6" strokeWidth={1.75} />
            </span>
            <p className="text-sm font-bold uppercase tracking-[0.14em] text-[color:var(--d-leaf)]">
              Islamic AI Challenge · Preview
            </p>
          </div>
          <div className="grid gap-x-12 gap-y-6 md:grid-cols-2">
            <div className="flex flex-col gap-4">
              <h1 className="text-[clamp(2.2rem,5vw,3.8rem)] font-extrabold leading-[1.1]" style={{ textWrap: 'balance' }}>
                Al-Sadiq Showcase
              </h1>
              <p className="max-w-[34rem] text-lg leading-8 text-[color:var(--d-ink-soft)]">
                The animated Al-Sadiq, ready to open: on the meadow background the product uses today, the speaking states, the landing page, and the 3D forest experiment.
                Preview only, with no server behind it.
              </p>
            </div>
            <div lang="ar" dir="rtl" className="flex flex-col gap-4">
              <h2 className="text-[clamp(2rem,4.6vw,3.4rem)] font-extrabold leading-[1.2] text-[color:var(--d-leaf-2)]" style={{ textWrap: 'balance' }}>
                معاينة الصديق الصدوق
              </h2>
              <p className="max-w-[34rem] text-lg leading-8 text-[color:var(--d-ink-soft)]">
                الصديق المتحرّك جاهز للفتح: على خلفية المرج التي يستخدمها المنتج اليوم، وحالات الكلام، وصفحة البداية، وتجربة الغابة ثلاثية الأبعاد. للمعاينة فقط ولا يوجد خادم خلفها.
              </p>
            </div>
          </div>
        </header>

        <main>
          <ul className="grid gap-5 md:grid-cols-2">
            {CARDS.map((card, i) => {
              const Icon = card.icon;
              return (
                <li key={card.id} className="showcase-card" style={{ '--i': i }} data-card={card.id}>
                  <div className="flex items-start justify-between gap-3">
                    <span className="showcase-icon" aria-hidden="true">
                      <Icon className="h-7 w-7" strokeWidth={1.75} />
                    </span>
                    <Go target={card.open} className="showcase-open" data-open={card.id}>
                      <span>Open</span>
                      <span lang="ar" dir="rtl">افتح</span>
                      <ArrowUpRight className="h-4 w-4" strokeWidth={2.25} aria-hidden="true" />
                    </Go>
                  </div>
                  {card.tag ? (
                    <p className="mt-4 inline-flex flex-wrap items-center gap-x-2 rounded-full bg-[color:var(--d-leaf)]/10 px-3 py-1 text-xs font-bold uppercase tracking-wide text-[color:var(--d-leaf)]" data-tag={card.id}>
                      <span>{card.tag.en}</span>
                      <span lang="ar" dir="rtl" className="normal-case">{card.tag.ar}</span>
                    </p>
                  ) : null}
                  <h2 className="mt-3 text-2xl font-extrabold leading-tight">
                    {card.en.title}
                    <span lang="ar" dir="rtl" className="mt-0.5 block text-[0.9em] text-[color:var(--d-leaf-2)]">{card.ar.title}</span>
                  </h2>
                  <p className="mt-3 leading-7 text-[color:var(--d-ink-soft)]">{card.en.body}</p>
                  <p lang="ar" dir="rtl" className="mt-1 leading-7 text-[color:var(--d-ink-soft)]">{card.ar.body}</p>
                  {card.chips.length ? (
                    <div className="mt-5 flex flex-wrap gap-2">
                      {card.chips.map((chip) => (
                        <Go key={chip.to} target={chip} className="showcase-chip">
                          <span>{chip.en}</span>
                          <span lang="ar" dir="rtl" className="showcase-chip-ar">{chip.ar}</span>
                        </Go>
                      ))}
                    </div>
                  ) : null}
                </li>
              );
            })}
          </ul>
        </main>

        <footer className="pt-8">
          <p className="text-sm text-[color:var(--d-ink-soft)]">
            Team preview, sign-in required. The real demo lives on the live server.
          </p>
        </footer>
      </div>
    </div>
  );
}
