# text-to-google-keep

Create **one Google Keep note per line** of a UTF-8 text file. Labels are created in Keep if they do not already exist.

Uses [gkeepapi](https://github.com/kiwiz/gkeepapi) (unofficial Keep client), not Google’s official API.

## Install (uv)

```bash
cd text-to-google-keep
uv venv
uv pip install -e .
```

## Usage

```bash
source .venv/bin/activate   # optional
export GOOGLE_EMAIL='you@gmail.com'
text-to-google-keep notes.txt
text-to-google-keep notes.txt -l Shopping -l Inbox
text-to-google-keep notes.txt --blank-lines
```

**First run:** you are prompted for your Google password (use an [App password](https://myaccount.google.com/apppasswords) if 2-Step Verification is on). A **master token** is then stored in your OS keyring.

**If you see `BadAuthentication`:** password login is blocked for many accounts. Obtain a master token with any `gpsoauth` helper (e.g. exchange an `oauth_token` cookie from Google’s account flow) and run:

```bash
text-to-google-keep notes.txt --token 'aas_et/...'
# or
export KEEP_MASTER_TOKEN='aas_et/...'
text-to-google-keep notes.txt
```

**Reset saved token:**

```bash
text-to-google-keep --reset notes.txt
```

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
