# text-to-google-keep

Create **one Google Keep note per line** of a UTF-8 text file. Labels are created in Keep if they do not already exist.

Uses [gkeepapi](https://github.com/kiwiz/gkeepapi) (unofficial Keep client), not Google’s official API.

## Install (uv)

```bash
cd text-to-google-keep
uv venv
uv pip install -e .
```

## Authenticate with Google

Sign-in follows [gkeepapi](https://github.com/kiwiz/gkeepapi): it is **not** a “Sign in with Google” OAuth consent screen. Your password or **master token** is used only on your machine and, when applicable, stored in the **OS keyring** (same idea as other desktop mail/Keep clients).

### Order of sign-in (CLI and web)

1. **Master token** if you set `--token` / `KEEP_MASTER_TOKEN` (CLI) or paste a token in the web form (non-empty value wins over the keyring for this attempt).
2. Otherwise the **saved master token** for that email from the keyring (after a previous successful login).
3. Otherwise **password**: CLI prompts; web uses the password field. On success, gkeepapi returns a master token and this app **saves it to the keyring** so later runs can skip the password.

Saved tokens are per email; use **`--reset`** (CLI) or **Clear saved token** (web) to delete the stored token for that address before trying again.

### Password

- Use your normal Google account **email** and account **password** only if Google still allows that kind of sign-in for your account.
- With **[2-Step Verification](https://myaccount.google.com/signinoptions/two-step-verification)** on, use a **[Google App Password](https://myaccount.google.com/apppasswords)** (16 characters) in the password field or prompt instead of your regular password—Google treats that as a separate credential for “mail / less secure clients” style access.

### Master token (when the password path fails)

Many accounts see **`BadAuthentication`** or similar: Google blocks plain password login for Keep via this API. Then you need a **master token** (often shown as a string starting with `aas_et/`).

Typical approach used by the community: run a small **gpsoauth**-based helper (see gkeepapi’s README and issues) that performs Google’s **OAuth / device** style exchange so you end up with that token—often by copying a token or cookie from a browser session after you sign in to Google in the browser. **This is fragile and undocumented by Google**; treat any script you use like a password.

**CLI:** `--token 'aas_et/...'` or:

```bash
export KEEP_MASTER_TOKEN='aas_et/...'
text-to-google-keep notes.txt
```

Using only a supplied or keyring **master token** does not write a new token; the keyring is updated after a successful **password** sign-in when Google returns a new master token (see order above).

**Web:** paste the token into **Master token**. If the keyring already has a valid token for that email, password can stay empty; otherwise provide password or token as required by your account.

### “Browser verification” / `BrowserLoginRequiredException`

If the library reports that Google wants **browser verification**, open the URL it prints, complete verification in the browser, then obtain a **master token** via a helper as above and use **`--token`** or the web form—password-only may not proceed until Google is satisfied.

### Clear stored credentials

```bash
text-to-google-keep --reset notes.txt
```

Use the same email you will use on the next run; only that email’s saved token is removed from the keyring.

## Usage

```bash
source .venv/bin/activate   # optional
export GOOGLE_EMAIL='you@gmail.com'
text-to-google-keep notes.txt
text-to-google-keep notes.txt -l Shopping -l Inbox
text-to-google-keep notes.txt --blank-lines
```

Sign-in options, app passwords, master tokens, and errors are covered in **[Authenticate with Google](#authenticate-with-google)** above.

## Web UI

Local [Flask](https://flask.palletsprojects.com/) app: paste lines or upload a UTF-8 file, same auth rules as the CLI. Listens on **127.0.0.1:8765** by default (not exposed to your LAN).

```bash
text-to-google-keep-web
# open http://127.0.0.1:8765
```

Optional: `FLASK_SECRET_KEY` for session signing if you change `--host`/`--port`; treat remote access like handing someone your Google session.

## Publish this repo

```bash
cd text-to-google-keep
git init
git add .
git commit -m "task: initial text-to-google-keep CLI"
```

Create an empty repository on GitHub/GitLab, then `git remote add origin …` and `git push -u origin main`.
