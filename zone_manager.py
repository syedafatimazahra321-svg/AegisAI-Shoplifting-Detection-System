import cv2
import numpy as np

# Default zones for a standard store layout.
# Each zone has a polygon (normalized 0-1 coords) and risk multiplier.
DEFAULT_ZONES = [
    {
        "name": "Exit Zone",
        "polygon": [(0.7, 0.5), (1.0, 0.5), (1.0, 1.0), (0.7, 1.0)],
        "risk_multiplier": 2.0,
        "color": (0, 0, 255)  # Red
    },
    {
        "name": "High Value Shelf",
        "polygon": [(0.0, 0.0), (0.3, 0.0), (0.3, 0.5), (0.0, 0.5)],
        "risk_multiplier": 1.5,
        "color": (0, 165, 255)  # Orange
    },
    {
        "name": "General Area",
        "polygon": [(0.3, 0.0), (0.7, 0.0), (0.7, 1.0), (0.3, 1.0)],
        "risk_multiplier": 1.0,
        "color": (0, 255, 0)  # Green
    }
]

class ZoneManager:
    def __init__(self, zones=None, frame_width=640, frame_height=480):
        self.zones = zones or DEFAULT_ZONES
        self.w = frame_width
        self.h = frame_height

    def _to_pixel(self, normalized_polygon):
        return [(int(x * self.w), int(y * self.h)) for x, y in normalized_polygon]

    def get_zone_multiplier(self, person_bbox):
        """
        person_bbox: (x, y, w, h) of detected person in pixels
        Returns the highest risk multiplier from all zones the person is in.
        """
        if person_bbox is None:
            return 1.0, "General Area"
            
        px, py, pw, ph = person_bbox
        # Use bottom-center of bounding box as person's location (their feet)
        person_x = px + pw // 2
        person_y = py + ph
        
        max_multiplier = 1.0
        active_zone = "General Area"
        
        for zone in self.zones:
            pts = np.array(self._to_pixel(zone["polygon"]), dtype=np.int32)
            # Use OpenCV pointPolygonTest to check if the point is inside the polygon
            if cv2.pointPolygonTest(pts, (person_x, person_y), False) >= 0:
                if zone["risk_multiplier"] > max_multiplier:
                    max_multiplier = zone["risk_multiplier"]
                    active_zone = zone["name"]
                    
        return max_multiplier, active_zone

    def draw_zones(self, frame):
        """Draw semi-transparent zone overlays on frame for visualization."""
        overlay = frame.copy()
        for zone in self.zones:
            pts = np.array(self._to_pixel(zone["polygon"]), dtype=np.int32)
            cv2.fillPoly(overlay, [pts], zone["color"])
            
            # Draw Label at the center of the polygon
            centroid_x = int(np.mean([p[0] for p in self._to_pixel(zone["polygon"])]))
            centroid_y = int(np.mean([p[1] for p in self._to_pixel(zone["polygon"])]))
            cv2.putText(overlay, zone["name"], (centroid_x - 40, centroid_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                        
        # Blend overlay with original frame (30% transparency)
        return cv2.addWeighted(overlay, 0.3, frame, 0.7, 0)

# Verification Test
if __name__ == "__main__":
    zm = ZoneManager()
    # Test simulation: simulating a person box at (280, 300, 80, 100)
    mult, zone = zm.get_zone_multiplier((280, 300, 80, 100))
    print(f"Zone: {zone}, Risk multiplier: {mult}")
    print("Zone Manager OK!")