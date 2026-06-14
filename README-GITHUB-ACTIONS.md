# GitHub Actions Setup

This project can run from GitHub Actions on a 15-minute schedule or manually with `workflow_dispatch`.

## GitHub Secrets

Add these secrets to the repository:

- `API_ID`
- `API_HASH`
- `CHANNEL_USERNAME`
- `R2_ENDPOINT`
- `R2_BUCKET`
- `R2_ACCESS_KEY`
- `R2_SECRET_KEY`
- `MAX_CONCURRENT_UPLOADS`
- `TELEGRAM_SESSION_STRING` (or legacy `TELEGRAM_STRING_SESSION`)

Notes:

- A Telegram session is required. The workflow reads `TELEGRAM_SESSION_STRING` first, then falls back to legacy `TELEGRAM_STRING_SESSION`.
- `MAX_CONCURRENT_UPLOADS` should usually stay at `3` unless you have a specific throughput reason to change it.

## Session String Generation

Generate a Telegram StringSession locally once, then store it in the `TELEGRAM_SESSION_STRING` secret.

One practical approach is to run a short Telethon script locally, authenticate once, and print the string session. Keep the string secret and never commit it to the repository.

## Workflow Execution

The workflow file is:

- [.github/workflows/backup.yml](.github/workflows/backup.yml)

It runs:

- manually via `workflow_dispatch`
- every 15 minutes via cron

The job:

- installs Python 3.12
- installs `requirements.txt`
- launches `python src/main.py`

## Resume Mechanism

Resume state is synchronized to Cloudflare R2 at:

- `state/progress.json`

Startup flow:

1. Download `state/progress.json` from R2 if it exists.
2. If it is missing, start from message id `0`.
3. After each successfully processed message, upload the updated progress state back to R2.

This makes the backup job resilient to GitHub Actions restarts and ephemeral runners.
