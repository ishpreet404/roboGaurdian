import math
import time
from dataclasses import dataclass, field
from typing import List, Optional

from drift_correction import GPSDriftCorrector


@dataclass
class PathPoint:
    x: float
    y: float
    lat: float
    lon: float
    heading_deg: float
    timestamp: float


@dataclass
class PathState:
    x: float = 0.0
    y: float = 0.0
    heading_deg: float = 0.0
    last_update: float = field(default_factory=time.time)
    last_lat: Optional[float] = None
    last_lon: Optional[float] = None


class PathTracker:
    def __init__(self, max_points: int = 1500, smoothing: float = 0.2) -> None:
        self.max_points = max_points
        self.smoothing = smoothing
        self.state = PathState()
        self.points: List[PathPoint] = []
        self.drift = GPSDriftCorrector(smoothing=smoothing)

    def update_odometry(self, speed_mps: float, heading_deg: float, dt: float) -> None:
        heading_rad = math.radians(heading_deg)
        dx = math.cos(heading_rad) * speed_mps * dt
        dy = math.sin(heading_rad) * speed_mps * dt

        self.state.x += dx
        self.state.y += dy
        self.state.heading_deg = heading_deg
        self.state.last_update = time.time()

        self._append_point()

    def apply_gps(self, lat: float, lon: float, heading_deg: Optional[float] = None) -> None:
        if lat == 0.0 and lon == 0.0:
            return

        corrected_x, corrected_y = self.drift.correct(self.state.x, self.state.y, lat, lon)
        self.state.x = corrected_x
        self.state.y = corrected_y
        self.state.last_lat = lat
        self.state.last_lon = lon

        if heading_deg is not None:
            self.state.heading_deg = heading_deg

        self._append_point()

    def _append_point(self) -> None:
        point = PathPoint(
            x=self.state.x,
            y=self.state.y,
            lat=self.state.last_lat or 0.0,
            lon=self.state.last_lon or 0.0,
            heading_deg=self.state.heading_deg,
            timestamp=time.time(),
        )
        self.points.append(point)
        if len(self.points) > self.max_points:
            self.points = self.points[-self.max_points :]

    def get_points(self) -> List[dict]:
        return [
            {
                "x": p.x,
                "y": p.y,
                "lat": p.lat,
                "lon": p.lon,
                "heading_deg": p.heading_deg,
                "timestamp": p.timestamp,
            }
            for p in self.points
        ]
