import os
import cv2
import time
import boto3
import base64
import numpy as np
from boto3.dynamodb.conditions import Key

# YOLO configs root path
yolo_path = "/opt/yolo_tiny_configs"

# Yolov3-tiny configs
labels_path = "coco.names"
configs_path = "yolov3-tiny.cfg"
weights_path = "yolov3-tiny.weights"

# Thresholds
conf_threshold = 0.3
nms_threshold = 0.1

# DynamoDB boto3 client
ddb = boto3.resource('dynamodb')
ddb_table_name = "images"
table = ddb.Table(ddb_table_name)

# Images S3 prefix
images_prefix = "images"
thumbnails_prefix = "thumbnails"

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

    print("Loading YOLO object detector ...")
    net = cv2.dnn.readNetFromDarknet(config_path, weights_path)
    return net

def predict(image, net, labels):
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
    print("YOLO took {:.6f} seconds".format(end - start))

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
    tags = list()
    
    # Ensure at least one detection exists
    if len(idxs) > 0:
        # Loop over the indexes we are keeping
        # Create object_list placeholder list
        objects_list = list()
        for i in idxs.flatten():

            # Retain tags with greater than 0.6 confidence
            if confidences[i] > 0.6:
                tags.append(labels[class_ids[i]])
            
    return tags

def resolve_tags(tag):
    """
    Resolve tag string to tags and count

    Parameters
    ----------
    :param tag: tag string to resolve

    Returns
    -------
    :return tag, count
    """

    tags = tag.split(",")
    if len(tags) == 1:
        return tags[0].strip(), 1
    else:
        return tags[0].strip(), int(tags[1].strip())

# Get YOLO configs
lables = get_labels(labels_path)
configs = get_config(configs_path)
weights = get_weights(weights_path)

def run(event, _):
    """
    A lambda function to detect objects in a given image
    and search for images based on tags
    """
    
    empty_request = False
    image_urls = list()
    response_body = dict()
    response = dict()
    response["statusCode"] = 200

    try: 

        user_id = event['requestContext']['authorizer']['claims']['cognito:username']
        request_body = eval(event['body'])
    
        if "image" not in request_body:
            response_body["message"] = "Key 'image' is missing in request."
            response["body"] = response_body.__str__()
            return response
    
        # Check for empty image in request
        empty_request = len(request_body["image"]) == 0            
        if empty_request:
            response_body["message"] = "Empty input provided for image in request."
            response["body"] = response_body.__str__()
            return response
            
        # Convert base64 image string to OpenCV image
        print("Converting to OpenCV image")
        image = np.frombuffer(base64.b64decode(request_body["image"]), np.uint8)
        image = cv2.imdecode(image, flags = cv2.COLOR_BGR2RGB)
        
        # Load the neural net
        print("Loading model")
        nets = load_model(configs, weights)
        
        # Perform predictions
        print("Getting predictions")
        upload_image_tags = list(set(predict(image, nets, lables)))
        print(f"Unique tags in uploaded image: {upload_image_tags}")

        # Get all images records for the given user
        records = table.query(
            KeyConditionExpression = Key('user_id').eq(user_id)
        )
    
        print("Checking of matching thumbnail image urls")
        for record in records["Items"]:
            image_tags = list(record["tags"])
            for tag in image_tags:
                image_tag_name, image_tag_count = resolve_tags(tag)
                for upload_image_tag in upload_image_tags:
                    if upload_image_tag.strip() != "":
                        if upload_image_tag == image_tag_name:
                            image_urls.append(record["thumbnail_url"])
        
        print(f"Matching image thumbnail urls found: {image_urls}")
        if len(image_urls) != 0: 
            response_body["thumbnail_urls"] = image_urls
            response["body"] = response_body.__str__()
            return response
            
    except Exception as e:
        print(f"Failed to retrive images from uploaded image's tags: {e}")
        response["statusCode"] = 500
        response_body["message"] = f"Exception: {e}"
        response["body"] = response_body.__str__()
    
    response_body["message"] = "No images available for uploaded image's tags."
    response["body"] = response_body.__str__()
    
    return response