import argparse
import json
import math
import threading
import time
from typing import Dict, List, Optional

try:
    import serial
except ImportError as exc:  # pragma: no cover
    raise SystemExit("pyserial is required: pip3 install pyserial") from exc

try:
    from flask import Flask, Response
except ImportError:  # pragma: no cover
    Flask = None
    Response = None

from api_client import BackendClient
from path_tracker import PathTracker
from vision import VisionDetector


COMMAND_MAP = {
    "forward": "F",
    "backward": "B",
    "left": "L",
    "right": "R",
    "stop": "S",
}


class CommandDispatcher:
    def __init__(self, uart: serial.Serial) -> None:
        self.uart = uart
        self.lock = threading.Lock()

    def send(self, action: str) -> None:
        action = action.lower().strip()
        code = COMMAND_MAP.get(action, action[:1].upper())
        if not code:
            return
        with self.lock:
            self.uart.write(f"{code}\n".encode("utf-8"))


def parse_line(line: str) -> Optional[dict]:
    if not line:
        return None
    if line.startswith("TL:"):
        try:
            return json.loads(line[3:])
        except json.JSONDecodeError:
            return None
    return None


def distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    meters_per_deg_lat = 111_111.0
    meters_per_deg_lon = 111_111.0 * math.cos(math.radians(lat1))
    dx = (lon2 - lon1) * meters_per_deg_lon
    dy = (lat2 - lat1) * meters_per_deg_lat
    return math.hypot(dx, dy)


def start_stream_server(vision: VisionDetector, host: str, port: int) -> None:
    if Flask is None or Response is None:
        raise RuntimeError("flask is required for streaming")

    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("opencv-python is required for streaming") from exc

    app = Flask(__name__)

    def frame_generator():
        while True:
            frame = vision.read_frame()
            if frame is None:
                time.sleep(0.05)
                continue
            ok, encoded = cv2.imencode(".jpg", frame)
            if not ok:
                time.sleep(0.05)
                continue
            chunk = encoded.tobytes()
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + chunk + b"\r\n"
            )

    @app.route("/camera/stream")
    def camera_stream():
        return Response(frame_generator(), mimetype="multipart/x-mixed-replace; boundary=frame")

    thread = threading.Thread(
        target=lambda: app.run(host=host, port=port, debug=False, threaded=True, use_reloader=False),
        daemon=True,
    )
    thread.start()


def main() -> None:
    parser = argparse.ArgumentParser(description="Raspberry Pi telemetry bridge")
    parser.add_argument("--port", default="/dev/serial0", help="ESP32 UART port")
    parser.add_argument("--baud", type=int, default=115200, help="UART baud rate")
    parser.add_argument("--backend", default="http://localhost:8080", help="Go backend base URL")
    parser.add_argument("--ws", default="ws://localhost:8080/ws", help="Backend WebSocket URL")
    parser.add_argument("--stream", action="store_true", help="Enable MJPEG stream on Pi")
    parser.add_argument("--stream-port", type=int, default=8000, help="MJPEG stream port")
    parser.add_argument("--camera", type=int, default=0, help="Camera index")
    parser.add_argument("--vision-model", default="", help="Optional YOLO model path")
    args = parser.parse_args()

    uart = serial.Serial(args.port, args.baud, timeout=0.2)
    dispatcher = CommandDispatcher(uart)

    backend = BackendClient(args.backend, args.ws)
    backend.on_command = lambda cmd: dispatcher.send(cmd.get("action", ""))
    backend.start()

    path = PathTracker()
    vision = VisionDetector(camera_index=args.camera, model_path=args.vision_model or None)

    if args.stream:
        start_stream_server(vision, host="0.0.0.0", port=args.stream_port)

    telemetry = {}
    victims: List[Dict] = []
    last_path_push = 0.0
    last_telemetry_push = 0.0
    last_vision_check = 0.0
    last_obstacle_alert = 0.0

    while True:
        raw = uart.readline().decode("utf-8", errors="ignore").strip()
        if raw.startswith("AL:"):
            try:
                alert = json.loads(raw[3:])
                backend.send_alert(alert)
            except json.JSONDecodeError:
                pass
            continue

        payload = parse_line(raw)
        if payload:
                        payload["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                        telemetry = payload

                        gps = payload.get("gps", {})
                        odom = payload.get("odometry", {})
                        pose = payload.get("pose", {})

            speed = float(odom.get("speed_mps", 0.0))
            heading = float(pose.get("heading_deg", 0.0))
            now = time.time()
            dt = max(0.0, now - path.state.last_update)
            path.update_odometry(speed, heading, dt)

            if gps.get("fix") and gps.get("lat") and gps.get("lon"):
                path.apply_gps(float(gps.get("lat")), float(gps.get("lon")), heading)

            pose["x"] = path.state.x
            pose["y"] = path.state.y
            pose["heading_deg"] = heading
            payload["pose"] = pose

            sonar_cm = float(payload.get("sonar_cm", 0.0))
            if sonar_cm > 0.0 and sonar_cm < 35.0 and now - last_obstacle_alert > 3.0:
                alert = {
                    "id": f"obs-{int(now)}",
                    "level": "warning",
                    "message": f"Obstacle detected at {sonar_cm:.1f} cm",
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
                }
                backend.send_alert(alert)
                last_obstacle_alert = now

        now = time.time()
        if telemetry and now - last_telemetry_push > 0.2:
            backend.send_telemetry(telemetry)
            last_telemetry_push = now

        if now - last_path_push > 1.0:
            backend.send_path(path.get_points())
            last_path_push = now

        if now - last_vision_check > 1.2:
            last_vision_check = now
            frame = vision.read_frame()
            detections = vision.detect_people(frame)
            if detections:
                gps = telemetry.get("gps", {})
                lat = float(gps.get("lat", 0.0))
                lon = float(gps.get("lon", 0.0))
                x = float(path.state.x)
                y = float(path.state.y)

                for det in detections:
                    if gps.get("fix") and lat and lon:
                        too_close = any(
                            distance_m(lat, lon, v.get("lat", 0.0), v.get("lon", 0.0)) < 4.0
                            for v in victims
                        )
                    else:
                        too_close = any(
                            math.hypot(x - v.get("x", 0.0), y - v.get("y", 0.0)) < 2.0
                            for v in victims
                        )

                    if not too_close:
                        victim = {
                            "id": f"victim-{int(now)}",
                            "lat": lat,
                            "lon": lon,
                            "x": x,
                            "y": y,
                            "confidence": det.confidence,
                            "detected_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
                        }
                        victims.append(victim)
                        backend.send_victims(victims)

        time.sleep(0.01)


if __name__ == "__main__":
    main()
