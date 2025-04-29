import cv2
import numpy as np
from collections import OrderedDict
import threading
import requests
import time

class CentroidTracker:
    def __init__(self, max_disappeared=50):
        self.next_object_id = 0
        self.objects = OrderedDict()
        self.disappeared = OrderedDict()
        self.max_disappeared = max_disappeared

    def register(self, centroid):
        self.objects[self.next_object_id] = centroid
        self.disappeared[self.next_object_id] = 0
        self.next_object_id += 1

    def deregister(self, object_id):
        del self.objects[object_id]
        del self.disappeared[object_id]

    def update(self, input_centroids):
        if len(input_centroids) == 0:
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)
            return self.objects

        if len(self.objects) == 0:
            for centroid in input_centroids:
                self.register(centroid)
        else:
            object_ids = list(self.objects.keys())
            object_centroids = list(self.objects.values())
            D = np.linalg.norm(np.array(object_centroids)[:, np.newaxis] - input_centroids, axis=2)
            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]

            used_rows = set()
            used_cols = set()

            for (row, col) in zip(rows, cols):
                if row in used_rows or col in used_cols:
                    continue
                object_id = object_ids[row]
                self.objects[object_id] = input_centroids[col]
                self.disappeared[object_id] = 0
                used_rows.add(row)
                used_cols.add(col)

            unused_rows = set(range(D.shape[0])) - used_rows
            unused_cols = set(range(D.shape[1])) - used_cols

            for row in unused_rows:
                object_id = object_ids[row]
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)

            for col in unused_cols:
                self.register(input_centroids[col])
        return self.objects

# Send updates to server every second (threaded)
def send_update():
    while True:
        try:
            current_capacity = in_count - out_count
            temperature = 24.0  # Replace if needed
            requests.post("http://localhost:5000/update", json={
                "capacity": current_capacity,
                "temperature": temperature
            }, timeout=1)
        except requests.exceptions.RequestException:
            pass  # Silent fail
        time.sleep(1)  # Send every 1 second

# Load model
net = cv2.dnn.readNetFromCaffe("deploy.prototxt", "mobilenet_iter_73000.caffemodel")

# Stream from Raspberry Pi
stream_url = "http://192.168.254.162:5000/video_feed/entrance"
cap = cv2.VideoCapture(stream_url)

ct = CentroidTracker()
in_count = 0
out_count = 0
previous_x = {}
object_states = {}

# Start background thread for server update
threading.Thread(target=send_update, daemon=True).start()

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    h, w = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5)
    net.setInput(blob)
    detections = net.forward()
    centroids = []

    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > 0.5:
            idx = int(detections[0, 0, i, 1])
            if idx != 15:
                continue
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            x1, y1, x2, y2 = box.astype("int")
            centroid = (int((x1 + x2) / 2), int((y1 + y2) / 2))
            centroids.append(centroid)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

    objects = ct.update(np.array(centroids))

    line_in_position = int(w * 0.7)
    line_out_position = int(w * 0.3)

    for (object_id, centroid) in objects.items():
        current_x = centroid[0]
        if object_id in previous_x:
            prev_x = previous_x[object_id]
            if prev_x < line_in_position and current_x >= line_in_position:
                if object_states.get(object_id) != "in":
                    in_count += 1
                    object_states[object_id] = "in"
            elif prev_x > line_out_position and current_x <= line_out_position:
                if object_states.get(object_id) != "out":
                    out_count += 1
                    object_states[object_id] = "out"
        previous_x[object_id] = current_x

    # Draw interface
    cv2.line(frame, (line_in_position, 0), (line_in_position, h), (255, 0, 0), 2)
    cv2.line(frame, (line_out_position, 0), (line_out_position, h), (0, 255, 255), 2)
    cv2.putText(frame, f"In: {in_count}", (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
    cv2.putText(frame, f"Out: {out_count}", (10, 100),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

    cv2.imshow("People Counter", frame)
    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
