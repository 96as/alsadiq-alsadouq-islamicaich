// w3: DEV FIXTURES for the held web page. Every one of these is made up and says so: `fixture: true` goes into the
// page model, and every domain ends in .example (a reserved name, it can never be a real site). They exist so the dev
// pages and the meadow showcase can show the page without a live agent. A live session only ever shows the text the
// search tool returned (contentFilter.js). Nothing here is scripture, and nothing here is a real result.

export const FIXTURE_NOTE = 'Dev fixtures: invented kid-safe text, .example domains. Not search results.';

const SKY_EN = {
  q: 'why is the sky blue',
  lang: 'en',
  r: [
    {
      t: 'Why the sky looks blue',
      d: 'skyschool.example',
      s: 'Sunlight is made of many colours. The air bounces blue light around the most, so we see blue.',
    },
    {
      t: 'Sunsets and the colour red',
      d: 'kidscience.example',
      s: 'When the sun is low its light travels a long way, and the blue is bounced out of the way.',
    },
    {
      t: 'Light, colours and rainbows',
      d: 'colourlab.example',
      s: 'Raindrops split white light into a rainbow. Try it yourself with a glass of water and a torch.',
    },
    {
      t: 'Ten sky facts for curious kids',
      d: 'factfun.example',
      s: 'Clouds are tiny drops of water floating in the air. A small cloud can still weigh a lot.',
    },
    {
      t: 'Make your own cloud in a jar',
      d: 'homelab.example',
      s: 'Warm water, ice and a little spray make a small cloud. Ask a grown-up to help you.',
    },
  ],
  hl: 0,
};

const SKY_AR = {
  q: 'لماذا السماء زرقاء',
  lang: 'ar',
  r: [
    {
      t: 'لماذا تبدو السماء زرقاء',
      d: 'skyschool.example',
      s: 'ضوء الشمس فيه ألوان كثيرة. والهواء يشتت اللون الأزرق أكثر من غيره فنراه أزرق.',
    },
    {
      t: 'الغروب واللون الأحمر',
      d: 'kidscience.example',
      s: 'عندما تكون الشمس منخفضة يقطع ضوءها طريقا أطول فيضيع الأزرق ويبقى الأحمر.',
    },
    {
      t: 'الضوء والألوان وقوس المطر',
      d: 'colourlab.example',
      s: 'قطرات المطر تفرق الضوء الأبيض إلى ألوان. جرب ذلك بكأس ماء ومصباح صغير.',
    },
    {
      t: 'عشر حقائق عن السماء للأطفال',
      d: 'factfun.example',
      s: 'السحاب قطرات ماء صغيرة تطفو في الهواء. والسحابة الصغيرة قد تكون ثقيلة جدا.',
    },
    {
      t: 'اصنع سحابتك في برطمان',
      d: 'homelab.example',
      s: 'ماء دافئ وثلج وقليل من الرذاذ يصنعون سحابة صغيرة. اطلب من أحد الكبار مساعدتك.',
    },
  ],
  hl: 1,
};

const BEES_EN = {
  q: 'how do bees make honey',
  lang: 'en',
  r: [
    {
      t: 'How bees turn nectar into honey',
      d: 'buzzclub.example',
      s: 'Bees sip nectar from flowers, carry it home and fan it with their wings until it thickens.',
    },
    {
      t: 'A day in the life of a bee hive',
      d: 'hivelife.example',
      s: 'Workers gather food, nurses feed the babies and guards watch the door of the hive.',
    },
    {
      t: 'Why flowers need bees',
      d: 'gardenkids.example',
      s: 'Bees carry pollen from flower to flower, and that helps plants to grow seeds and fruit.',
    },
  ],
  hl: 0,
};

const BEES_AR = {
  q: 'كيف يصنع النحل العسل',
  lang: 'ar',
  r: [
    {
      t: 'كيف يحول النحل الرحيق إلى عسل',
      d: 'buzzclub.example',
      s: 'يمتص النحل الرحيق من الزهور ويحمله إلى الخلية ثم يحرك جناحيه حتى يصير سميكا.',
    },
    {
      t: 'يوم في حياة خلية النحل',
      d: 'hivelife.example',
      s: 'العاملات تجمع الغذاء والمربيات تطعم الصغار والحارسات تراقب باب الخلية.',
    },
    {
      t: 'لماذا تحتاج الزهور إلى النحل',
      d: 'gardenkids.example',
      s: 'ينقل النحل الطلع من زهرة إلى أخرى فتنمو البذور والثمار.',
    },
  ],
  hl: 0,
};

/** The fixtures by name, then language. */
export const FIXTURES = {
  sky: { en: SKY_EN, ar: SKY_AR },
  bees: { en: BEES_EN, ar: BEES_AR },
};

/** A message in the al.search format (BEHAVIOUR-SPEC 6.8) for a fixture, in one of its three states. */
export function fixtureMessage(name = 'sky', lang = 'en', state = 'results', id = 'fx1') {
  const set = FIXTURES[name] || FIXTURES.sky;
  const f = set[lang === 'ar' ? 'ar' : 'en'] || set.en;
  const base = { id, kind: 'web', q: f.q, lang: f.lang, fixture: true };
  if (state === 'searching') return { ...base, st: 'searching' };
  if (state === 'none') return { ...base, st: 'none' };
  return { ...base, st: 'results', r: f.r, hl: f.hl };
}

/** A query the grown-up rule must catch (it contains a meta word only: no scripture text at all). */
export function flaggedMessage(lang = 'en', id = 'fx-sf') {
  return {
    id,
    kind: 'web',
    lang,
    fixture: true,
    st: 'results',
    q: lang === 'ar' ? 'معنى سورة' : 'what is a surah',
    sf: 1,
    r: [{ t: 'A page', d: 'pages.example', s: 'Fixture result that is never shown.' }],
    hl: 0,
  };
}

/** Results whose title carries a meta word: the whole page must turn into the grown-up card. */
export function metaWordMessage(lang = 'en', id = 'fx-meta') {
  return {
    id,
    kind: 'web',
    lang,
    fixture: true,
    st: 'results',
    q: lang === 'ar' ? 'قصص للاطفال' : 'stories for kids',
    r: [
      { t: 'Stories for kids', d: 'storytime.example', s: 'Fixture: a friendly page about stories.' },
      { t: 'A hadith for children', d: 'bookclub.example', s: 'Fixture: only the meta word is here, no text.' },
    ],
    hl: 0,
  };
}
