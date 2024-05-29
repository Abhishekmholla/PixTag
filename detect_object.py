import os
import cv2
import time
import base64
import urllib.parse
import numpy as np


# YOLO configs root path
yolo_path = "yolo_tiny_configs"

# Yolov3-tiny configs
labels_path = "coco.names"
configs_path = "yolov3-tiny.cfg"
weights_path = "yolov3-tiny.weights"

# Thresholds
conf_threshold = 0.3
nms_threshold = 0.1

def get_labels(labels_path):
    """
    Load the COCO class labels our YOLO model was trained on

    Parameters
    ----------
    :param labels_path: path to class labels

    Returns
    -------
    :return list of COCO labels
    """

    label_path = os.path.sep.join([yolo_path, labels_path])
    labels = open(label_path).read().strip().split("\n")

    return labels


def get_weights(weights_path):
    """
    Derive the paths to the YOLO weights and model configuration

    Parameters
    ----------
    :param weights_path: path to YOLO weights

    Returns
    -------
    :return derived weights paths
    """

    weights_path = os.path.sep.join([yolo_path, weights_path])

    return weights_path

def get_config(config_path):
    """
    Derive the paths to the YOLO configs

    Parameters
    ----------
    :param config_path: path to YOLO configs

    Returns
    -------
    :return derived config paths
    """

    config_path = os.path.sep.join([yolo_path, config_path])

    return config_path

def load_model(config_path, weights_path):
    """
    Load our YOLO object detector trained on COCO dataset (80 classes)

    Parameters
    ----------
    :param config_path: path to YOLO configs
    :param weights_path: path to YOLO weights

    Returns
    -------
    :return object detector model
    """

    print("[INFO] Loading YOLO object detector ...")
    net = cv2.dnn.readNetFromDarknet(config_path, weights_path)
    return net

def predict(image, net, labels, id):
    """
    Load our YOLO object detector trained on COCO dataset (80 classes)

    Parameters
    ----------
    :param config_path: path to YOLO configs
    :param weights_path: path to YOLO weights
    """

    (H, W) = image.shape[:2]
    
    # Determine only the *output* layer names that we need from YOLO
    ln = net.getLayerNames()
    ln = [ln[i - 1] for i in net.getUnconnectedOutLayers()]

    # Construct a blob from the input image and then perform a forward
    # pass of the YOLO object detector, giving us our bounding boxes and
    # associated probabilities
    blob = cv2.dnn.blobFromImage(image, 1 / 255.0, (416, 416),
                                 swapRB = True, crop = False)
    net.setInput(blob)
    start = time.time()
    layer_outputs = net.forward(ln)
    end = time.time()

    # Log timing information on YOLO
    print("[INFO] YOLO took {:.6f} seconds".format(end - start))

    # Initialize our lists of detected bounding boxes, 
    # confidences and class IDs respectively
    boxes = []
    confidences = []
    class_ids = []

    # Loop over each of the layer outputs
    for output in layer_outputs:
        # Loop over each of the detections
        for detection in output:
            # Extract the class ID and confidence (i.e., probability) of
            # the current object detection
            scores = detection[5:]
            classID = np.argmax(scores)
            confidence = scores[classID]

            # Filter out weak predictions by ensuring the detected
            # probability is greater than the minimum probability
            if confidence > conf_threshold:
                # Scale the bounding box coordinates back relative to the
                # size of the image, keeping in mind that YOLO actually
                # returns the center (x, y)-coordinates of the bounding
                # box followed by the boxes' width and height
                box = detection[0:4] * np.array([W, H, W, H])
                (centerX, centerY, width, height) = box.astype("int")

                # Use the center (x, y)-coordinates to derive the top and
                # and left corner of the bounding box
                x = int(centerX - (width / 2))
                y = int(centerY - (height / 2))

                # Update our list of bounding box coordinates, 
                # confidences and class IDs
                boxes.append([x, y, int(width), int(height)])
                confidences.append(float(confidence))
                class_ids.append(classID)

    # Apply non-maxima suppression to suppress weak, overlapping bounding boxes
    idxs = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, nms_threshold)

    # Reponse object dictionary placeholder
    response = dict()
    
    # Ensure at least one detection exists
    if len(idxs) > 0:
        # Loop over the indexes we are keeping
        # Create object_list placeholder list
        objects_list = list()
        for i in idxs.flatten():

            # A new object dictionary
            new_object = dict()
            new_object["label"] = labels[class_ids[i]]
            new_object["accuracy"] = confidences[i]

            # A new object boundary rectangle dictionary
            new_object_boundary = dict()
            new_object_boundary["height"] = boxes[i][3]
            new_object_boundary["left"] = boxes[i][0]
            new_object_boundary["top"] = boxes[i][1]
            new_object_boundary["width"] = boxes[i][2]
            new_object["rectangle"] = new_object_boundary

            # Append objects to object_list list
            objects_list.append(new_object)
        
        response["id"] = id
        response["objects"] = objects_list

    return response

# Get YOLO configs
lables = get_labels(labels_path)
configs = get_config(configs_path)
weights = get_weights(weights_path)

def run(event, _):
    """
    A lambda function to detect objects in a given image
    """

    # Resolve S3 image upload event parameters
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(event["Records"][0]["s3"]["object"]["key"], encoding = "utf-8")
    image_path = f"s3://{bucket}/{key}"

    try: 

        # Encode image to base64 string
        image_file = open(image_path, "rb")
        image_base64_str = base64.b64encode(image_file.read())
        image_file.close()

        # Convert base64 image string to OpenCV image
        image = np.frombuffer(base64.b64decode(image_base64_str), np.uint8)
        image = cv2.imdecode(image, flags = cv2.COLOR_BGR2RGB)
        
        # Load the neural net.
        nets = load_model(configs, weights)
        
        # Perform predictions
        response = predict(image, nets, lables, id)
        
        # Return JSON response
        print(response)
    
    except Exception as e:
        print(f"Exception: {e}")

