# Task 05 UI review

Owner: Abdulrahman Mahmalji. Branch: `hk/05-web-ui`.

Open [the comparison gallery](index.html) to review every child page, the parent pages, account screens, and the source-card session preview. No PR will be opened until the owner verifies the work.

The before captures use commit `e7c98a3`. The after captures use the task 05 implementation with the verification fixes. Accounts, activity and names shown in these screenshots are synthetic local demo data. Passwords, keys and runtime fixtures are excluded from the repository.

## Verification

| Check | Result |
| --- | --- |
| Child Home, Quests, Achievements and Settings | Captured at desktop and phone widths, light and dark |
| Parent Children, Insights, Alerts, Summary and Settings | Captured at desktop and phone widths, light and dark |
| Login, Register, Forgot Password, Reset Password and Add Child dialog | Captured at both widths |
| Horizontal overflow | None in the captured after pages at 1440 × 1000 and 390 × 844 CSS pixels |
| Reference delivery | Mocked LiveKit `DataReceived` event reached the actual decoder, subscriber and card UI in about 315 ms, including browser tool overhead |
| Source rail | Three-card limit, repeated-reference promotion, invalid-event rejection and reset on new session verified |
| Audio control | Neutral test tone played and paused; starting another clip stopped the first; missing clip showed “Recitation unavailable” |
| Exit dialog | Tab and Shift+Tab stayed in the dialog; Escape closed it and restored previous focus |
| Add Child dialog | Keyboard focus returned to the Add Child button after Escape; no new account submitted |
| Regression scripts | Source checks passed; all 21 session cleanup and dialog focus cases passed, including realistic disconnect rejection |
| Frontend lint and build | Passed; existing large application/avatar bundle warning remains |
| Final independent review | No blocking issues in the verification fixes through `b385959`; citation bounds, grading policy and failed-room cleanup findings resolved |

Run the checks from `frontend/`:

```sh
node scripts/check-source-cards.mjs
node scripts/check-session-startup.mjs
npm run lint
npm run build
```

Source validation uses numeric Hafs verse bounds counted from the official [Quranpedia mushaf data](https://quranpedia.net/dumps), file `mushafs-1.json.gz`, version 2026-10-04. Only numeric bounds enter the frontend. Actual Quran and hadith text still must come from the approved, seeded or reviewed content bank.

## Review and integration still needed

- Owner visual approval is pending. No PR, merge or deployment has been performed.
- The local session preview replaces LiveKit transport and session allocation outside the repo. Placeholder source text and a neutral audio tone verify UI behavior. A real task 03 agent, retrieved Uthmani text, Saheeh International translation and recitation recording have not been verified end to end here.
- These are **web** before/after captures. The mobile palette and scale were checked against `mobile/src/theme/tokens.js`; a native Expo device/simulator comparison remains pending. The old `docs/mobile-uiux-screenshots/` images are production web audit captures, not evidence of native Expo rendering.
- Arabic UI translation and full RTL are the optional stretch item and remain unimplemented. Source-card Arabic text itself uses RTL and Amiri.
- The avatar directory was not edited during this Codex verification pass. Majd owns avatar animation; its stage sizing contract is documented in `VoiceMode.jsx`.

Long pages and the source rail scroll; viewport images do not include all off-screen content. The QA toolbar is visible only in the isolated mocked session captures and is not shipped with the app.
