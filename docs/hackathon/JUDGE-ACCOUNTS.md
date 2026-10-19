# Judge accounts

Five persistent parent accounts for the judges (7–22 Oct 2026). Each parent has two linked children with a synthetic week of history, so a judge opens a product that has already been used. Judges can also start new voice and text sessions with these children.

These accounts are separate from the one-click demo pool (`DEMO-LOGIN.md`). The pool only touches `demo-…` usernames, so these accounts are never leased, reset or wiped by demo cleanup.

## Accounts

| Username | Who | Language | Shows |
|---|---|---|---|
| `judge1` … `judge5` | Parent "Judge N" | Parent page in Arabic or English (switch in the page) | Both children below |
| `judgeN-ar` | سلمى, girl, 7 | Arabic | The honesty week: a broken cup she hadn't owned up to → she tells her mother → she tells her teacher she forgot her homework |
| `judgeN-en` | Adam, boy, 11 | English | The friendship week: an unkind class group chat → he greets the new boy Sami → he works through jealousy about a friend's phone |

All five judges get the same family, each in their own copy (the lead approved this on 6 Oct). All names are made up. The Arabic text is the demo pool's honesty theme (`backend/demo/content.py`, `THEMES[0]`). The English text is `THEME_EN` in the same file.

For each child, the parent sees:

- **«الملخصات» / Insights:** 3 past sessions from the last 5 days, each with a parent summary and recommendations.
- **Values this week:** each session's values (for example honesty and honouring-parents, or avoiding-backbiting, spreading-salam and contentment).
- **Questions to discuss:** three per child, from the weekly summary.
- **Sources discussed:** cards built from reviewed bank items, stored as `ServedReference` rows that point at existing `ContentItem` ids. The seed contains no scripture text.
- **Quests:** one in each state: done, waiting for the parent's approval (so the judge can approve it), in progress and to do. Quest titles are in the child's language.
- **Badges:** awarded by the real badge engine (`evaluate_badges`), so some are earned and the rest are locked.

## Session limits

When the demo guards are on (production), judge children use their own caps in place of the demo ones:

| Env var | Default | Replaces |
|---|---|---|
| `JUDGE_DAILY_SESSIONS` | 30 per child per day | `DEMO_DAILY_SESSIONS` |
| `JUDGE_SESSION_START_PER_HOUR` | 20 per child per hour | `DEMO_SESSION_START_PER_HOUR` |

These limits still apply to judges as well:

- the session length (`DEMO_SESSION_MAX_SECONDS`);
- the shared ElevenLabs daily budget (`ELEVEN_DAILY_CHAR_CAP`): when it runs out, new sessions are text only, for judges too;
- the kill switch (`VOICE_MODE`);
- the always-on 30 starts per hour (`SESSION_START_USER_RATE`).

The `judge` username prefix is reserved: registration and "add child" refuse it, so nobody can sign up as a judge to get these caps.

## Run it on the server (lead)

The password file must live outside the repo, which is `/opt/alsadiq`, and it must never be committed. The prod backend container has no host folder mounted, so use a one-off `run` with a mount:

```bash
sudo mkdir -p /opt/alsadiq-secrets && sudo chmod 700 /opt/alsadiq-secrets
cd /opt/alsadiq
docker compose -f docker-compose.prod.yml run --rm --no-deps \
  -v /opt/alsadiq-secrets:/secrets \
  backend python manage.py seed_judges --count 5 --password-file /secrets/judge-accounts.txt
```

`run` uses the backend image that is currently built, so deploy this branch first. Keep the `-v` mount: without it the file is written inside the throwaway container and lost, and the next run quietly makes new passwords.

What it does:

- Writes `/opt/alsadiq-secrets/judge-accounts.txt` with mode 600, one line per account (username, password, role).
- Prints only a one-line summary. Passwords are never printed, logged or stored anywhere else.
- The file is owned by root, so read it with `sudo cat /opt/alsadiq-secrets/judge-accounts.txt`. Give each judge only their own three lines. Don't paste the file into chat, the brain or a PR.
- Needs migrations applied and the bank seeded (`seed_content`), which a normal deploy already does. With an empty bank the "Sources discussed" card is just empty.

## Reset

Run the same command again. Every run:

- wipes and re-seeds each judge child's history, including sessions the judges started (sessions, summaries, quests, badges, points and memory);
- restores the names, languages and links. Any extra child a judge added is unlinked;
- keeps the passwords: it reads them back from the file. A missing or new account gets a fresh one. A password a judge changed in the app goes back to the one in the file.

To give everyone new passwords and sign out every judge's open session, add `--rotate-passwords`. To add judges later, raise `--count`: existing accounts keep their passwords, and the new ones are added to the file.

The command refuses to take over a `judgeN` account that it did not create (wrong role or no `@judges.invalid` email).
