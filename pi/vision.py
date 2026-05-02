from dataclasses import dataclass
from typing import List, Optional, Tuple

try:
    import cv2
except ImportError:  # pragma: no cover
    cv2 = None

try:
    from ultralytics import YOLO
except Exception:  # pragma: no cover
    YOLO = None


@dataclass
class Detection:
    bbox: Tuple[int, int, int, int]
    confidence: float


class VisionDetector:
    def __init__(self, camera_index: int = 0, model_path: Optional[str] = None) -> None:
        self.camera_index = camera_index
        self.model_path = model_path
        self.cap = None
        self.hog = None
        self.yolo = None

        if cv2 is not None:
            self.cap = cv2.VideoCapture(camera_index)
            self.hog = cv2.HOGDescriptor()
            self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

        if YOLO is not None and model_path:
            try:
                self.yolo = YOLO(model_path)
            except Exception:
                self.yolo = None

    def read_frame(self):
        if self.cap is None:
            return None
        ok, frame = self.cap.read()
        return frame if ok else None

    def detect_people(self, frame) -> List[Detection]:
        if frame is None or cv2 is None:
            return []

        if self.yolo is not None:
            results = self.yolo.predict(frame, imgsz=640, conf=0.35, verbose=False)
            detections: List[Detection] = []
            for result in results:
                for box in result.boxes:
                    cls = int(box.cls[0]) if box.cls is not None else -1
                    if cls != 0:
                        continue
                    conf = float(box.conf[0]) if box.conf is not None else 0.0
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    detections.append(Detection((x1, y1, x2, y2), conf))
            return detections

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rects, weights = self.hog.detectMultiScale(gray, winStride=(8, 8))
        detections = []
        for (x, y, w, h), weight in zip(rects, weights):
            detections.append(Detection((x, y, x + w, y + h), float(weight)))
        return detections

    def close(self) -> None:
        if self.cap is not None:
            self.cap.release()
            self.cap = None
