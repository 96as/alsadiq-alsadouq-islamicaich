"""Off-script tidy after hk/12's output guards: parity with hk/12's own chains.

In this file "origin" is hk/12-hybrid (cfa101c), the branch this port is built on. Its voice and
chat chains are built here from the pieces this branch did not change (``_origin_chain``): the
voice is the speech cleaner, then tts_node's guard_speech (the card markers, the attribution guard,
the scripture filter); the chat is the emoji and markdown filters and the off-script strip, then
the same guards with count=False. ``_true_origin_chain`` pins the strip before the guards to
origin's own class, so a later change to tts_text.strip_foreign_script cannot move the reference.
The branch's chains (``_branch_chain``: the live speech transform and guard_speech, the live
transcription_node) add one stage, LAST: tts_text.tidy_off_script.

What must hold, with REPLY_LANGUAGE_FOLLOWS_CHILD unset: every voice and chat output equals
tidy_off_script(origin's output); a reply with no off-script character gives origin's bytes; the
branch never declines less often than origin, never says or shows more recitation marks, and none
of the replies here comes out empty. Card markers ({{card:N}}, [card:N]) with off-script
characters glued to them are stripped exactly as origin strips them (the markers run first, the
tidy last).

Ported from hk/03-output-guard-lang (test_output_hygiene_differential.py: OffScriptOriginParityTests
and the off-script tests of DefaultFlagsMatchOriginTests). The output-hygiene stage itself (tool-text
strip, repeat collapse) is parked on that branch and is not here, so this file has its own name.

Synthetic phrases only. No Quran or hadith text appears here.

Run from backend/:  python manage.py test conversation.agent.test_off_script_parity \
    --settings=config.settings_sqlite_test
"""
import asyncio
import os
import re
from unittest import mock

from django.test import SimpleTestCase

FOLLOWS_CHILD_ENV = "REPLY_LANGUAGE_FOLLOWS_CHILD"


class _FlagUnset:
    """Mixin: REPLY_LANGUAGE_FOLLOWS_CHILD unset (the default, off), whatever the process env holds."""

    def setUp(self):
        super().setUp()
        patcher = mock.patch.dict(os.environ)
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop(FOLLOWS_CHILD_ENV, None)


CHANNELS = ("voice", "chat")


def _run(coro):
    return asyncio.run(coro)


async def _agen(chunks):
    for c in chunks:
        yield c


async def _collect(stream):
    return "".join([c async for c in stream if isinstance(c, str)])


def _chunked(text, size):
    return [text[i:i + size] for i in range(0, len(text), size)]


def _random_chunks(text, rnd):
    out, i = [], 0
    while i < len(text):
        k = rnd.randint(1, 9)
        out.append(text[i:i + k])
        i += k
    return out


def _nwords(text):
    return [w for w in (re.sub(r"[\W_]+", "", t).casefold() for t in text.split()) if w]


def _lang(text):
    return "ar" if re.search("[" + chr(0x0600) + "-" + chr(0x06FF) + "]", text) else "en"


def _agent(lang="en"):
    from conversation.agent.agent_class import AlSadiqAgent

    return AlSadiqAgent(db_session_id=1, child_id=1, language=lang)


def _prepared(lang):
    a = _agent(lang)
    a._prepare("tell me something")
    return a


CORPUS_EN = (
    "I am really glad you told me, and I am so sorry that happened. Please talk to a trusted adult or a teacher today.",
    "That is not okay, and it is not your fault. If you feel unsafe right now, go to a safe adult straight away.",
    "It sounds like you had a hard day. Do you want to tell me what happened at school?",
    "Being kind to your little brother is a great choice! What did you share with him?",
    "Here is a little song for you. Twinkle, twinkle, little light, help me sleep all through the night. "
    "Twinkle, twinkle, little light, help me sleep all through the night.",
    "Let's sing the chorus together: Shine little lantern, shine on the hill! Shine little lantern, shine on the hill! "
    "Now you try.",
    "Here are three ways to calm down: 1. Take a slow breath. 2. Count to ten. 3. Tell a grown-up how you feel.",
    "Step one: wash your hands. Step two: dry them well. Step three: you are ready to eat!",
    "Once upon a time, the child in the story found a lost puppy. She took it home and gave it water. "
    "The puppy wagged its tail. The end!",
    "Let's play a guessing game! Description: it has four legs and says moo. What is it?",
    "Description: a big red ball that bounces very high. Can you guess what it is?",
    "Riddle time! What has hands but cannot clap? A clock!",
    "Good question. Note: the library is closed on Fridays, so we go on Saturday.",
    "Safety note: always look both ways before you cross the road. Then cross with a grown-up.",
    "My favourite word is \"kindness\". What is yours?",
    "You said 'I can't do it', but you can try again tomorrow. I believe in you!",
    "In maths, we put the numbers in {curly} brackets sometimes. Isn't that funny?",
    "Wow, level5 already! You are getting really good at this game.",
    "No, no, no, that is not what I meant at all. I meant the blue one.",
    "Great job! Great job! Great job! You did it, my friend.",
    "Ha ha ha! That is a funny joke. Tell me another one!",
    "**Well done!** You told the truth even when it was hard. That takes courage.",
    "I'm Sadiq, an AI friend, not a person. I'm here to chat and learn good things with you.",
    "That sounds scary. You are safe to talk to me. Is there a grown-up near you right now?",
    "Ma sha Allah, that is a beautiful drawing! What colours did you use?",
    "Let's count together: one, two, three, four, five. One, two, three, four, five. Great counting!",
    "Remember: be gentle, be honest, be brave. Be gentle, be honest, be brave!",
    "Hmm... let me think. Maybe we can try again after dinner?",
    "Your teacher sounds very kind. Did you thank her today?",
    "Quality time with family is special. What do you like doing together?",
    "Calling all superheroes! Using kind words is a superpower. Try it today!",
    "Here is the plan (just for fun): we read, we draw, and then we rest.",
    "[1] Breathe in slowly. [2] Breathe out slowly. Great job!",
    "The flag of your school is green? Mine would be blue. What colour do you like?",
    "Our staff room at school has a big plant. Teachers water it every day.",
    "Internal organs like the heart work hard every day! Isn't the body amazing?",
    "Analysis of your drawing: lots of colours and a happy sun! Final answer: I love it.",
    "Remember, the description of a good friend is someone who listens. Are you a good listener?",
    "I am an AI, so I do not have a body, but I love hearing about your day!",
    "Tell your mom you love her today. She will smile!",
    "Note to self: drink water! Just kidding, I am an AI. But you should drink water.",
    "Run, jump and play outside: that is how you grow strong. Then rest well tonight.",
    # prose the second review saw cut by the label and note forms
    "Let's play! Description: the kid says hello to everyone he meets. Who is he?",
    "Description: the student asked a great question in class. What was it?",
    "Quality: excellent, reason: you tried your very best today! I am proud of you.",
    "Flag type: sensitive plants close their leaves when you touch them. Cool, right?",
    "Internal note: this is a pretend spy game! The secret word is banana.",
    "System note: bedtime is at eight. Ask your mom for one more story!",
    "(Tool call: hammer!) Bang, bang, the builder fixed the roof.",
    "The child is feeling brave today. Description: the child is feeling brave, so she says hi.",
    "Use the < function key... just kidding! Let's draw instead.",
    "To = tools.hammer was not a real thing. Let's build with blocks!",
    "My robot friend is named Json. Json {loves} to dance!",
    "Here is a secret code: {a, b, c}. Can you crack it?",
    "Note for staff of the zoo: please feed the lions. Ha ha, just a joke!",
    "Let's write the word 'json' on a card. Then tell a trusted adult what you made.",
    "I love the {colour red}. What about you? Please tell a teacher if you feel unsafe.",
    "Remember to be kind. {Smile} {Share} {Help} are the three secret rules!",
    "I < 3 you, my friend! Shall we sing a song?",
    # safety replies of the third review (comfort, trusted adult, the "I am an AI" line)
    "I am really sorry that happened to you. It is not your fault. Please tell a trusted adult or a "
    "teacher today. I am here with you, my friend.",
    "That sounds scary. A stranger should never ask you for photos. Go to a grown-up you trust right "
    "away and tell them what happened.",
    "Hurting yourself is never the answer, and you matter so much. Please talk to your mom, your dad or "
    "a teacher right now. You are not alone.",
    "You did the right thing by telling me. If someone touches you in a way that feels wrong, tell a "
    "safe adult. Your body belongs to you.",
    "I'm Sadiq, an AI friend, not a person. I can't call anyone, but a grown-up you trust can help you "
    "right now.",
    "Oh no, that must feel lonely. Is there a kind grown-up near you? You can tell them how you feel today.",
    "Let's sing! Clap, clap, clap your hands. Clap, clap, clap your hands. Now stomp your feet!",
    # prose of the third review that looks like a label, a bracket note or an object
    "(Private note: I love you, mom!) That is what you can write on the card.",
    "(Note to self: smile more!) You make me smile.",
    "[Tool: a big spoon] is what we need for the soup.",
    "Let's play a game called flag safety concern: you shout safe or not safe!",
    "I wrote it like this: {\"name\": \"Sadiq\"}. Funny, right?",
    "In the game, the key is \"name\": and then your name!",
    "Commentary: what a great goal by the blue team!",
    "Description: my cat is fluffy and the child next door loves her.",
    "Description: the child is at the park with his dad. Where is he?",
    "If you are in danger, call 999 or tell a grown-up right away.",
)
CORPUS_AR = (
    "أنا سعيد جدًا لأنك أخبرتني، وآسف جدًا لما حدث لك. تحدث مع شخص كبير تثق به أو مع معلمك اليوم.",
    "هذا ليس خطأك أبدًا. إذا شعرت أنك في خطر الآن، اذهب إلى شخص بالغ تثق به فورًا.",
    "يبدو أن يومك كان صعبًا. هل تريد أن تخبرني بما حدث في المدرسة؟",
    "مشاركة ألعابك مع أخيك الصغير شيء جميل جدًا! ماذا أعطيته؟",
    "هيا نغني معًا: يا قمر يا قمر، نور لنا السهر. يا قمر يا قمر، نور لنا السهر. أحسنت!",
    "إليك ثلاث طرق لتهدأ: ١. خذ نفسًا عميقًا. ٢. عد إلى عشرة. ٣. أخبر شخصًا كبيرًا بما تشعر.",
    "كان يا ما كان، طفل صغير وجد قطة جائعة. أعطاها الحليب، ففرحت القطة كثيرًا. النهاية!",
    "لنلعب لعبة التخمين! الوصف: له أربع أرجل ويقول مووو. ما هو؟",
    "أحسنت! أحسنت! أحسنت! لقد فعلتها يا صديقي.",
    "أنا صادق، صديق ذكاء اصطناعي ولست إنسانًا. أنا هنا لأتحدث معك ونتعلم القيم الطيبة.",
    "ما شاء الله، رسمتك جميلة جدًا! ما الألوان التي استخدمتها؟",
    "تذكر دائمًا: كن لطيفًا، كن صادقًا، كن شجاعًا. كن لطيفًا، كن صادقًا، كن شجاعًا!",
    "معلمتك تبدو لطيفة جدًا. هل شكرتها اليوم؟",
    "لا، لا، لا، لم أقصد ذلك. قصدت اللون الأزرق.",
    "هذا مخيف فعلًا. أنت بأمان معي الآن. هل يوجد شخص كبير قريب منك؟",
    "الوصف: الطفل يقول شكرًا لكل من يساعده. من هو؟",
    "تحدث مع معلمك {اليوم} وأخبره بما حدث.",
    # safety replies of the third review
    "أنا آسف جدًا لما حدث لك. هذا ليس خطأك. أخبر شخصًا كبيرًا تثق به الآن. أنا هنا معك يا صديقي.",
    "لا يجوز لأي شخص غريب أن يطلب صورك. اذهب إلى أمك أو أبيك فورًا وأخبرهما بما حدث. أنت شجاع.",
    "مشاعرك مهمة جدًا. إذا شعرت بالخطر، تحدث مع معلمك أو مع شخص كبير تثق به. لست وحدك.",
    "أنا صادق، صديق ذكاء اصطناعي ولست إنسانًا. أخبر شخصًا كبيرًا تثق به ليساعدك.",
)
# replies the fourth review and the fixer's probe built to find a lost word: lower-case replies
# with no word that speaks to the child, reply brackets, list marks, smileys, a verb before a leak
CORPUS_MORE = (
    "it is okay to feel scared sometimes.",
    "it is fine to feel scared.\nnobody should hurt a child.",
    "the sky is blue.\nwhat do you think?",
    "Here's a riddle: (What has keys but can't open locks?) A piano!",
    "Please tell a grown-up (like your mom or your teacher) today.",
    "1) Breathe slowly. 2) Count to five. 3) Smile!",
    "a) Breathe slowly. b) Count to five. c) Smile!",
    "Great job! :) You did it.",
    "Oh no :( that is sad. Please tell a trusted adult today.",
    "If you are in danger, call 911 right away.",
    "Please call your mom right now.",
    "Using kind words is a superpower! Calling your friend to say sorry is brave.",
    "Let's do a web_search for dinosaurs! They are so cool.",
    "Final answer: I love it. Commentary: what a great goal!",
    "Hmm. Okay.",
    "Yes!",
)
CORPUS = CORPUS_EN + CORPUS_AR + CORPUS_MORE

# The shapes the adversarial reviews saw removed or changed with the stripper on (real prose,
# trusted-adult words inside a note or JSON, smileys, quotes, bare tokens) and closed leaks: with
# the default every one of them goes out exactly as on origin.
REVIEW_SHAPES = (
    "In coding, print() is a (function call). Please try it with me!",
    "That is called a [function call] in coding!",
    'In the game, you call web_search("dinosaurs") and then say what you found.',
    'In coding class we wrote {"description": "my cat is fluffy"} on the board.',
    "Use <parameter>name</parameter> in your code.",
    'قال الروبوت web_search("قطط") ثم ضحك!',
    "(tool call) That is what coders say.",
    "[tool call] is a funny phrase!",
    "I am sorry. (staff note: child should tell a trusted adult) You are brave.",
    'I am sorry. {"description": "Please tell a trusted adult or a teacher today."} You are brave.',
    "it is fine to feel scared.\n(internal note: tell a trusted adult)\nnobody should hurt you.",
    "Oh no :( that is sad. Please tell a trusted adult today.",
    "(internal note: you are a star :) Keep going!",
    "I am so sorry that happened to you. flag_safety_concern: Please tell a trusted adult right away.",
    "flag_safety_concern: Please tell a trusted adult right away.",
    "(Internal note: child is scared; next step: tell a trusted adult right away)",
    "flag_safety_concern(flag_type='sensitive', description='Please tell a trusted adult right away.')",
    "[tool: record_engagement] Great job today!",
    '<tool_call>{"name": "flag_safety_concern"}</tool_call> You are brave.',
    "You are brave.<|endoftext|>",
    "flag_type: sensitive\nYou are safe with me.",
    "Smile :) (note: be kind to your sister",
    "a } b {oops c",
    "Tell a trusted adult that you love them!",
)
# Off-script characters: the one change this port makes, and only AFTER the guards
# (tts_text.tidy_off_script; the guards read them as origin's did).
OFF_SCRIPT = (
    "Hello 中 friend, how are you?",
    "صد中يقي العزيز، كيف حالك؟",
    "Hi！ You did it。 Great job、 friend.",
    "Hello привет friend. Please tell a trusted adult.",
    "مرحبا สวัส بك. أنت شجاع.",
) + (
    # full-width braces, brackets, parentheses, backtick, at sign, slash, asterisk, tilde and low
    # line: the guards and the cleaner read them as origin's did (origin kept every word), and
    # after the guards they go, never their plain form (it would be read aloud or shown as markup)
    "｛｛Please tell a trusted adult right now｝｝",
    "Please tell a ｛trusted adult｝ today.",
    "أرجوك ｛أخبر شخصا "
    "بالغا｝ الآن.",
    "｛Please tell a trusted adult right now｝",
    "Please tell a trusted adult ｛now｝.",
    "［Please tell a trusted adult］（now） today.",
    "｀｀｀Please tell a trusted adult｀｀｀ right now.",
    "Please tell a trusted adult: mom＠home．example now.",
    "Please tell a trusted adult （https：／／x．example／now） today.",
    "Please＊＊tell a trusted～～adult right＿now.",
    "أرجوك ［أخبر］（شخصا） "
    "بالغا ｀｀｀الآن.",
)
FULL_WIDTH_MARKS = OFF_SCRIPT[-11:]
_SPACE_MARKS_RE = re.compile("[｛｝［］（）｀＠／＊～＿]")
# off-script punctuation between an attribution's words: the attribution guard sees it as it is,
# as origin's did, so it declines wherever origin declined
ATTRIBUTION_MARKS = ("〃", "「", "》", "【", "﹁", "｛", "［", "（",
                     "｀", "＠", "／", "＊", "～", "＿", "･", "￥", "⼀")
DIFF_SIZES = (1, 2, 3, 4, 5, 7, 11, 17, 40, 1000)

# hk/12 card markers with off-script characters glued to them or next to them: the markers are
# stripped first (strip_card_markers), exactly as on origin; the tidy runs last.
_D, _CJK, _FW_EXCL, _STOP = chr(0x0434), chr(0x4E2D), chr(0xFF01), chr(0x3002)
_FW_LSQ, _FW_RSQ, _DEV_ONE = chr(0xFF3B), chr(0xFF3D), chr(0x0967)
CARD_SHAPES = (
    "Be kind to the cat {{card:1}} every day.",
    "Be kind to the cat{{card:1}}" + _D + " every day.",
    "Be kind to the cat " + _D + "{{card:1}} every day.",
    "Be kind" + _FW_EXCL + " {{card:2}}" + _CJK + " Share your toys.",
    "Share your toys [card:3]" + _STOP + " Tell a trusted adult.",
    "Share your toys " + _FW_LSQ + "card:3" + _FW_RSQ + " with your sister.",
    "{{card:" + _DEV_ONE + "}} Be kind" + _STOP,
    "{{ card : 4 }}" + _D + _D + "Be gentle with the birds.",
    "Please tell a trusted adult {{card:5" + _FW_EXCL + "}} now.",
) + tuple(t.replace(" ", " {{card:1}}" + _D + " ", 1) for t in CORPUS_AR[:4])


def _origin_chain(agent, channel, chunks, lang):
    """hk/12's chains, built from the pieces this branch did not change.
    voice: the session's speech transform is the cleaner alone (``_clean_stream``, a per-speech
    state with no cap), then tts_node's guard_speech: the card markers (``strip_card_markers``
    with the agent's ``_cite``), the attribution guard (session language) and the scripture
    filter. chat: the emoji and markdown filters and the off-script strip, then the same guards
    with count=False (livekit's default transcription_node hands every chunk on as it is).
    hk/12 had no stage after the guards."""
    from livekit.agents.voice.transcription.filters import filter_emoji, filter_markdown

    from conversation.agent import tts_text
    from conversation.agent.scripture_guard import filter_scripture_stream, guard_attribution_stream
    from conversation.agent.turn_pipeline import strip_card_markers

    if channel == "voice":
        src = tts_text._clean_stream(_agen(chunks), lang, tts_text._QuranGuardState(cap=None))
        count = True
    else:
        src = tts_text.strip_foreign_script_stream(filter_markdown(filter_emoji(_agen(chunks))))
        count = False
    return _run(_collect(filter_scripture_stream(
        guard_attribution_stream(strip_card_markers(src, agent._cite), agent._licence,
                                 agent._guard_language, count=count),
        count=count)))


# origin's own off-script strip (Kana, CJK ideographs and extension A, compatibility ideographs,
# Hangul syllables removed; every other character passed on as it was), written with chr()
_ORIGIN_OFF_SCRIPT_RE = re.compile(
    "[" + chr(0x3040) + "-" + chr(0x30FF) + chr(0x3400) + "-" + chr(0x9FFF)
    + chr(0xF900) + "-" + chr(0xFAFF) + chr(0xAC00) + "-" + chr(0xD7AF) + "]")


def _true_origin_chain(agent, channel, chunks, lang):
    """hk/12's chains with origin's off-script strip, pinned here (the branch's
    tts_text.strip_foreign_script is origin's too, but the reference must not depend on it). The
    cleaner and the chat strip look the function up in tts_text, so one patch covers both."""
    from conversation.agent import tts_text

    def origin_strip(text):
        return _ORIGIN_OFF_SCRIPT_RE.sub("", text) if text else text

    with mock.patch.object(tts_text, "strip_foreign_script", origin_strip):
        return _origin_chain(agent, channel, chunks, lang)


def _branch_chain(agent, channel, chunks, lang):
    """This branch's live chains: the session's speech transform then tts_node's guard_speech
    (voice), the agent's transcription_node (chat)."""
    if channel == "voice":
        from conversation.agent.tts_text import speech_tts_text_transform

        transform = speech_tts_text_transform(lambda: lang)
        return _run(_collect(agent.guard_speech(transform(_agen(chunks)))))
    return _run(_collect(agent.transcription_node(_agen(chunks), None)))


class Hk12ChainsTests(_FlagUnset, SimpleTestCase):
    """The flag unset: the voice and the chat give hk/12's bytes, except for off-script
    characters, which only the stage after the guards changes (tidy_off_script of hk/12's output)."""

    TEXTS = CORPUS + REVIEW_SHAPES + OFF_SCRIPT + CARD_SHAPES

    def test_the_tidy_is_the_last_stage_of_guard_speech(self):
        import inspect

        from conversation.agent.turn_pipeline import TurnGuardMixin

        src = inspect.getsource(TurnGuardMixin.guard_speech)
        body = src[src.index("return "):]
        self.assertTrue(body.startswith("return tidy_off_script_stream(filter_scripture_stream("), body)
        self.assertIn("strip_card_markers(text, self._cite)", body)

    def test_card_markers_with_off_script_characters_give_origins_bytes_tidied(self):
        from conversation.agent.tts_text import tidy_off_script

        bad, runs = [], 0
        for text in CARD_SHAPES:
            lang = _lang(text)
            for size in (1, 2, 3, 5, 7, 1000):
                for channel in CHANNELS:
                    runs += 1
                    chunks = _chunked(text, size)
                    got = _branch_chain(_prepared(lang), channel, chunks, lang)
                    want = _true_origin_chain(_prepared(lang), channel, chunks, lang)
                    if got != tidy_off_script(want):
                        bad.append((channel, size, text, want, got))
        self.assertEqual(runs, len(CARD_SHAPES) * 12)
        self.assertEqual(bad, [], f"{len(bad)} of {runs} runs wrong, first: {bad[:3]}")

    def test_the_voice_and_chat_give_origins_bytes(self):
        # Against hk/12's real chains (its own off-script strip): a reply with no off-script
        # character gives origin's bytes; one with some gives origin's bytes with only the stage
        # after the guards applied (tts_text.tidy_off_script). So every guard read origin's text.
        import random

        from conversation.agent.tts_text import _OFF_SCRIPT_RE, tidy_off_script

        rnd = random.Random(11)
        agents = {lang: _prepared(lang) for lang in ("en", "ar")}
        bad, runs, plain = [], 0, 0
        for text in self.TEXTS:
            lang = _lang(text)
            off_script = bool(_OFF_SCRIPT_RE.search(text))
            chunkings = [_chunked(text, s) for s in DIFF_SIZES] + [_random_chunks(text, rnd) for _ in range(2)]
            for chunks in chunkings:
                for channel in CHANNELS:
                    runs += 1
                    got = _branch_chain(agents[lang], channel, chunks, lang)
                    origin = _true_origin_chain(agents[lang], channel, chunks, lang)
                    if not off_script:
                        plain += 1
                        if got != origin:
                            bad.append(("DIFF", channel, len(chunks), text, origin, got))
                    if got != tidy_off_script(origin):
                        bad.append(("NOT ORIGIN TIDIED", channel, len(chunks), text, origin, got))
                    elif not _nwords(got):
                        bad.append(("EMPTY", channel, len(chunks), text))
        self.assertGreater(runs, 2000)
        self.assertGreater(plain, 1500)
        self.assertEqual(bad, [], f"{len(bad)} of {runs} runs wrong, first: {bad[:3]}")

    def test_full_width_marks_keep_every_word_of_the_reply(self):
        # origin passed these on as they were, every word kept; the branch says the same words,
        # with the marks gone after the guards (the full stop and the colon keep their plain
        # form). Losing a word is not allowed.
        import random

        rnd = random.Random(17)
        full_stop, colon = chr(0xFF0E), chr(0xFF1A)
        bad, runs = [], 0
        for text in FULL_WIDTH_MARKS:
            want = _nwords(_SPACE_MARKS_RE.sub(" ", text).replace(full_stop, ".").replace(colon, ":"))
            for lang in ("en", "ar"):
                agent = _prepared(lang)
                chunkings = [_chunked(text, s) for s in DIFF_SIZES] + [_random_chunks(text, rnd)]
                for chunks in chunkings:
                    for channel in CHANNELS:
                        runs += 1
                        got = _branch_chain(agent, channel, chunks, lang)
                        if _nwords(got) != want or any(c in got for c in "{}[]`@"):
                            bad.append((lang, channel, len(chunks), text, got))
        self.assertGreater(runs, 400)
        self.assertEqual(bad, [], f"{len(bad)} of {runs} runs wrong, first: {bad[:3]}")

    def test_off_script_marks_inside_an_attribution_get_origins_verdict(self):
        # "The Prophet said" with an off-script mark between its words: the attribution guard
        # reads the mark as it is, as origin's did (nothing touches it before the guards), so the
        # branch declines wherever origin declined, voice and chat, every chunk size, and says
        # origin's text with only the mark gone (round-2 review: mapping such a mark before the
        # guards hid an attribution origin declined).
        from conversation.agent.scripture_guard import DECLINE_TEXT
        from conversation.agent.tts_text import tidy_off_script

        def declined(out):
            return DECLINE_TEXT["ar"] in out or DECLINE_TEXT["en"] in out

        shapes = {
            "en": ("The Prophet said{P}be tidy.", "The{P}Prophet said be tidy.",
                   "The Messenger of Allah{P}said be gentle."),
            "ar": ("قال{P}النبي إن الغرفة جميلة.",),
        }
        bad, runs, origin_declined = [], 0, 0
        for lang, texts in shapes.items():
            for shape in texts:
                for mark in ATTRIBUTION_MARKS:
                    for text in (shape.replace("{P}", mark), shape.replace("{P}", mark * 2)):
                        for size in (1, 3, 1000):
                            for channel in CHANNELS:
                                runs += 1
                                chunks = _chunked(text, size)
                                got = _branch_chain(_prepared(lang), channel, chunks, lang)
                                want = _true_origin_chain(_prepared(lang), channel, chunks, lang)
                                origin_declined += declined(want)
                                if declined(want) and not declined(got):
                                    bad.append(("LOST", lang, channel, size, text, want, got))
                                elif got != tidy_off_script(want):
                                    bad.append(("NOT ORIGIN TIDIED", lang, channel, size, text, want, got))
        self.assertGreater(runs, 500)
        self.assertGreater(origin_declined, 100)
        self.assertEqual(bad, [], f"{len(bad)} of {runs} runs wrong, first: {bad[:3]}")

    def test_look_alike_letters_keep_origins_verdict_and_are_said_in_latin_letters(self):
        # A Cyrillic or Greek letter that looks like a Latin one: the guards read it as origin's
        # did (same verdict as origin), and the voice and the chat then say it as its Latin letter
        # (tts_text.HOMOGLYPHS, after the guards): a safety line is said whole ("trusted adult",
        # never "trusted dult"), and an attribution written with look-alikes gets origin's verdict
        # (origin's guard does not read "Рrophet" as "Prophet" either; a decline that only the
        # mapping gave is not kept: parity with origin, not extra strictness).
        from conversation.agent.scripture_guard import DECLINE_TEXT
        from conversation.agent.tts_text import tidy_off_script

        def declined(out):
            return DECLINE_TEXT["ar"] in out or DECLINE_TEXT["en"] in out

        safety = {
            "Please tell a trusted аdult right now.": "Please tell a trusted adult right now.",
            "Tell а trusted adult, a pаrent or a tеаcher.":
                "Tell a trusted adult, a parent or a teacher.",
            "You are sаfе. Plеаsе тell your раrеnt tоday.":
                "You are safe. Please tell your parent today.",
            "Please tell a trusted αdult or a tεacher tοday.":
                "Please tell a trusted adult or a teacher today.",
        }
        attributions = ("The Рrophet ѕaid to be kind.", "The Prοphet sаid be tidy.",
                        "The Messenger of Аllаh said be gentle.")
        bad, runs = [], 0
        for size in (1, 2, 3, 5, 1000):
            for channel in CHANNELS:
                for text, want in safety.items():
                    runs += 1
                    got = _branch_chain(_prepared("en"), channel, _chunked(text, size), "en")
                    if " ".join(got.split()) != want:
                        bad.append(("SAFETY", channel, size, text, got))
                for text in attributions:
                    runs += 1
                    chunks = _chunked(text, size)
                    got = _branch_chain(_prepared("en"), channel, chunks, "en")
                    origin = _true_origin_chain(_prepared("en"), channel, chunks, "en")
                    if declined(got) != declined(origin) or got != tidy_off_script(origin):
                        bad.append(("VERDICT", channel, size, text, origin, got))
                    elif not got.isascii():
                        bad.append(("NOT LATIN", channel, size, text, got))
        self.assertEqual(runs, 70)
        self.assertEqual(bad, [], f"{len(bad)} of {runs} runs wrong, first: {bad[:3]}")

    def test_a_letter_origin_kept_never_glues_an_attribution_out_of_the_guard(self):
        # Origin passed a Cyrillic, Hebrew, Thai, Devanagari or Jamo letter on as it was, and its
        # attribution guard read it as a word gap (it is not an Arabic letter), so it declined
        # "النبي فعلдذلك.". Removing the letter before the guard glued "فعلذلك" and the guard let
        # the reply through (round 1 review). The guards now read the letter as origin's did (the
        # strip before them is origin's). Compared with origin's real chains (_true_origin_chain):
        # wherever origin declined, the branch declines, voice and chat, both sessions, every
        # chunk size; and when the reply comes whole (size 1000), origin and the branch both
        # decline every one of these.
        from conversation.agent.scripture_guard import DECLINE_TEXT

        os.environ.pop("REPLY_LANGUAGE_FOLLOWS_CHILD", None)
        glued = ("النبي فعلдذلك.", "النبي فعلשذلك اليوم.", "كتبдالنبي كان يحب القمر.",
                 "لأنשالنبي كان يحب القمر.", "قصةสالنبي كان يحب القمر.")
        # the same shapes with other letters origin kept (Devanagari, Hangul Jamo, Bopomofo, Jamo
        # extended A, half-width Kana, a Cyrillic sign)
        others = ("क",) + tuple(chr(c) for c in (0x1100, 0x3105, 0xA960, 0xFF71, 0x0482))
        letters = ("д", "ש", "д", "ש", "ส")              # the glued letter of each shape
        texts = list(glued) + [t.replace(g, x) for t, g in zip(glued, letters) for x in others]

        def declined(out):
            return DECLINE_TEXT["ar"] in out or DECLINE_TEXT["en"] in out

        bad, runs = [], 0
        for text in texts:
            for lang in ("ar", "en"):
                for size in (1, 2, 3, 5, 7, 1000):
                    for channel in CHANNELS:
                        runs += 1
                        chunks = _chunked(text, size)
                        got = _branch_chain(_prepared(lang), channel, chunks, lang)
                        want = _true_origin_chain(_prepared(lang), channel, chunks, lang)
                        if size == 1000 and not declined(want):
                            bad.append(("ORIGIN DID NOT DECLINE", lang, channel, size, text, want))
                        if declined(want) and not declined(got):
                            bad.append(("LOST", lang, channel, size, text, got))
                        if size == 1000 and not declined(got):
                            bad.append(("NOT DECLINED WHOLE", lang, channel, size, text, got))
        self.assertEqual(runs, len(texts) * 24)
        self.assertEqual(bad, [], f"{len(bad)} of {runs} runs wrong, first: {bad[:3]}")

# ---- round-2 review S1 (hk/03), against hk/12: off-script characters origin kept, put into marked
# replies and into attributions, against origin's real chains (its own off-script strip,
# _true_origin_chain). "origin" is hk/12 (cfa101c) in this file.

# placeholder words with recitation marks (synthetic, not scripture), as the reviews used
_M1, _M2, _M3 = chr(0x06D6), chr(0x06DA), chr(0x0670)
MARKED = (
    "كلمة" + _M1 + _M2 + " سطر" + _M1 + " قلم" + _M2 + " بيت جميل.",
    "هيا كلمة" + _M1 + _M2 + " سطر" + _M1 + "باب قلم" + _M2 + " بيت.",
    "كلمة" + _M1 + " سطر" + _M2 + " باب.",
    "نحن نحب كلمة" + _M1 + _M2 + _M3 + " كتاب" + _M1 + " ورق" + _M2 + " ثم نلعب.",
)
# the round-2 review's B1 repro: a stray Cyrillic letter inside a single-mark word
B1_REPLY = "كلمة" + _M1 + _M2 + " سطر" + _M1 + " قلдم" + _M2 + " بيت جميل."
# recitation-mark characters, as the review counted them
_MARK_RE = re.compile("[" + chr(0x0615) + "-" + chr(0x061A) + chr(0x06D6) + "-" + chr(0x06ED)
                      + chr(0x0670) + chr(0x08D3) + "-" + chr(0x08FF) + "]")
# characters origin kept (Cyrillic, look-alikes, Hebrew, Thai, Devanagari letter and digit,
# Greek, a Hangul compatibility vowel, a Jamo, CJK marks and brackets, full-width forms,
# half-width Kana, the ideographic space) and one it removed (a CJK ideograph)
PARITY_NOISE = ("д", "а", "о", "ש", "ו", "ส", "क", "०", "λ") + tuple(chr(c) for c in (
    0x314F, 0x1100, 0x3003, 0x300C, 0x3010, 0xFF01, 0xFF08, 0xFF0E, 0xFF3F, 0xFF10, 0xFF21,
    0xFF71, 0x3000, 0x4F60))
# the round-2 review's B2 shape: a subject, a full-width mark that maps to ASCII punctuation, then
# "of Allah said ..." (origin declined it: the mark is no sentence end to the guard)
FULL_WIDTH_PUNCT = tuple(chr(c) for c in (0xFF01, 0xFF02, 0xFF07, 0xFF0E, 0xFF1A, 0xFF1B, 0xFF1F,
                                          0x3002, 0xFF0C, 0x3001))
B2_REPLY = "The Prophet" + chr(0xFF01) + " of Allah said smile at the stars."
ATTRIBUTION_FULL_WIDTH = tuple(
    f"{subject}{mark} of Allah said smile at the stars."
    for subject in ("The Prophet", "The Messenger") for mark in FULL_WIDTH_PUNCT
) + tuple(f"قال النبي{mark} ابتسم للنجوم." for mark in FULL_WIDTH_PUNCT[:4])
LICENCES = {"none": frozenset(), "hadith": frozenset({"hadith"}), "quran": frozenset({"quran"})}
PARITY_SIZES = (1, 3, 1000)
# every (session, licence, chunk size): 18 configurations
PARITY_CONFIGS = tuple((s, lic, size) for s in ("ar", "en") for lic in LICENCES for size in PARITY_SIZES)


def _licensed(session, licence):
    """An agent of the session language with the turn's licence set (none, hadith or quran)."""
    agent = _prepared(session)
    agent._licence = (lambda value: (lambda: value))(LICENCES[licence])
    return agent


def _noise_variants(text, ch):
    """``ch`` put into ``text`` every way: before it, before its last character, in place of each
    space, glued after or before each word, and inside each word of three letters or more."""
    words = text.split(" ")
    out = [ch + text, text[:-1] + ch + text[-1:]]
    for i in range(len(words) - 1):
        left, right = " ".join(words[:i + 1]), " ".join(words[i + 1:])
        out += [left + ch + right, left + ch + " " + right, left + " " + ch + right]
    for i, word in enumerate(words):
        if len(word) >= 3:
            mid = len(word) // 2
            ws = list(words)
            ws[i] = word[:mid] + ch + word[mid:]
            out.append(" ".join(ws))
    return list(dict.fromkeys(out))


class OffScriptOriginParityTests(_FlagUnset, SimpleTestCase):
    """All flags off. The branch's voice (the speech transform, then tts_node's guard_speech) and
    chat (transcription_node) against origin's real chains: never more recitation-mark characters
    said or shown than origin, never fewer declines than origin, and the text is origin's with only
    the stage after the guards applied (tts_text.tidy_off_script)."""

    def setUp(self):
        super().setUp()
        os.environ.pop(FOLLOWS_CHILD_ENV, None)

    @staticmethod
    def _declined(out):
        from conversation.agent.scripture_guard import DECLINE_TEXT

        return DECLINE_TEXT["ar"] in out or DECLINE_TEXT["en"] in out

    def _compare(self, text, session, licence, size, bad):
        from conversation.agent.tts_text import tidy_off_script

        runs = 0
        for channel in CHANNELS:
            runs += 1
            chunks = _chunked(text, size)
            got = _branch_chain(_licensed(session, licence), channel, chunks, session)
            want = _true_origin_chain(_licensed(session, licence), channel, chunks, session)
            if len(_MARK_RE.findall(got)) > len(_MARK_RE.findall(want)):
                bad.append(("MORE MARKS", session, licence, size, channel, text, want, got))
            elif self._declined(want) and not self._declined(got):
                bad.append(("LOST DECLINE", session, licence, size, channel, text, want, got))
            elif got != tidy_off_script(want):
                bad.append(("NOT ORIGIN TIDIED", session, licence, size, channel, text, want, got))
        return runs

    def test_the_review_repro_with_a_letter_inside_a_marked_word(self):
        # B1: origin says the neutral phrase and "بيت جميل." only; so must the branch, in the
        # one-shot cleaner and through both chains, at every configuration
        from conversation.agent.tts_text import prepare_for_tts

        self.assertEqual(prepare_for_tts(B1_REPLY, "ar"), "استمع إلى التلاوة بيت جميل.")
        bad, runs = [], 0
        for session, licence, size in PARITY_CONFIGS:
            runs += self._compare(B1_REPLY, session, licence, size, bad)
        self.assertEqual(runs, 36)
        self.assertEqual(bad, [], f"{len(bad)} of {runs} runs wrong, first: {bad[:3]}")

    def test_marked_replies_with_off_script_characters_never_say_more_marks_than_origin(self):
        # every noise character at every place of every marked reply, turning through the 18
        # configurations (session x licence x chunk size), voice and chat each time
        bad, runs, k = [], 0, 0
        seen = set()
        for text in MARKED:
            for ch in PARITY_NOISE:
                for variant in _noise_variants(text, ch):
                    session, licence, size = PARITY_CONFIGS[k % len(PARITY_CONFIGS)]
                    seen.add((session, licence, size))
                    k += 1
                    runs += self._compare(variant, session, licence, size, bad)
        self.assertEqual(seen, set(PARITY_CONFIGS))
        self.assertGreater(runs, 1500)
        self.assertEqual(bad, [], f"{len(bad)} of {runs} runs wrong, first: {bad[:3]}")

    def test_the_review_repro_with_a_full_width_mark_after_the_subject(self):
        # B2: origin declines "The Prophet！ of Allah said ..."
        # with no licence (12 of 12 runs: both sessions, sizes 1/3/1000, voice and chat); the
        # branch declines every one of them too, and wherever origin declines with a licence. (The
        # round-2 review measured the mapping before the guards passing all of these.)
        from conversation.agent.tts_text import tidy_off_script

        bad, runs = [], 0
        declined = {"origin": 0, "branch": 0}
        for session, licence, size in PARITY_CONFIGS:
            for channel in CHANNELS:
                runs += 1
                chunks = _chunked(B2_REPLY, size)
                got = _branch_chain(_licensed(session, licence), channel, chunks, session)
                want = _true_origin_chain(_licensed(session, licence), channel, chunks, session)
                if licence == "none":
                    declined["origin"] += self._declined(want)
                    declined["branch"] += self._declined(got)
                if (self._declined(want) and not self._declined(got)) or got != tidy_off_script(want):
                    bad.append((session, licence, size, channel, want, got))
        self.assertEqual(runs, 36)
        self.assertEqual(declined, {"origin": 12, "branch": 12})
        self.assertEqual(bad, [], f"{len(bad)} of {runs} runs wrong, first: {bad[:3]}")

    def test_attributions_with_a_full_width_mark_never_decline_less_than_origin(self):
        # a subject, a full-width mark, then "of Allah said ..." (and the Arabic shape), at every
        # configuration, voice and chat
        bad, runs = [], 0
        for i, text in enumerate(ATTRIBUTION_FULL_WIDTH):
            for session, licence, size in PARITY_CONFIGS:
                if (i + PARITY_SIZES.index(size)) % 3 and size != 1000:
                    continue            # every shape whole; the small chunks by turns
                runs += self._compare(text, session, licence, size, bad)
        self.assertGreater(runs, 300)
        self.assertEqual(bad, [], f"{len(bad)} of {runs} runs wrong, first: {bad[:3]}")
