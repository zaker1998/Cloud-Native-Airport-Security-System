from fastapi import FastAPI, Request
import requests

app = FastAPI()

IMAGE_ANALYSIS_URL = "http://image-analysis/frame"
FACE_RECOGNITION_URL = "http://face-recognition/frame"
SECTION_URL = "http://section/persons"
ALERT_URL = "http://alert/alerts"


@app.get("/livenessProbe")
def live():
    return {"status": "ok"}


@app.get("/readinessProbe")
def ready():
    return {"status": "ready"}


@app.post("/frame")
def receive_frame(frame: dict):
    # 1. send to image-analysis
    try:
        ia_res = requests.post(IMAGE_ANALYSIS_URL, json=frame, timeout=3)
        if ia_res.status_code >= 300:
            ia_data = None
        else:
            ia_data = ia_res.json()
    except:
        ia_data = None

    # 2. send persons → section
    if ia_data and "persons" in ia_data:
        persons_payload = {
            "timestamp": frame.get("timestamp"),
            "section": frame.get("section"),
            "event": frame.get("event"),
            "persons": ia_data.get("persons", []),
            "image": frame.get("image"),
            "frame_uuid": frame.get("frame_uuid"),
        }
        try:
            requests.post(SECTION_URL, json=persons_payload, timeout=3)
        except:
            pass

    # 3. send to face-recognition
    try:
        fr_res = requests.post(FACE_RECOGNITION_URL, json=frame, timeout=3)
        if fr_res.status_code == 200:
            fr_data = fr_res.json()
        else:
            fr_data = None
    except:
        fr_data = None

    # 4. send known-persons → alert
    if fr_data and "known-persons" in fr_data:
        alert_payload = {
            "timestamp": frame.get("timestamp"),
            "section": frame.get("section"),
            "event": frame.get("event"),
            "known-persons": fr_data.get("known-persons", []),
            "image": frame.get("image"),
            "frame_uuid": frame.get("frame_uuid"),
        }
        try:
            requests.post(ALERT_URL, json=alert_payload, timeout=3)
        except:
            pass

    # 5. return response
    return {"status": "processed"}
