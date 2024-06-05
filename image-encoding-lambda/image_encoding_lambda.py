import boto3
import base64

# S3 boto3 client
s3 = boto3.client('s3')

def run(event, _):
    """
    A lambda function to encode images to base64 string
    """
    
    images_dict = dict()
    response_body = dict()
    response = dict()
    response["statusCode"] = 200

    try: 
        
        request_body = eval(event['body'])

        # Resolve S3 image upload event parameters
        bucket = request_body["bucket_name"]

        for key in request_body["keys"]:
        
            # Get S3 object
            image_object = s3.get_object(Bucket = bucket, Key = key)

            # Encode image to base64 string
            image_base64_str = base64.b64encode(image_object['Body'].read())

            # Add to dictionary
            images_dict[key] = image_base64_str
        
        response_body["images"] = images_dict
        response["body"] = response_body.__str__()
        return response

    except Exception as e:
        print(f"Exception: {e}")
        response["statusCode"] = 500
        response_body["message"] = f"Exception: {e}"
        response["body"] = response_body.__str__()
