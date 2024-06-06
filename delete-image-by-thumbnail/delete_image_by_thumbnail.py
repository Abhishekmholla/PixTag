import boto3
from boto3.dynamodb.conditions import Key

# S3 boto3 client
s3 = boto3.client('s3')

# DynamoDB boto3 client
ddb = boto3.resource('dynamodb')
ddb_table_name = "images"
table = ddb.Table(ddb_table_name)

def get_records(user_id, thumbnail_url):
    '''
    This function is to fetch the records related to the user and thumbnail user provided
    '''
    # Fetching the records for the current user and thumbnail_url
    records = table.query(
            KeyConditionExpression = Key('user_id').eq(user_id) & Key('thumbnail_url').eq(thumbnail_url)
        )
    
    # returning the records fetched  
    return records

def get_bucketname_and_key(image_url):
    '''
    This function fetches the bucketname and key for deletion from the image url
    '''
    # Split the url into parts
    url_parts = image_url.replace("s3://", "").split("/", 1)
    # Fetch the bucket name and key
    bucket_name = url_parts[0]
    key = url_parts[1]
    return (bucket_name, key)

def delete_object_from_s3(bucket_name, key):
    '''
    Function to delete files from the bucket
    '''
    # Deleting the files from the s3 bucket
    s3.delete_object(Bucket=bucket_name, Key=key)

def delete_record_from_ddb(user_id, thumbnail_url):
    '''
    Function to delete record from the dynamodb
    '''
    table.delete_item(
        Key={
            'user_id': user_id,
            'thumbnail_url': thumbnail_url
        }
    )

def run(event, _):
    """
    This function deletes images based on the thumbnail url
    """
    
    try:
        # user_id = event['requestContext']['authorizer']['claims']['cognito:username']
        user_id = "bd4b7a2c-7bd1-427f-8655-936872fe0fe4"
        request_body = eval(event['body'])

        # For all the urls in the request body
        for thumbnail_url in request_body['url']:
            
            # Fetching the record details from the dynamodb
            records = get_records(user_id, thumbnail_url)
            
            # Returning an error message if no records found
            if records["Count"] == 0:
                message = f"No records found for the user with user_id: {user_id} and thumbnail url: {thumbnail_url}"
                return send_response(500,message)
            
            # Fetching the image and thumbnail url
            image_url = records['Items'][0]['image_url']     
            thumbnail_url = records['Items'][0]['thumbnail_url']  
            
            # Fetching the bucket name and key for deletion
            bucket_name, image_key = get_bucketname_and_key(image_url)
            _, thumbnail_key = get_bucketname_and_key(thumbnail_url)
            
            # Deleting object from S3 thumbnails
            delete_object_from_s3(bucket_name, thumbnail_key)
            
            # Deleting from S3 images
            delete_object_from_s3(bucket_name, image_key)
             
            # Delete record from dynamodb
            delete_record_from_ddb(user_id, thumbnail_url)
            
        message =  f"Records deleted successfully for the user with user_id {user_id} and thumbnail_url:{request_body['url']}"
        return send_response(200,message)
        
    except Exception as e:
        print(f"Failed to delete images for the given thumbnail urls: {e}")
        return send_response(500,f"Exception: {e}")
    
def send_response(status_code, message):
    '''
    A generic function to handle the response body
    '''
    response_body = dict()
    response = dict()
    response_body["message"]  = message
    response["statusCode"] = status_code
    response["body"] = response_body.__str__()
    return response