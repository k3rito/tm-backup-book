# telegram-r2-backup

A production-oriented Python 3.12+ service that streams media from a public Telegram channel directly into Cloudflare R2 without writing media files to local disk.

## What it does

- Reads Telegram messages in message-id order and resumes from the last committed message.
- Requires `TELEGRAM_SESSION_STRING`; there is no interactive login path in production or GitHub Actions.
- Skips messages without supported media.
- Streams media from Telegram in chunks and uploads to Cloudflare R2 using multipart upload.
- Avoids `download_media(file=bytes)` so the full file is never loaded into memory.
- Skips uploads when the object already exists in R2.
- Writes structured logs to `logs/app.log`.
- Persists resume state locally and synchronizes it to `state/progress.json` in Cloudflare R2.

## Supported media

- document
- video
- audio
- photo
- archive

## Project structure

```text
telegram-r2-backup/
├── src/
│   ├── main.py
│   ├── telegram_client.py
│   ├── r2_client.py
│   ├── transfer.py
│   ├── logger.py
│   └── utils.py
├── data/
│   ├── sessions/
│   └── state/
├── logs/
├── .env
├── .env.example
├── requirements.txt
├── README.md
├── .gitignore
├── docker-compose.yml
└── Dockerfile
```

## Requirements

- Python 3.12+
- Telegram API ID and API hash from https://my.telegram.org
- A Telegram user session for the target account
- Cloudflare R2 bucket and API credentials

## Environment variables

Copy `.env.example` to `.env` and fill the values:

```env
API_ID=
API_HASH=
CHANNEL_USERNAME=

R2_ENDPOINT=
R2_BUCKET=
R2_ACCESS_KEY=
R2_SECRET_KEY=

MAX_CONCURRENT_UPLOADS=3
```

Optional Telegram session support is available through:

```env
TELEGRAM_SESSION_STRING=
TELEGRAM_SESSION_NAME=telegram_r2_backup
```

## Install locally

1. Create a virtual environment.
2. Install dependencies.
3. Configure `.env`.
4. Run the service.

Example:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

## Telegram session

Telethon needs an authorized user session to read the channel and download its media.

`TELEGRAM_SESSION_STRING` is required. If it is missing or invalid, the app exits with a clear error.

## Cloudflare R2 setup

Use the standard R2 S3-compatible endpoint format:

```text
https://<account-id>.r2.cloudflarestorage.com
```

The bucket must already exist, and the access key must have permission to read object metadata and perform multipart uploads.

## Running with Docker

Build and start the container:

```bash
docker compose up --build
```

The compose file mounts the `data/` and `logs/` directories so progress and logs survive restarts.

## Runtime behavior

- Progress is stored in `data/state/progress.json` as:

```json
{
  "last_message_id": 12345
}
```

- After each successful or intentionally skipped message, the resume state advances.
- If the process stops mid-upload, the next run resumes from the last committed message and skips any object already present in R2.
- The current resume state is stored in Cloudflare R2 at `state/progress.json`, which survives GitHub Actions restarts.

## Logging

`logs/app.log` uses structured JSON lines and includes:

- timestamp
- file name
- size
- transfer speed
- success or failure status

## Notes

- Multipart uploads use 8 MB chunks on the R2 side.
- Telegram download chunking uses a smaller request size internally to respect Telegram API limits, while the R2 uploader buffers into 8 MB multipart parts.
- Concurrency is limited by `MAX_CONCURRENT_UPLOADS` to control load and reduce Telegram API pressure.
# tm-backup-book
