# WhatsApp Automation Setup (WAHA + Python)

This project sets up **WAHA (WhatsApp HTTP API)** in Docker along with a **Python Flask service** that:
- Starts WhatsApp sessions automatically on boot.
- Receives webhook events from WAHA.
- Forwards incoming messages to `ntfy` (except from blocked senders).
- Supports both delayed start (default 2 minutes) and instant start (`--instant`).

---

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/mhamidjamil/waha
cd waha
````

---

### 2. Create .env file by copying .env.example

```bash
cp .env.example .env
```

---

### 3. Start WAHA (Docker)

Make sure Docker is installed, then run:

```bash
docker-compose up -d
```

This will start WAHA at `http://localhost:5002`.

---

### 4. Run Python Flask Service

Install dependencies:

```bash
pip install -r requirements.txt
```

Run with default 2-minute delayed start:

```bash
python whatsapp_starter.py
```

Run with **instant start** (skip delay):

```bash
python whatsapp_starter.py --instant
```

---

## ⚡ Running Python Script on Windows Startup

You can make the Flask service run automatically whenever Windows starts.

1. Press **`Win + R`**, type:

   ```
   shell:startup
   ```

   and hit Enter.
   This opens the **Startup folder**.

2. Create a new **Shortcut** inside this folder:

   * Right-click → New → Shortcut.
   * Enter the command to run your script, for example:

     ```
     python "C:\path\to\your\repo\whatsapp_starter.py"
     ```
   * Name it (e.g., `WhatsApp Starter`).

3. Save and reboot. The script will now run automatically at startup 🎉

---

## 🛠 Features

* WAHA runs in Docker (`docker-compose.yaml`).
* Python Flask API:

  * `/trigger` → manually start WAHA session.
  * `/waha` → receive WAHA webhooks (messages).
* Blocklist support: add senders (e.g., `status`) to `.env` → these messages will only print, not forward to ntfy.
* Logs incoming messages with timestamp.
* Secure API calls with `X-Api-Key`.

---

## 📌 Notes

* Make sure ports `5002` (WAHA) and `5000` (Flask) are open.
* Protect your API key! Keep `.env` private and never commit it.
* If using on a VPS, consider tunneling (e.g., **ngrok**) to avoid WhatsApp login blocks.

---
