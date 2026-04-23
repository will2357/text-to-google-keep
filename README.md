# keep-lines-to-keep

Create **one Google Keep note per line** of a UTF-8 text file. Labels are created in Keep if they do not already exist.

Uses [gkeepapi](https://github.com/kiwiz/gkeepapi) (unofficial Keep client), not Google’s official API.

## Install (uv)

```bash
cd keep-lines-to-keep
uv venv
uv pip install -e .
```

## Usage

```bash
source .venv/bin/activate   # optional
export GOOGLE_EMAIL='you@gmail.com'
keep-lines notes.txt
keep-lines notes.txt -l Shopping -l Inbox
keep-lines notes.txt --blank-lines
```

**First run:** you are prompted for your Google password (use an [App password](https://myaccount.google.com/apppasswords) if 2-Step Verification is on). A **master token** is then stored in your OS keyring.

**If you see `BadAuthentication`:** password login is blocked for many accounts. Obtain a master token with any `gpsoauth` helper (e.g. exchange an `oauth_token` cookie from Google’s account flow) and run:

```bash
keep-lines notes.txt --token 'aas_et/...'
# or
export KEEP_MASTER_TOKEN='aas_et/...'
keep-lines notes.txt
```

**Reset saved token:**

```bash
keep-lines --reset notes.txt
```

## Publish this repo

```bash
cd keep-lines-to-keep
git init
git add .
git commit -m "task: initial keep-lines CLI"
```

Create an empty repository on GitHub/GitLab, then `git remote add origin …` and `git push -u origin main`.
