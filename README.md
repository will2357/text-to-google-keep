# text-to-google-keep

Create **one Google Keep note per line** of a UTF-8 text file (**CLI** or **Django + Inertia + React** web app).

- **Google OAuth (recommended for personal Gmail)** — real consent screen, official [Google Keep API](https://developers.google.com/workspace/keep/api/guides), refresh token in your OS keyring. **Labels are not supported** (the REST API does not expose labels on create).
- **gkeepapi (legacy)** — unofficial client with password / [master token](https://gkeepapi.readthedocs.io/en/latest/index.html#obtaining-a-master-token). Supports **labels** but often hits `BadAuthentication` on consumer accounts.

**Contents:** [GitHub Pages](#github-pages-static-site) · [Install](#install-uv) · [Google OAuth](#google-oauth-personal-gmail--official-api) · [gkeepapi / legacy](#authenticate-with-google-gkeepapi--legacy) · [Usage](#usage) · [Web app](#web-app-django) · [Development](#development)

## GitHub Pages (static site)

GitHub Pages serves **only static files** from `docs/` (landing page + links). It **cannot** run Django, PostgreSQL, or the Keep importer — use the [CLI](#install-uv) or [local Django app](#web-app-django) for that.

**One-time setup**

1. In GitHub: **Settings → Pages → Build and deployment**, set **Source** to **GitHub Actions** (not “Deploy from a branch”).
2. Push to **`main`** or **`master`**, or run workflow **Deploy GitHub Pages** manually (**Actions** tab).
3. After a green run, open the environment URL (e.g. `https://<user>.github.io/<repo>/`).

The workflow **`.github/workflows/deploy-github-pages.yml`** substitutes `__GITHUB_REPOSITORY__` in `docs/index.html` with `owner/repo` at deploy time. **`docs/.nojekyll`** disables Jekyll so paths behave predictably.

## Install (uv)

```bash
cd text-to-google-keep
uv venv
uv pip install -e .
```

## Google OAuth (personal Gmail — official API)

This path uses Google’s documented **OAuth 2.0** flow and **`https://www.googleapis.com/auth/keep`**. It is the supported way to act as **yourself** with a normal `@gmail.com` account, as long as Google lets your Cloud project use the Keep API (enable the API, consent screen, test users — below).

### One-time Google Cloud setup

1. Open [Google Cloud Console](https://console.cloud.google.com/) and create or pick a **project**.
2. **APIs & Services → Library** — enable **Google Keep API**.
3. **APIs & Services → OAuth consent screen** — choose **External** (unless you only use Workspace internal). Add your **Gmail address** under **Test users** while the app is in **Testing** (required until you publish and complete verification, if Google asks for it).
4. Under **Data Access / Scopes**, add the non-sensitive scope **`https://www.googleapis.com/auth/keep`** (or add it when Google prompts during client setup).
5. **APIs & Services → Credentials → Create credentials → OAuth client ID**  
   - **Desktop app** — download JSON. Use this for **`text-to-google-keep --oauth`** (browser opens on a random localhost port).  
   - **Web application** — add **Authorized redirect URI** exactly  
     `http://127.0.0.1:8000/oauth/callback/`  
     (match **host, port, and trailing slash** if you run Django elsewhere). Download JSON for the **Django** web UI “Sign in with Google” button.
6. Save the downloaded file on your machine, e.g. `~/client_secret.json`, and point the app at it with **`GOOGLE_KEEP_CLIENT_SECRETS`** or **`--client-secrets`**, or put a copy named **`client_secret.json`** in the directory from which you start the CLI or **`manage.py runserver`**.

### CLI (OAuth)

First run (browser opens; you approve access):

```bash
export GOOGLE_KEEP_CLIENT_SECRETS="$HOME/client_secret.json"
text-to-google-keep --oauth sample.txt
```

Later runs reuse the **refresh token** stored in the keyring (service **`text-to-google-keep-oauth`**, username = your email lowercased). Set **`GOOGLE_EMAIL`** if you use multiple accounts.

```bash
export GOOGLE_EMAIL='you@gmail.com'
text-to-google-keep --oauth shopping.txt
```

Clear only OAuth storage:

```bash
text-to-google-keep --oauth --reset-oauth --email you@gmail.com notes.txt
```

### Web UI (OAuth, Django)

1. Set **`GOOGLE_KEEP_CLIENT_SECRETS`** (or place **`client_secret.json`** in the process working directory) so Django can find the **Web** client JSON whose redirect URI matches **`/oauth/callback/`** on your dev server.
2. Run **`python manage.py runserver`** (see [Web app (Django)](#web-app-django) below), open **http://127.0.0.1:8000/**, click **Sign in with Google** in the header, complete consent.
3. On the form, check **Use Google OAuth**, enter the **same** email, leave password empty, then import.

### Keyring entries for OAuth

| Field | Value |
|--------|--------|
| **Service** | `text-to-google-keep-oauth` |
| **Username** | Google email, lowercased (same as gkeepapi normalization) |

Read the stored refresh bundle (JSON string) with:

```bash
uv run python -c "import keyring; print(keyring.get_password('text-to-google-keep-oauth', 'you@gmail.com') or '(none)')"
```

### If the Keep API returns HTTP 403

Your account must be allowed on the **OAuth consent screen** (Test users while in Testing). The Cloud project must have **Keep API** enabled. If Google changes policy for consumer accounts, check the [Keep API overview](https://developers.google.com/workspace/keep/api/guides) and Console errors for the exact message.

---

## Authenticate with Google (gkeepapi / legacy)

The gkeepapi path is **not** Google’s OAuth consent screen. Your password or **master token** is used only on your machine and, when applicable, stored in the **OS keyring** under service **`text-to-google-keep`**.

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

### Keyring: where this app stores the gkeepapi master token

(OAuth refresh tokens use service **`text-to-google-keep-oauth`** — see [Google OAuth](#google-oauth-personal-gmail--official-api) above.)

If gkeepapi password sign-in ever succeeds, this program saves the returned master token in your **OS keyring** so later runs can use `Keep.authenticate` without typing a password.

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

Use the **same** `--email` / `GOOGLE_EMAIL` you use for sign-in. That removes only the keyring entry for **`text-to-google-keep`** + that normalized email. In the **Django** web UI, use **Clear saved token** before sign-in for the same effect.

## Usage

```bash
source .venv/bin/activate   # optional
export GOOGLE_EMAIL='you@gmail.com'
text-to-google-keep notes.txt
text-to-google-keep notes.txt -l Shopping -l Inbox
text-to-google-keep notes.txt --blank-lines
```

Sign-in options, app passwords, master tokens, and errors are covered in **[Authenticate with Google (gkeepapi / legacy)](#authenticate-with-google-gkeepapi--legacy)** above.

## Web app (Django)

The web UI follows the same stack and styling approach as **Sython** (`~/src/sython`): **Django**, **inertia-django**, **Vite**, **React 19**, **Tailwind v4** (`frontend/src/index.css` `@theme` tokens), and **shadcn-style** UI primitives under `frontend/components/ui/`.

### Prerequisites

- **SQLite by default** (`db.sqlite3`; **`make migrate`** works with no database server). Set **`DJANGO_USE_SQLITE=false`** and uncomment **`DB_*`** in **`.env`** for PostgreSQL.
- **Node 20+** for Vite (`npm install`).

### First-time setup

```bash
cd text-to-google-keep
uv sync
cp .env.example .env   # edit DJANGO_SECRET_KEY; use Postgres only if you set DJANGO_USE_SQLITE=false + DB_*
npm install
npm run build          # writes frontend/dist for django-vite (ignored by git; run after clone)
uv run python manage.py migrate
```

### Run (two terminals)

**Terminal A — Vite dev server (HMR, same as Sython):**

```bash
npm run dev
```

**Terminal B — Django** (`DJANGO_DEBUG=True` enables `django-vite` dev mode against `http://localhost:5173`):

```bash
export DJANGO_SECRET_KEY=dev-only-change-me
# Postgres: export DJANGO_USE_SQLITE=false
uv run python manage.py runserver
```

Open **http://127.0.0.1:8000/**. OAuth redirect URIs must match this host/port (see [Google OAuth](#google-oauth-personal-gmail--official-api)).

### Production-style assets

```bash
npm run build
uv run python manage.py collectstatic --noinput
```

Use a real **`DJANGO_SECRET_KEY`**, **`DJANGO_DEBUG=False`**, and configure **`DJANGO_ALLOWED_HOSTS`** / HTTPS flags as for any Django deployment.

### PostgreSQL

Optional: set **`DJANGO_USE_SQLITE=false`** and uncomment **`DB_*`** in **`.env`** (`ttgk_dev` / **`ttgk`** / **`ttgk_local`**; test DB **`ttgk_test`**). One-time: **`make db-create`** ( **`scripts/postgres-local.sql`** as **`postgres`**; **`sudo -u postgres psql … -f scripts/postgres-local.sql`** on peer-auth systems), then **`migrate`**. SQLite mode uses **`db.sqlite3`** and **`db_test.sqlite3`** for tests. Import history lives in **`pages_importlog`** (`ImportLog` model).

## Development

```bash
uv sync
npm run typecheck
uv run python manage.py test
uv run text-to-google-keep --help
```
