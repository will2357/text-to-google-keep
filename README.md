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

If password / App Password sign-in fails (including **`BadAuthentication`**), you need a **master token**: a long secret string gkeepapi can pass to `Keep.authenticate(email, token)`. It often starts with **`aas_et/`** (treat it like a password).

#### How to obtain one (upstream flow)

gkeepapi’s auth stack ultimately uses **[gpsoauth](https://github.com/simon-weber/gpsoauth)**. Follow the **maintained** instructions here (they change when Google changes things):

1. **[gkeepapi docs — “Obtaining a Master Token”](https://gkeepapi.readthedocs.io/en/latest/index.html#obtaining-a-master-token)** — overview and a Docker-based recipe you can copy from the current page (do not trust stale copies in random blogs).
2. **[gpsoauth — “Alternative flow”](https://github.com/simon-weber/gpsoauth#alternative-flow)** — the usual inputs are your **email**, a **Google OAuth token** (from a browser session / account login flow; *not* the final master token), and an **Android ID** string as described there. The library exchanges those for the **master token** you paste into this app.

You will need to get the OAuth token and Android ID from steps described in that gpsoauth section (often involving browser devtools or a helper script). **Google does not document this for end users**; flows break without warning. Only run code you understand; never paste a master token into untrusted sites.

#### After you have the token

**CLI** (one run):

```bash
text-to-google-keep sample.txt --token 'aas_et/…YOUR_TOKEN…'
```

Or for several commands in one shell:

```bash
export KEEP_MASTER_TOKEN='aas_et/…YOUR_TOKEN…'
text-to-google-keep sample.txt
```

**Web UI:** paste the full token into **Master token** and submit the form.

When you authenticate **only** via `--token` / `KEEP_MASTER_TOKEN` / the web **Master token** field, this app **does not** overwrite the keyring entry from that path. The keyring is updated only after a successful **password** sign-in (see [Order of sign-in](#order-of-sign-in-cli-and-web)).

### Keyring: where this app stores the master token

If password sign-in ever succeeds, this program saves the returned master token in your **OS keyring** so later runs can use `Keep.authenticate` without typing a password.

| What | Value |
|------|--------|
| **Keyring “service”** | `text-to-google-keep` (exact string) |
| **Keyring “username” / account** | Your Google email with **leading/trailing spaces removed and lowercased** (e.g. `You@Gmail.com` → `you@gmail.com`) |

The same email normalization applies when you use **`--reset`**: pass the same address you use for sign-in.

### Keyring: read the saved token (same machine)

From the **repository root**, with dependencies installed (`uv sync` or your venv active), replace the email with yours:

```bash
uv run python -c "import keyring; print(keyring.get_password('text-to-google-keep', 'you@gmail.com') or '(no token stored for this email)')"
```

If you use a venv and `keyring` is on `PATH`:

```bash
python -c "import keyring; print(keyring.get_password('text-to-google-keep', 'you@gmail.com') or '(no token stored)')"
```

**Linux (GNOME / Secret Service):** Python’s default backend stores items with attributes `service`, `username`, and `application` (`Python keyring library`). If you have **`secret-tool`** (from `libsecret`):

```bash
secret-tool lookup application 'Python keyring library' service 'text-to-google-keep' username 'you@gmail.com'
```

**GUI:** search your password manager for **`text-to-google-keep`** (e.g. **Passwords and Keys / Seahorse** on GNOME, **Keychain Access** on macOS, **Credential Manager** on Windows). The entry label is often like `Password for 'you@gmail.com' on 'text-to-google-keep'`.

### Keyring: delete the saved token without the CLI `--reset` flag

Same email normalization as above:

```bash
uv run python -c "import keyring; keyring.delete_password('text-to-google-keep', 'you@gmail.com')"
```

If nothing was stored, Python raises `PasswordDeleteError` — that is normal.

### “Browser verification” / `BrowserLoginRequiredException`

If the library reports that Google wants **browser verification**, open the URL it prints, complete verification in the browser, then obtain a **master token** via the [gpsoauth alternative flow](https://github.com/simon-weber/gpsoauth#alternative-flow) and use **`--token`** / **`KEEP_MASTER_TOKEN`** / the web **Master token** field—password-only may not proceed until Google is satisfied.

### Clear stored credentials (built-in)

```bash
text-to-google-keep --reset notes.txt
```

Use the **same** `--email` / `GOOGLE_EMAIL` you use for sign-in. That removes only the keyring entry for **`text-to-google-keep`** + that normalized email. On the **web** UI, use **Clear saved token** for the same effect.

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
