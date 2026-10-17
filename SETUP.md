# 🌙 Night Patrol setup: phone → GitHub → README

Your phone sends one small request each morning. A GitHub Action logs the night,
redraws `assets/sleep.svg`, and commits it. No server, no third-party service.

```
phone wakes up ──POST──▶ GitHub repository_dispatch ──▶ sleep.yml ──▶ assets/sleep.svg updated
```

## 1. Make a token (once)

GitHub → Settings → Developer settings → **Fine-grained tokens** → Generate new token

- **Repository access:** Only select repositories → `Aman-Thaper/Aman-Thaper`
- **Permissions:** Repository → **Contents: Read and write** (nothing else)
- Give it a long expiry and copy it. Treat it like a password: it can only touch this one repo.

## 2a. iPhone (Apple Health, fully automatic)

Make a shortcut called **Log Sleep** in the Shortcuts app:

1. **Find Health Samples** where *Type* is *Sleep Analysis*, *Start Date* is *in the last 1 day*,
   and *Value* is not *In Bed* (and not *Awake*). This keeps only real sleep stages.
2. **Get Details of Health Samples** → *Duration*.
3. **Calculate Statistics** → *Sum*.
4. **Calculate** → divide by 60 (the sum comes out in minutes; add a temporary **Show Result**
   the first time to check. If you see something like 25000, it's seconds, so divide by 3600 instead).
5. **Round Number** → hundredths.
6. **Get Contents of URL**
   - URL: `https://api.github.com/repos/Aman-Thaper/Aman-Thaper/dispatches`
   - Method: **POST**
   - Headers:
     - `Authorization` → `Bearer YOUR_TOKEN`
     - `Accept` → `application/vnd.github+json`
   - Request Body: **JSON**
     - `event_type` (Text) → `sleep`
     - `client_payload` (Dictionary) → `hours` (Number) → *Rounded Number*

Then **Automation → + → Sleep → Wake Up** (or **Alarm → Is Stopped**), pick **Log Sleep**,
and set it to **Run Immediately**. Done: every morning the card updates by itself.

Works with anything that writes sleep into Apple Health: Apple Watch, the iPhone's own
sleep schedule, Oura, Fitbit, AutoSleep, and so on.

## 2b. Android

Android's Health Connect keeps sleep data on the phone and has no web API, so pick one:

- **One tap each morning:** install *HTTP Shortcuts* (free, open source) and make a POST to the
  same URL, with the same headers and body as above. Add it as a home-screen widget.
- **Zero apps:** open the GitHub mobile app → this repo → Actions → *Night Patrol* → **Run workflow**
  and type your hours.
- **Fully automatic:** if your sleep comes from Fitbit, Oura or Whoop, those have cloud APIs.
  A scheduled workflow can pull from them directly. Ask, and that can be wired in.

## 3. Test it from your laptop

```bash
curl -X POST https://api.github.com/repos/Aman-Thaper/Aman-Thaper/dispatches \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -d '{"event_type":"sleep","client_payload":{"hours":6.5}}'
```

Check the Actions tab: a *Night Patrol* run should appear and commit a new card within a minute.

## Tweaks

- Change the sleep goal: `GOAL` in `scripts/sleep_card.py`.
- Change the quips: the `verdict()` function in the same file.
- Change the header text or spider paths: edit `scripts/make_assets.py`, then run
  `python scripts/make_assets.py`.
- The "last night" badge reads `data/sleep-badge.json` from the `main` branch.
  If your default branch is `master`, change `main` to `master` in that badge URL in the README.
