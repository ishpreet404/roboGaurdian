# RoboGuardian Deployment & Usage Guide

This guide walks you through preparing the W### 4.4 Configure voice output
- Attach a USB/Bluetooth speaker (or use the Pi's audio jack). The enhanced TTS system supports multiple engines for better speech quality.
- **Speech Quality Options**:
  - **Best quality**: gTTS (needs internet) - natural sounding Hindi/English
  - **Good quality**: pyttsx3 with Festival engine - configurable voices
  - **Basic quality**: espeak - works offline, fast but robotic
- **Fix "No speech engine available"**: Run the included `fix_pi_speech.sh` script for full setup.
- Test Hindi: `echo "नमस्ते रोबोट" | espeak -v hi` and English: `echo "Hello robot" | espeak`.
- **One-Way Audio Chat**: Use `audio_chat_test.html` to send live audio from your laptop microphone directly to the Pi speaker.
- (Optional) To enable the GitHub-based assistant, export the same tokens used on Windows and set `PI_ASSISTANT_MODE=full`.
- To keep the Pi in **speaker-only mode** (no GitHub API calls), leave the token unset and ensure `PI_ASSISTANT_MODE` is `fallback` (default).ws control center, the Raspberry Pi robot server, and the optional frontend so you can stream video, control the robot, exchange assistant messages, and deliver one-way voice notes with reminder scheduling.

---

## 1. High-level architecture

- **Windows workstation** runs `windows_robot_supervisor.py` to expose REST APIs to the frontend and coordinate with the Pi.
- **Raspberry Pi** runs `pi_camera_server_fixed.py`, handling camera streaming, UART commands to the ESP32, speaker playback (audio files & TTS), and reminder scheduling.
- **Frontend app (optional)** talks to the Windows supervisor APIs to control the system and upload voice notes.

Voice notes flow from the browser → Windows supervisor → Pi `/assistant/voice_note` endpoint → local playback queue (or text-to-speech reminder).

### New Features:
- **Enhanced TTS**: Multi-engine speech system with smooth Hindi/English support via gTTS
- **Fixed Reminders**: Local reminder scheduling with proper error logging and delivery
- **One-Way Audio Chat**: Live microphone → Pi speaker streaming for real-time communication

---

## 2. Requirements checklist

| Component | Minimum requirements |
|-----------|----------------------|
| Windows PC | Python 3.11+, Git, optional Node.js (for `frontend/`), speakers/mic if testing locally |
| Raspberry Pi | Raspberry Pi 4 (2 GB+) recommended, Raspberry Pi OS Bullseye+, internet, UART wired to ESP32, optional speakers or audio-output device |
| ESP32 | Pre-flashed with compatible firmware responding to `F/B/L/R/S` commands |
| Network | Windows PC and Pi must share the same LAN (or VPN tunneled) |

> **Tip:** Keep the Pi on a stable power supply; video streaming and TTS draw noticeable current.

---

## 3. Windows workstation setup

1. **Clone repo & install dependencies**
   ```powershell
   git clone https://github.com/ishpreet404/roboGaurdian.git
   cd roboGaurdian
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. **Configure environment**
   - Copy `.env.example` to `.env` if present; otherwise create `.env` beside `windows_ai_controller.py` with any tokens you need (e.g., GitHub Models token, Pi base URL overrides).
   - Ensure `PI_BASE_URL` points to your Pi (default `http://raspberrypi:5000`).

3. **Run the Windows supervisor**
   ```powershell
   python .\windows_robot_supervisor.py
   ```
   - API lives at `http://localhost:5050/api/status`.
   - Use the UI or REST endpoints to connect to the Pi (`POST /api/connect`).

4. **(Optional) Frontend**
   ```powershell
   cd frontend
   npm install
   npm run dev
   ```
   Configure it to talk to `http://localhost:5050`.

---

## 4. Raspberry Pi setup

### 4.1 Prepare the OS
- Update packages: `sudo apt update && sudo apt upgrade -y`.
- Enable camera & UART via `sudo raspi-config` → Interface Options.
- Reboot.

### 4.2 Install system packages
```bash
sudo apt install -y python3-pip python3-venv python3-opencv python3-flask \
    python3-serial python3-numpy ffmpeg mpv alsa-utils espeak espeak-data \
    festival festvox-hi-nsk speech-dispatcher
pip3 install pyttsx3 gTTS pygame
```

### 4.3 Deploy repo files to Pi
```bash
mkdir -p ~/roboGuardian
rsync -avz <windows_pc>:/path/to/repo/pi_camera_server_fixed.py ~/roboGuardian/
rsync -avz <windows_pc>:/path/to/repo/raspi-chatbot/ ~/roboGuardian/raspi-chatbot/
cd ~/roboGuardian
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
> You can also run `wget_pi_multimode.sh` from the repo to download all Pi-side files.

### 4.4 Configure voice output
- Attach a USB/Bluetooth speaker (or use the Pi’s audio jack). The built-in `pyttsx3` fallback will speak reminders and text.
- (Optional) To enable the GitHub-based assistant, export the same tokens used on Windows and set `PI_ASSISTANT_MODE=full`.
- To keep the Pi in **speaker-only mode** (no GitHub API calls), leave the token unset and ensure `PI_ASSISTANT_MODE` is `fallback` (default).

### 4.5 Launch the Pi server
```bash
source ~/roboGuardian/.venv/bin/activate
python3 pi_camera_server_fixed.py
```
- Video stream: `http://<pi-ip>:5000/video_feed`
- Status: `http://<pi-ip>:5000/status`
- Assistant API (new): `http://<pi-ip>:5000/assistant/...`

---

## 5. ESP32 & hardware notes

1. Wire Pi GPIO14/15 (UART) to ESP32 RX/TX and common ground.
2. Confirm serial link at 9600 baud. Use `test_esp32.py` as a sanity check.
3. Calibrate motors and ensure `F/B/L/R/S` map correctly.

---

## 6. Voice notes & reminders

### 6.1 Uploading a voice note
- POST to Windows supervisor `POST /api/assistant/voice-note` with either:
  - `multipart/form-data`: `file=@note.wav`, optional `delay_seconds`, `text` (plays TTS alongside audio), or
  - JSON body containing Base64 `audio`, optional `delay_seconds`, `filename`, and `text`.
- Windows proxies the call to the Pi, which stores the audio (in `/tmp`) and enqueues playback.
- Response fields:
  - `playback_mode`: `audio` or `text`
  - `queued`: `true` if a delay was requested (`>=1s`)
  - `scheduled_for`: ISO timestamp of playback
  - `playback_id`: file identifier (for logs)

### 6.2 Reminder scheduling
- `GET /api/assistant/reminders` – list reminders (mirrors Pi state even if Windows assistant offline).
- `POST /api/assistant/reminders` JSON fields:
  - `message` (required)
  - `remind_at` (ISO string) **or** `delay_seconds` / `delay_minutes`
  - `voice_note` (optional text spoken at reminder time)
- `DELETE /api/assistant/reminders/{id}` – cancel a reminder.
- Reminders fire locally on the Pi—even without the GitHub assistant—using the fallback speaker.

### 6.3 Direct speaking
- `POST /api/assistant/speak` with `text` to immediately queue speech (TTS).
- `async` flag defaults to `true`; set `false` for blocking behaviour.

---

## 7. Verification checklist

1. **Syntax check**
   ```powershell
   python -m compileall pi_camera_server_fixed.py windows_robot_supervisor.py
   ```
2. **Pi server health**
   - Browse to `http://<pi-ip>:5000` and verify video feed.
   - `GET /assistant/status` shows `online` (or `speaker_only` when fallback active).
3. **Windows supervisor health**
   - Visit `http://localhost:5050/api/status`; ensure `pi_connected` true.
4. **Voice note smoke test**
   ```bash
   curl -X POST http://localhost:5050/api/assistant/voice-note \
     -H "Content-Type: application/json" \
     -d '{"audio":"<base64 wav>", "delay_seconds":0}'
   ```
   Confirm audio plays through the Pi speakers.
5. **Reminder test**
   ```bash
   curl -X POST http://localhost:5050/api/assistant/reminders \
     -H "Content-Type: application/json" \
     -d '{"message":"Drink water","delay_seconds":30}'
   ```
   Expect a spoken reminder ~30 seconds later.

---

## 8. Troubleshooting

| Symptom | Fix |
|---------|-----|
| `voice_ready` false and no speech | Ensure GitHub token valid, speaker connected, or rely on fallback pyttsx3 engine (install `libespeak-ng1`, `libportaudio2`). |
| Voice note endpoint returns 503 | Pi server offline or no speaker hardware; check `/assistant/status`. |
| UART commands fail | Verify `sudo raspi-config` UART enabled and wiring correct; see logs in Pi terminal. |
| Camera feed blank | Run `python3 camera_test.py`, check ribbon cable/orientation. |
| Audio file fails to play | Install `ffmpeg` or `mpv`; ensure ALSA volume > 0 (`alsamixer`). |

---

## 9. Maintenance tips

- Regularly update dependencies on both Windows and Pi (`pip install -U -r requirements.txt`).
- Keep Pi storage tidy; the voice note queue deletes processed files, but monitor `/tmp` if using long delays.
- Schedule `systemd` services for automatic startup (samples: `pi_camera_server.service`, `windows_robot_supervisor.bat`).
- Log monitoring: tail `~/roboGuardian/pi_server.log` (configure logging to file) for audio/reminder events.

Happy building! 🚀
