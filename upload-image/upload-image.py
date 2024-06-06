
    import boto3
    import base64
    import uuid

    # Creating a s3 boto3 client
    s3 = boto3.client('s3')

    # Hardcoding the bucket name
    bucket_name = "g74-a3"
    object_folder_mapper = {
        "image" : "images",
        "thumbnail" : "thumbnails"
    }

    def upload_image_to_s3(object_name, image_data):
        '''
        Function to upload file to s3
        '''
        # Uploading file to s3
        s3.put_object(Bucket=bucket_name, Key=object_name, Body=image_data, ContentType='image/jpeg')
        
    def run(event, _):
        
        try:
            # user_id = event['requestContext']['authorizer']['claims']['cognito:username']
            user_id = "bd4b7a2c-7bd1-427f-8655-936872fe0fe4"
            
            #NEEDED
            # request_body = eval(event['body'])
            
            request_body = event
            file_name = request_body['file_name']
            
            if 'image' not in request_body or request_body['image'] is None or request_body['image'] == '':
                return send_response(500,f"Image as string needed to upload to the s3 bucket for the user with user_id {user_id}")
            
            if 'file_name' not in request_body or request_body['file_name'] is None or request_body['file_name'] == '':
                file_name = f"{str(uuid.uuid4())}.jpg"
            
            
            # If the image is not a thumbnail, upload it into image folder else into thumbnails
            if not request_body['is_thumbnail']:
                object_name = f"{object_folder_mapper['image']}/{user_id}/{file_name}"
            else:
                object_name = f"{object_folder_mapper['image']}/{user_id}/{file_name}"
            
            # Decoding the base64 image
            image_data  = base64.b64decode(request_body['image'])
            
            # Uploading to S3 bucket
            upload_image_to_s3(object_name,image_data)
            return send_response(200,f"Image uploaded successfully for the user with user_id {user_id}")
        except Exception as e:
            print(f"Failed to delete images for the given thumbnail urls: {e}")
            return send_response(500,f"Exception: {e}")

    def send_response(status_code, message):
        response_body = dict()
        response = dict()
        response_body["message"]  = message
        response["statusCode"] = status_code
        response["body"] = response_body.__str__()
        return response