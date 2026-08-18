# Hoyo Auto

Personal HoYoLAB automation for **Genshin Impact** and **Honkai: Star Rail** only.

This tool runs two tasks for each enabled game:

1. **Daily check-in** on HoYoLAB
2. **Automatic discovery and redemption** of live promo codes

It is intended for **personal use on a single account**. It does not support ZZZ, stamina/resin tracking, Discord bots, web UI, or multi-user management.

## Supported games

| Game | Check-in | Code redemption |
|------|----------|-----------------|
| Genshin Impact | Yes | Yes |
| Honkai: Star Rail | Yes | Yes |

## Requirements

- Python 3.11+
- A HoYoLAB account with Genshin and/or HSR linked

## Setup

1. Clone this repository and enter the project directory.

2. Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

3. Copy the example environment file and add your credentials:

```bash
cp .env.example .env
```

4. Edit `.env` and set `HOYOLAB_COOKIE`.

### Required credentials

Your cookie string must include at minimum:

| Field | Required for |
|-------|----------------|
| `ltoken_v2`, `ltuid_v2`, `ltmid_v2` | Daily check-in |
| `cookie_token_v2`, `account_mid_v2`, `account_id_v2` | Code redemption |

**How to obtain cookies**

1. Log in at [HoYoLAB](https://www.hoyolab.com) in your browser.
2. Open DevTools → Application → Cookies for `hoyolab.com`.
3. Copy the required values into a single semicolon-separated string in `.env`.

Reference guide: [HoYoLab Auto cookie guide](https://gist.github.com/torikushiii/59eff33fc8ea89dbc0b2e7652db9d3fd)

**Security notes**

- Never commit `.env` or cookie values to Git.
- Logs never print full cookie strings.
- Cookies expire — if authentication fails, refresh your cookie in `.env`.

## Usage

Run everything once (check-in + code redemption):

```bash
hoyo-auto run
```

Run only check-in:

```bash
hoyo-auto checkin
```

Run only code discovery/redemption:

```bash
hoyo-auto redeem
```

Run on a schedule (daily check-in + periodic code polling):

```bash
hoyo-auto schedule
```

Schedule defaults (override in `.env`):

- Check-in: `00:05` local time daily (`CHECKIN_HOUR`, `CHECKIN_MINUTE`)
- Code polling: every 15 minutes (`REDEEM_INTERVAL_MINUTES`)

## Local code cache

Processed codes are stored in `data/state.json` (configurable via `STATE_DIR`).

Behavior:

1. **First run:** all currently active codes from the code source are saved to cache **without redemption**. This prevents mass-redeeming historical codes on a fresh install.
2. **Later runs:** only newly discovered codes are submitted.
3. **Permanent results** (success, expired, invalid, already redeemed) are cached and not retried.
4. **Temporary failures** (network errors, API busy, cooldown) are **not** cached and may be retried on the next run.

Code sources (same as the reference implementation):

- Genshin: `https://api.ennead.cc/mihoyo/genshin/codes`
- HSR: `https://api.ennead.cc/mihoyo/starrail/codes`

## Logging

Example log outcomes:

- `already checked in today` — normal, not an error
- `check-in successful` — signed in and received today's reward
- `found N new code(s) to redeem` — new code discovered
- `redeemed CODE` — redemption succeeded
- `already redeemed` / `expired` / `invalid` — permanent outcome, won't retry
- `Cookie is invalid or expired` — refresh your `.env` cookie

## GitHub Actions (daily automation)

Run check-in and code redemption once per day on GitHub-hosted runners.

1. Push this repository to GitHub.
2. Add repository secret **`HOYOLAB_COOKIE`** (Settings → Secrets and variables → Actions) with the same cookie string used in `.env`.
3. The workflow in `.github/workflows/daily.yml` runs daily at **07:00 ICT (UTC+7)** and can also be triggered manually (**Actions → Daily HoYoLAB Automation → Run workflow**).

Processed redemption codes are cached between runs via GitHub Actions cache (`data/state.json`).

## Testing

Tests use mocked HTTP responses and do not contact HoYoLAB or redeem real codes:

```bash
pytest
```

## Common errors

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| `Cookie is invalid or expired` | Session expired | Refresh `HOYOLAB_COOKIE` in `.env` |
| `Redemption disabled` | Missing token cookie fields | Add `cookie_token_v2`, `account_mid_v2`, `account_id_v2` |
| `no linked game account found` | Game not linked to HoYoLAB | Link Genshin/HSR in HoYoLAB settings |
| Captcha required | HoYoLAB security challenge | Visit game records on HoYoLAB to solve captcha |
| Code redeemed on wrong server | Region mismatch | Ensure cookie matches the account's server |

## Project layout

```
hoyo_auto/
  auth.py          # Cookie parsing and account lookup
  checkin.py       # Check-in orchestration
  client.py        # HTTP client
  config.py        # Environment settings
  redeem.py        # Code discovery orchestration
  state.py         # Local code cache
  games/
    genshin.py     # Genshin check-in + redeem
    hsr.py         # HSR check-in + redeem
tests/             # Mocked unit tests
```

## Disclaimer

This project automates official HoYoLAB endpoints for personal convenience. Use at your own risk. It is not affiliated with or endorsed by HoYoverse.

## Reference

Implementation patterns are based on [torikushiii/hoyolab-auto](https://github.com/torikushiii/hoyolab-auto), scoped down to Genshin + HSR check-in and code redemption only.
