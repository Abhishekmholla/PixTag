import cv2
import boto3
import numpy as np
import urllib.parse

# S3 boto3 client
s3 = boto3.client('s3')

# Thumbnail prefix in S3
thumbnail_prefix = "thumbnails"

def run(event, _):
    """
    This function creates a thumbnail from given image

    Parameters
    ----------
    :param image: opencv image

    Returns
    -------
    :return a resized image
    """

    # Resolve S3 image upload event parameters
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(event["Records"][0]["s3"]["object"]["key"], encoding = "utf-8")

    # Get image S3 object
    image_object = s3.get_object(Bucket = bucket, Key = key)

    try: 
        
        # Resolving user_id
        user_id = key.split("/")[-2]
    
        # Read image
        print("Reading image to opencv")
        image = cv2.imdecode(np.asarray(bytearray(image_object['Body'].read())), cv2.IMREAD_COLOR)

        # Defining thumbnail size and dimensions
        thumbnail_px = 150
        (height, width) = image.shape[:2]

        # If height is greater than width, resize image
        # proportionally by height, else by width
        if height >= width:
            ratio = thumbnail_px / float(height)
            image_dimensions = (int(width * ratio), thumbnail_px)
        else:
            ratio = thumbnail_px / float(width)
            image_dimensions = (thumbnail_px, int(height * ratio))

        # Resize the image
        print("Resizing image")
        resized_image = cv2.resize(image, image_dimensions, interpolation = cv2.INTER_AREA)

        # Write thumbnail image to S3 bucket
        print(f"Writing image to bucket: {bucket}")
        
        image_string = cv2.imencode('.jpg', resized_image, [cv2.IMWRITE_JPEG_QUALITY, 90])[1].tostring()
        s3.put_object(
            Bucket=bucket,
            Key=f"{thumbnail_prefix}/{user_id}/{key.split('/')[-1]}",
            Body=image_string
        )
        
        print(f"Image written to bucket successfully: s3://{bucket}/{thumbnail_prefix}/{key.split('/')[-1]}")
    
    except Exception as e:
        print(f"Image write failed with exception: {e}")
