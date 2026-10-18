import cv2
import json
import time
import argparse
import numpy as np
from datetime import datetime

# Define Hazard Zone (normalized coordinates: [xmin, ymin, xmax, ymax])
HAZARD_ZONE = [0.4, 0.4, 0.9, 0.9]

def emit_incident(track_id, cx, cy, alert_type):
    event = {
        "timestamp": datetime.now().isoformat(),
        "event": alert_type,
        "worker_id": int(track_id),
        "location": {"x": int(cx), "y": int(cy)},
        "status": "VIOLATION_DETECTED"
    }
    with open("safety_incidents.jsonl", "a") as f:
        f.write(json.dumps(event) + "\n")
    print(f"🚨 [ALERT] {alert_type} - Worker ID {track_id} at ({cx}, {cy})")

def main():
    parser = argparse.ArgumentParser(description="Workplace Safety Sentinel")
    parser.add_argument("video", type=str, help="Path to site surveillance video")
    parser.add_argument("--show", action="store_true", help="Display live window")
    args = parser.parse_args()

    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        print(f"Error opening video file: {args.video}")
        return

    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30

    # Setup Video Writer for output evidence
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter('safety_annotated.mp4', fourcc, fps, (W, H))

    # Background subtractor for person/motion detection in hazard zones
    fgbg = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=False)

    frame_idx = 0
    violations_count = 0

    print("🛡️ Workplace Safety Sentinel running...")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_idx += 1
        fgmask = fgbg.apply(frame)
        kernel = np.ones((3, 3), np.uint8)
        fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)
        
        contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        hx1, hy1, hx2, hy2 = int(HAZARD_ZONE[0]*W), int(HAZARD_ZONE[1]*H), int(HAZARD_ZONE[2]*W), int(HAZARD_ZONE[3]*H)
        
        hazard_breached = False

        for idx, cnt in enumerate(contours):
            if cv2.contourArea(cnt) > 1000:  # Filter small noise
                x, y, w, h = cv2.boundingRect(cnt)
                cx, cy = x + w // 2, y + h // 2

                # Check if person/object is inside the hazard zone box
                in_hazard = (hx1 <= cx <= hx2) and (hy1 <= cy <= hy2)
                
                color = (0, 0, 255) if in_hazard else (0, 255, 0)
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                cv2.putText(frame, f"Worker #{idx+1}", (x, max(15, y - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                if in_hazard:
                    hazard_breached = True
                    if frame_idx % 30 == 0:  # Log once per second per violation
                        emit_incident(idx+1, cx, cy, "UNAUTHORIZED_ZONE_ENTRY")
                        violations_count += 1

        # Draw Hazard Zone boundary box on frame
        zone_color = (0, 0, 255) if hazard_breached else (0, 165, 255)
        cv2.rectangle(frame, (hx1, hy1), (hx2, hy2), zone_color, 2)
        cv2.putText(frame, "RESTRICTED HAZARD ZONE", (hx1, max(20, hy1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, zone_color, 2)

        # Status text overlay
        status_str = "STATUS: BREACH DETECTED!" if hazard_breached else "STATUS: AREA SECURE"
        cv2.putText(frame, status_str, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255) if hazard_breached else (0, 255, 0), 2)

        out.write(frame)

        if args.show:
            cv2.imshow("Workplace Safety Sentinel", frame)
            if cv2.waitKey(1) == 27:  # ESC to quit
                break

    cap.release()
    out.release()
    cv2.destroyAllWindows()
    print(f"Done! Processed {frame_idx} frames. Total violations logged: {violations_count}")

if __name__ == "__main__":
    main()