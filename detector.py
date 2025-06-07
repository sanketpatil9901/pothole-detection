import cv2

def detect_potholes(image_path):
    net = cv2.dnn.readNet("yolov4-tiny/yolov4-tiny.weights", "yolov4-tiny/yolov4-tiny.cfg")
    layer_names = net.getLayerNames()
    output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers().flatten()]

    img = cv2.imread(image_path)
    height, width = img.shape[:2]
    
    blob = cv2.dnn.blobFromImage(img, 1/255.0, (416, 416), swapRB=True, crop=False)
    net.setInput(blob)
    outputs = net.forward(output_layers)

    class_ids = []
    confidences = []
    boxes = []

    for output in outputs:
        for det in output:
            scores = det[5:]
            class_id = int(scores.argmax())
            confidence = scores[class_id]
            if confidence > 0.5:
                center_x, center_y, w, h = (det[0:4] * [width, height, width, height]).astype('int')
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)
                boxes.append([x, y, int(w), int(h)])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    if confidences:
        return max(confidences), max([w*h for _, _, w, h in boxes])
    else:
        return 0.0, 0
