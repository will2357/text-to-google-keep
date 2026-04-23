# text-to-google-keep

Create **one Google Keep note per line** of a UTF-8 text file (CLI or local web UI). Labels are created in Keep if missing. Uses [gkeepapi](https://github.com/kiwiz/gkeepapi) (unofficial client, not Google’s official API).

## Install (uv)

```bash
cd text-to-google-keep
uv venv
uv pip install -e .
```

## Authenticate with Google

Sign-in is **not** a Google OAuth consent screen. Your password or **master token** is used only on your machine and, when applicable, stored in the **OS keyring** (same idea as other desktop clients using gkeepapi).

### Order of sign-in (CLI and web)

1. **Master token** if you set `--token` / `KEEP_MASTER_TOKEN` (CLI) or paste a token in the web form (non-empty value wins over the keyring for this attempt).
2. Otherwise the **saved master token** for that email from the keyring (after a previous successful login).
3. Otherwise **password**: CLI prompts; web uses the password field. On success, gkeepapi returns a master token and this app **saves it to the keyring** so later runs can skip the password.

Saved tokens are per email; use **`--reset`** (CLI) or **Clear saved token** (web) to delete the stored token for that address before trying again.

### Password

- Use your normal Google account **email** and account **password** only if Google still allows that kind of sign-in for your account.
- With **[2-Step Verification](https://myaccount.google.com/signinoptions/two-step-verification)** on, try a **[Google App Password](https://myaccount.google.com/apppasswords)** (16 characters, no spaces) in the password field or prompt instead of your regular password.

### `BadAuthentication` even with an App Password

**Very common.** Google often rejects password-based sign-in for **Keep** for this unofficial client, and the error looks like `('BadAuthentication', None)` whether you used a normal password or an App Password. That does **not** mean your App Password is wrong—it usually means you must use a **master token** instead. Go to **[Master token](#master-token-when-the-password-path-fails)** below.

### Master token (when the password path fails)

If password / App Password sign-in fails (including **`BadAuthentication`**), you need a **master token** (often a string starting with `aas_et/`).

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

Local [Flask](https://flask.palletsprojects.com/) app: paste lines or upload a UTF-8 file. **Authentication is the same as the CLI** (see [Authenticate with Google](#authenticate-with-google)).

### Run the web server (recommended: `uv run`)

From the **repository root** (the directory that contains `pyproject.toml`):

```bash
cd text-to-google-keep          # or: cd /path/to/your/clone
uv sync                         # installs deps + this project into .venv
uv run text-to-google-keep-web   # note: space after "uv run", not a hyphen
```

Leave that terminal open. In a browser, open:

**http://127.0.0.1:8765**

The server listens on **127.0.0.1** (localhost only) and port **8765** by default. Stop it with **Ctrl+C** in the same terminal.

**Change host or port** (see all options):

```bash
uv run text-to-google-keep-web --help
uv run text-to-google-keep-web --host 127.0.0.1 --port 9000
```

### Run after `uv pip install -e .` (activated venv)

If you followed [Install (uv)](#install-uv) and ran `source .venv/bin/activate`, you can start the app **without** `uv run`:

```bash
text-to-google-keep-web
# then open http://127.0.0.1:8765
```

### Optional: `FLASK_SECRET_KEY`

If you change `--host` / `--port` so other machines can reach the app, set `FLASK_SECRET_KEY` to a long random string for session signing, and treat network exposure like handing someone your Google session.

## Development

```bash
uv sync
uv run text-to-google-keep --help
uv run text-to-google-keep-web --help
```

Use **`uv run text-to-google-keep-web`** (see [Web UI](#web-ui) above) to start the server during development.
