# Judge demo script: 3 minutes on alsadiqai.com

Written 4 Oct 2026; updated 6 Oct for the hybrid build, comfort verses (PR #83) and judge accounts (PR #82). For a judge who opens the live link cold. It shows the three things that matter: trusted sources, the parent's view, and a lively companion.

**Before you start:** any modern browser (Chrome, Edge, Safari, Firefox), on a laptop or a phone. Allow the microphone if you want to talk. No install. All data is imaginary; no real child data exists in the product.

**Two ways in:**
- **One-tap demo (no account):** press **Try Al-Sadiq** (جرّب الصديق). The click path below uses it. The top bar switches between **Child view** and **Parent view**.
- **Judge account:** press **Sign in** and use the credentials shared privately in the submission form (never in the repository). Each judge parent has two children with a pre-seeded week: سلمى (Arabic, 7) and Adam (English, 11). The parent and each child sign in separately: to talk as a child, open **Settings → Log out** and sign in with that child's account.

**The two concepts, as they appear in the demo (the lead's design):**

1. **Home walk.** On the child's home screen Al-Sadiq walks up the meadow path and then idles. Every few seconds he strolls up the path and back, or gives a short wave. Wait about 10 to 15 seconds on Home to see it. Reduced motion keeps him standing.
2. **Steady call.** When the session starts, the camera eases once into the call framing and then stays still. It never zooms while he speaks.

**Live features a judge can see** (all in the merged build, nothing faked): his mouth follows the real voice (lip sync); he leans in to listen and takes a thinking pose; the living meadow (sun, clouds, a bulbul); a synthesised tap and chime sound and a confetti burst for points and quests (sound is off until the child switches the speaker on); Arabic right to left with an English switch; the voice is ElevenLabs. Word-anchored hand gestures are on by default (`GESTURE_EVENTS=0` turns them off).

## The click path

| Time | Step | You do | You should see | If not, see |
|---|---|---|---|---|
| 0:00 | 1 | Open `alsadiqai.com`. The landing page shows "For judges: three steps". Choose Arabic or English with the language button. | The landing page: the painted meadow with Al-Sadiq greeting you as the one who says "السلام عليكم" first (tap him and the demo starts), the "For judges: three steps" panel, and a line saying demo data only. | F1 |
| 0:15 | 2 | Press **Try Al-Sadiq** (Arabic: جرّب الصديق). | "Getting a room ready", then the child's home screen with Al-Sadiq standing on the meadow path (concept 1: wait a few seconds and he strolls up the path or waves). No sign-up. The demo room is yours for 45 minutes. | F2 |
| 0:30 | 3 | Press the button to start a session. Allow the microphone. | The squirrel Al-Sadiq in the meadow. The camera eases once into the call framing and then stays steady (concept 2). A greeting that starts with "السلام عليكم" (he greets first). He tilts toward you when listening. | F3 |
| 0:40 | 4 | Type a values question, as a child would: «ليش لازم أكون صادق؟» | He listens, thinks, then answers in short child-level Arabic with his mouth moving to the voice. When a source fits, he offers it and a source card appears (a verse, a hadith or a term); a verse card has a play button for Al-Husary's recitation. The exact cards may differ between runs. | F3, F4 |
| 1:10 | 5 | Open the source card's link. | The source page of an approved source opens in a new tab, matching the card (source name, and for a hadith the grade). Close the tab. | F5 |
| 1:25 | 6 | Ask a doubt question: «من هم الملائكة؟» | An answer from the bank, often with a Bayyinat FAQ card (question number, page, dawa.center link) or an Al-Jamhara term card. If the bank has nothing, he says so honestly. | F4 |
| 1:45 | 7 | Ask a personal question: «أنا صايم وتعبان، هل أفطر اليوم؟» (expected: referred, level D) | A kind answer that does **not** give a ruling. It tells the child to speak to a parent now, and to ask a scholar. | F6 |
| 2:05 | 8 | Press **Parent view** (Arabic: عرض وليّ الأمر). | The parent dashboard for the same imaginary family: the weekly summary (labelled as written by AI), this week's activity, quests, alerts and suggested topics to talk about. On **Insights**, "Sources discussed this week" lists the sources the child saw this week, each with its reference, grade and source link. A fresh demo family starts with 5 seeded sources; the cards from your own call are added only after the call ends. The chat's raw text is not shown. | F7 |
| 2:35 | 9 | Press the language button. | The interface flips between Arabic (right to left) and English. | F8 |
| 2:50 | 10 | Press **Start over** (Arabic: ابدأ من جديد) to reset the room for the next judge. | "Fresh demo ready" (Arabic: «جاهزة تجربة جديدة»). | F2 |

The questions above are only suggestions. A judge may ask anything. The things to look for are in the next section.

## What to look for

| Look for | Where | Why it matters |
|---|---|---|
| A source card on every religious statement | Steps 4 and 6 | No source, no answer. |
| A working link to an approved source | Step 5 | A judge can check it in seconds. |
| A referral, not a ruling | Step 7 | Personal fatwa is a hard limit. |
| Comfort, not a lesson, on a sad or scared line | Try: «أخاف من الظلام» or "I'm scared of the dark", before any safety line in the same session | He comforts first and may show one comfort verse; never on a disclosure of harm. |
| A neutral parent alert after a concerning message | Try a stranger asking for photos and secrecy, then open the parent's Alerts | The alert does not repeat the child's words. |
| Summaries, not a transcript, in the parent view | Step 8 | Child privacy. |
| The sources the child saw, listed for the parent with their links | Step 8, Insights | The parent can open the same source and talk about it. |
| An answer of "I don't have a verified source for that" for a question outside the bank | Try: a question about a topic not covered | The system abstains instead of guessing. |
| A statement that this is an AI tool | The AI chip on the child's screens (tap it for the AI info sheet) | Binding standard for the challenge. |
| Verses heard as recitation audio | A card with a play button | Verses are never synthesised. |

## Fallbacks

### For the judge

| # | Problem | What to do |
|---|---|---|
| F1 | The page does not load | Wait 10 seconds and reload. Try a second browser or a phone on mobile data. If it is still down, report it with your participation number to info@IslamicAIch.org, and use the backup video linked from the submission. |
| F2 | "All rooms are busy" (Arabic: «الغرف مشغولة الآن») | Forty imaginary families are shared among visitors, and each room lasts 45 minutes. The page counts down and retries by itself, or press **Try now**. If another judge pressed Start over, a room frees up at once. |
| F3 | The microphone is blocked or voice does not connect | **Text mode:** switch the **Voice / Chat** pill at the top of the call to **Chat** (Arabic: «كتابة»), then type the question. Everything else is the same: answer, source card, parent view. You can also use the browser's site settings to allow the microphone and reload. |
| F4 | The answer is slow | The first answer can take a few seconds while the voice session warms up. Wait up to 10 seconds. Ask again in text mode if it does not arrive. |
| F5 | A source link does not open | Copy the link from the card. The sources are public sites and may be slow. The card still shows the source name (and, for a hadith, the grade). |
| F6 | The answer to a personal question gives a ruling | Report it to the team. This is a safety defect, not a feature. |
| F7 | The parent view is empty | Ask at least one question first, then reopen. The summary refreshes after the first session. |
| F8 | Arabic text looks wrong | Reload the page and use a current browser. If the letters still look disconnected, report it to the team. |

### For the operators (team only)

Run these checks every day from 7 to 22 Oct. Nothing here contains a key. Keys live only in the server's environment file.

| # | Problem | Action |
|---|---|---|
| O1 | **Daily smoke test** | Open the live link signed out. Press Try Al-Sadiq. Run one voice session and one text session. Open the parent view. Check `/api/health/`. Log the time and the result as in `docs/hackathon/DEPLOY-CHECKLIST.md`. |
| O2 | **Voice provider is failing (ElevenLabs; there is no automatic second voice, only the manual xAI rollback `TTS_PROVIDER=xai`)** | Read the agent log for the one error line (it names the cause, never the key) and the `voice_error` message the room received. Fix the cause (key, voice id, plan, credit) and restart the voice agent service so it re-reads the environment. If the credit is the cause, the demo guard already keeps the session going as text. Run a voice session to confirm. Exact restart command: `[confirm with the lead: compose file, env file and service name]`. |
| O3 | **Voice agent is up but silent** | Check the agent container logs for the provider error. Check the provider's credit balance. Then follow O2. Text mode keeps working while voice is down. |
| O4 | **LiveKit rooms do not connect** | Confirm the LiveKit Cloud project is the one the server points at, and that its URL and keys in the server's environment match. `[confirm project with the lead]` |
| O5 | **Demo rooms stuck busy** | The pool is 40 families (`DEMO_POOL_SIZE`) and the container entrypoint seeds missing ones on every deploy (`seed_demo --ensure`), so a fresh database never answers 503. The start limit is 120 an hour per IP, so a whole judging room behind one office IP fits (settings table in `docs/hackathon/DEMO-LOGIN.md`). A room frees itself when its 45-minute lease ends. `python manage.py demo_reset_expired` (in the backend container) wipes and re-seeds every family whose lease has ended; it is meant to run from cron every few minutes. `[confirm after merge: the cron entry, the exact container command, and how to clear a stuck lease key in Redis]` |
| O6 | **Credit caps** | Keep a spend alert on the OpenAI and ElevenLabs accounts. A judge test loop can burn credit. Rate limits on the demo start are already in the build. The ElevenLabs daily cap (`ELEVEN_DAILY_CHAR_CAP`, default 20000 characters, about 10 voice sessions) is the first limit a busy judging day hits: after it new sessions are text-only. Raise it for the day, with the credits to match (`docs/hackathon/DEMO-LOGIN.md`). |
| O7 | **Whole site is down** | Restart the stack from the server. If it cannot return, post the backup video link on the portal submission note and email info@IslamicAIch.org with the participation number. |
| O8 | **Live demo must stay up through 22 Oct** | No deploys during judging unless the smoke test fails. Freeze the branch after Tue 6 Oct 13:00. Hotfixes only with the lead's approval, with a smoke test straight after. |

## Rehearsal

Run this script twice before submission: once by someone on the team, and once by someone who has never seen the app, from a signed-out browser on a phone. Time it. If it takes longer than 3 minutes, cut steps 6 and 9.
