# svipr

> ~ everything is temporary, and encrypted at rest ~

**svipr** is a lightweight, self-hosted, temporary file-sharing service. Inspired by tools like `temp.sh` and `transfer.sh`, it is designed with a "geek-first" terminal aesthetic. 

The core philosophy of svipr is **zero plaintext at rest**. Files are encrypted on the backend using streaming AES-GCM (via Cobblestone) before they ever touch the disk. The encryption key is stored separately from the encrypted file. When a file expires, the ciphertext, the key, and the metadata are securely deleted together.

## Features

*   **Streaming Encryption:** Large files (up to 4 GB by default) are encrypted in chunks on the fly, preventing memory exhaustion and ensuring plaintext is never written to disk.
*   **Expiration Cleanup:** Files are automatically deleted after a configurable number of days.
*   **Access Keys (Optional):** Lock down your instance for private groups. When enabled, users must provide a valid key to upload.
*   **Geek Aesthetic:** Monospace fonts, dark mode, ASCII banners, and a scriptable API.
*   **API First:** Fully usable via `curl`, complete with copy-paste examples on the frontend.

## Tech Stack

*   **Backend:** Python 3.10+, FastAPI, Uvicorn
*   **Encryption:** `cryptography` (Cobblestone)
*   **Rate Limiting:** `slowapi`
*   **Frontend:** Vanilla TypeScript, Vite
*   **Styling:** Custom CSS (JetBrains Mono, self-hosted via `@fontsource`)

## Project Structure

    svipr/
    ├── main.py              # FastAPI application and routes
    ├── config.py            # Pydantic settings (loads from .env)
    ├── storage.py           # File streaming and encryption logic
    ├── meta.py              # Metadata handling (filenames, timestamps)
    ├── cleanup.py           # Background task for deleting expired files
    ├── limiter.py           # slowapi rate limiter configuration
    ├── keys.json            # Valid access keys (if WITH_KEY=1)
    ├── tests/               # Pytest suite
    ├── frontend/            # Vanilla TS + Vite source
    └── static/              # Built frontend assets (served by FastAPI)

## Quick Start (Development)

### 1. Backend Setup

    # Clone the repository
    git clone https://github.com/yourusername/svipr.git
    cd svipr

    # Create and activate a virtual environment
    python -m venv venv
    source venv/bin/activate  # On Windows use: venv\Scripts\activate

    # Install dependencies
    pip install -r requirements.txt

*(Note: Ensure you have a `requirements.txt` generated via `pip freeze > requirements.txt`)*

### 2. Configuration

Copy the example environment file:

    cp .env.example .env

Edit `.env` to match your preferences:

    APP_NAME=Svipr
    UPLOAD_DIR=uploads
    MAX_FILE_SIZE=4294967296
    RETENTION_DAYS=3
    UPLOAD_RATE_LIMIT=3/30 minutes
    WITH_KEY=0

### 3. Frontend Setup

    cd frontend
    npm install
    npm run build
    cd ..

### 4. Run the Server

    fastapi dev main.py

Open `http://127.0.0.1:8000` in your browser.

## API Usage

Svipr is designed to be scripted. No tokens, no auth headers—just a file ID.

### Upload a file

    curl -F "file=@test.txt" https://svipr.example/upload

**Response:**

    {
      "id": "Xk3f...",
      "size": 12,
      "url": "/download/Xk3f..."
    }

### Upload and get the link directly

Requires `jq` to parse the JSON response.

    curl -s -F "file=@test.txt" https://svipr.example/upload | jq -r .url

### Download (preserves original filename)

The `-O -J` flags tell curl to save the file using the name provided in the `Content-Disposition` header.

    curl -O -J https://svipr.example/download/Xk3f.../raw

### Pipe output directly

Use `file=@-` to read from standard input.

    echo "ephemeral note" | curl -F "file=@-" https://svipr.example/upload

## Private Groups (Access Keys)

To restrict uploads to authorized users, set `WITH_KEY=1` in your `.env`.

1.  Add valid keys to `keys.json`:

    {
      "keys": [
        "svipr-7a9f2b4c8d",
        "svipr-3e1f5a9b2c"
      ]
    }

2.  When `WITH_KEY=1`, the frontend will display an `[ AUTH REQUIRED ]` input box.
3.  API users must pass the key via the `X-Svipr-Key` header:

    curl -H "X-Svipr-Key: svipr-7a9f2b4c8d" -F "file=@test.txt" https://svipr.example/upload

*(Note: Valid keys bypass the IP-based upload rate limit, allowing teams behind a single NAT IP to upload freely).*

## Production Deployment

### Security Considerations

*   **Do not run Uvicorn directly.** Use a reverse proxy like Nginx or Caddy to handle SSL/TLS.
*   **Keys on disk:** The encryption keys are stored in `uploads/keys/`. If an attacker gains access to your disk, they can read the files. For maximum security, store the keys in a separate directory with strict permissions, or encrypt them with a master key from your environment variables.
*   **Nginx Rate Limiting:** The `slowapi` rate limit is in-memory and single-process. For production, configure Nginx to drop scripted floods before they reach Python.

### Sample Systemd Service

    [Unit]
    Description=Svipr Temporary File Sharing
    After=network.target

    [Service]
    User=www-data
    Group=www-data
    WorkingDirectory=/var/www/svipr
    Environment="PATH=/var/www/svipr/venv/bin"
    ExecStart=/var/www/svipr/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000

    [Install]
    WantedBy=multi-user.target

## License

MIT License. See `LICENSE` for details.
