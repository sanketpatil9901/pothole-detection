import cv2 as cv
import time
import geocoder
import os

def detectPotholeonVideo(filename):
    class_name = []
    with open(os.path.join("project_files", 'obj.names'), 'r') as f:
        class_name = [cname.strip() for cname in f.readlines()]

    net = cv.dnn.readNet('project_files/yolov4_tiny.weights', 'project_files/yolov4_tiny.cfg')
    net.setPreferableBackend(cv.dnn.DNN_BACKEND_OPENCV)
    net.setPreferableTarget(cv.dnn.DNN_TARGET_CPU)

    model = cv.dnn_DetectionModel(net)
    model.setInputParams(size=(640, 480), scale=1 / 255, swapRB=True)

    cap = cv.VideoCapture(filename)
    if not cap.isOpened():
        return "", 0, []

    width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))

    output_path = os.path.join("static", "outputs", "PotholeVideoResult.mp4")
    out = cv.VideoWriter(output_path, cv.VideoWriter_fourcc(*'mp4v'), 10, (width, height))

    try:
        g = geocoder.ip('me')
        coordinates = g.latlng if g.latlng else [0, 0]
    except:
        coordinates = [0, 0]

    pothole_details = []
    count = 0
    Conf_threshold = 0.5
    NMS_threshold = 0.4

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        classes, scores, boxes = model.detect(frame, Conf_threshold, NMS_threshold)
        for (classid, score, box) in zip(classes, scores, boxes):
            x, y, w, h = box
            cv.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv.putText(frame, f"{round(score * 100, 2)}% Pothole", (x, y - 10),
                       cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

            pothole_details.append({
                "confidence": round(score * 100, 2),
                "position": (int(x), int(y)),
                "size": (int(w), int(h)),
                "coordinates": coordinates
            })
            count += 1

        out.write(frame)

    cap.release()
    out.release()
    return output_path, count, pothole_details
