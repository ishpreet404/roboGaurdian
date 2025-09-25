# Robot Guardian React Frontend

A polished control center for monitoring and driving the Robot Guardian platform.

## Features

- 🌌 **Immersive design** with glassmorphism panels, gradients, and live telemetry.
- 🧭 **Multi-page navigation**: Overview, Live Control, and Alerts & Logs.
- 🛰️ **Real-time polling** of Raspberry Pi status and Windows AI bridge alerts.
- 🎮 **Manual command pad** with single-click maneuvers and safety stop.
- 🔄 **Configurable API endpoints** so the dashboard can follow tunnel or LAN changes.
- 📹 **Live MJPEG stream** preview pulled straight from the Pi camera server.

## Quick start

```bash
npm install
npm run dev
```

### Environment overrides

Copy `.env.example` to `.env` (create one if needed) and set:

```
VITE_PI_API_BASE=http://192.168.1.12:5000
VITE_WINDOWS_API_BASE=http://localhost:5050
```

When unset, the defaults fall back to the hard-coded addresses shown above.

## Building for production

```bash
npm run build
npm run preview
```

The `dist/` output can be served via any static server (e.g. `serve`, `nginx`, `Apache`).
