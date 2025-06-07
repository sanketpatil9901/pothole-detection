import cv2
import numpy as np

def detect_potholes(image_path):
    net = cv2.dnn.readNet("yolov4-tiny.weights", "yolov4-tiny.cfg")
    layer_names = net.getUnconnectedOutLayersNames()
    image = cv2.imread(image_path)
    h, w = image.shape[:2]
    blob = cv2.dnn.blobFromImage(image, 1/255, (416, 416), swapRB=True, crop=False)
    net.setInput(blob)
    outputs = net.forward(layer_names)
    
    results = []
    for output in outputs:
        for det in output:
            scores = det[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5:
                cx, cy, bw, bh = (det[0:4] * [w, h, w, h]).astype(int)
                results.append({
                    'bbox': [int(cx - bw/2), int(cy - bh/2), int(bw), int(bh)],
                    'confidence': float(confidence),
                    'severity': 'High' if bw * bh > 40000 else 'Medium' if bw * bh > 10000 else 'Low'
                })
    return results
