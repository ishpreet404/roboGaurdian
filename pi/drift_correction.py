import math
from dataclasses import dataclass
from typing import Tuple


@dataclass
class DriftState:
    origin_lat: float = 0.0
    origin_lon: float = 0.0
    initialized: bool = False


class GPSDriftCorrector:
    def __init__(self, smoothing: float = 0.15, max_jump_m: float = 5.0) -> None:
        self.smoothing = smoothing
        self.max_jump_m = max_jump_m
        self.state = DriftState()

    def reset_origin(self, lat: float, lon: float) -> None:
        self.state.origin_lat = lat
        self.state.origin_lon = lon
        self.state.initialized = True

    def to_local_xy(self, lat: float, lon: float) -> Tuple[float, float]:
        if not self.state.initialized:
            self.reset_origin(lat, lon)

        meters_per_deg_lat = 111_111.0
        meters_per_deg_lon = 111_111.0 * math.cos(math.radians(self.state.origin_lat))

        dx = (lon - self.state.origin_lon) * meters_per_deg_lon
        dy = (lat - self.state.origin_lat) * meters_per_deg_lat
        return dx, dy

    def correct(self, odom_x: float, odom_y: float, lat: float, lon: float) -> Tuple[float, float]:
        gps_x, gps_y = self.to_local_xy(lat, lon)

        drift_x = gps_x - odom_x
        drift_y = gps_y - odom_y
        drift_mag = math.hypot(drift_x, drift_y)

        if drift_mag > self.max_jump_m:
            scale = self.max_jump_m / drift_mag
            drift_x *= scale
            drift_y *= scale

        corrected_x = odom_x + drift_x * self.smoothing
        corrected_y = odom_y + drift_y * self.smoothing
        return corrected_x, corrected_y
