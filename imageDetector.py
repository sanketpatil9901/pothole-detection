import uuid
import time
import cv2
import os

def detectPotholeonImage(filename, gps_coords):
    img = cv2.imread(filename)

    # Load YOLO model
    with open(os.path.join("project_files", 'obj.names'), 'r') as f:
        classes = f.read().splitlines()

    net = cv2.dnn.readNet('project_files/yolov4_tiny.weights', 'project_files/yolov4_tiny.cfg')
    model = cv2.dnn_DetectionModel(net)
    model.setInputParams(scale=1 / 255, size=(416, 416), swapRB=True)
    classIds, scores, boxes = model.detect(img, confThreshold=0.6, nmsThreshold=0.4)

    pothole_info = []

    for (classId, score, box) in zip(classIds, scores, boxes):
        x, y, w, h = box
        cv2.rectangle(img, (x, y), (x + w, y + h), color=(0, 255, 0), thickness=2)
        label = f"{round(score * 100, 2)}% Pothole"
        cv2.putText(img, label, (x, y - 10), cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 0, 0), 1)

        pothole_info.append({
            'confidence': float(round(score * 100, 2)),
            'position': (int(x), int(y)),
            'size': (int(w), int(h)),
            'gps': [float(gps_coords[0]), float(gps_coords[1])]
        })

    # Generate a unique filename for each output
    ext = os.path.splitext(filename)[1]
    unique_filename = f"PothHoleDetected_{uuid.uuid4().hex}_{int(time.time())}{ext}"
    output_dir = 'static/outputs'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, unique_filename)
    cv2.imwrite(output_path, img)

    return len(pothole_info), pothole_info, output_path
