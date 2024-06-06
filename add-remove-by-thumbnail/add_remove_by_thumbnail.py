import boto3
from boto3.dynamodb.conditions import Key

# DynamoDB boto3 client
ddb = boto3.resource('dynamodb')
ddb_table_name = "images"
table = ddb.Table(ddb_table_name)

def update_ddb(user_id, thumbnail_url, current_tags):
    '''
    This function is to update the dynamodb table
    '''
    
    # Updating the dynamodb table
    update_response = table.update_item(
        Key={
                "user_id":user_id,
                'thumbnail_url':thumbnail_url
            },
            UpdateExpression='SET tags = :val',
               ExpressionAttributeValues={
                    ':val': current_tags
            },
            ReturnValues="UPDATED_NEW"
        )

    # returning true on postive update
    return (True,f"Records updated successfully for the user with user_id {user_id} and thumbnail_url:{thumbnail_url}")
        
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

    
def update_tag_by_thumbnail(user_id, request_body):
    '''
    This function handles the update and delete of the tags for a thumbnail
    '''
    
    # For all the thumbnail urls in the request body
    for thumbnail_url in request_body['url']:

        # Fetching the records for the user, thumbnail_url combination
        records = get_records(user_id, thumbnail_url)
        
        # If no records found, returning and error
        if records["Count"] == 0:
            return (False,f"No records found for the user with user_id: {user_id} and thumbnail url: {thumbnail_url}")
        
        # Fetching the existing tags for the image
        current_tags = records['Items'][0]['tags'] 
        
        # If the request is deletion and the tag requested does not exist as the current tag list then returning error
        if request_body['type'] == 0 and not set(request_body['tags']).issubset(current_tags):
            return (False,f"Tag: {set(request_body['tags'])} requested for deletion not found for the thumbnail_url: {thumbnail_url}")
        
        # Validating if trying to delete all the tags related to the image
        validation_status = validate_request_for_deletion(request_body,current_tags)
        
        # If trying to remove all tags, sending error message
        if not validation_status[0]:
            return validation_status
        
        # If the type is 1 then it is addition of tags else it is deletion of tags 
        if request_body['type'] == 1:
            # Updating the current_tags set
            current_tags.update(request_body['tags'])
        elif request_body['type'] == 0:
            # Updating the current_tags set
            for tag in request_body['tags']:
                current_tags.discard(tag)

        # Updating the dynamodb   
        return update_ddb(user_id, thumbnail_url, current_tags)

def validate_request_for_deletion(request_body, current_tags):
    '''
    This function handles the delete all tags scenario for the image 
    '''
    # If the user is requesting to delete all tags related to the image, send error message 
    if (request_body['type'] == 0) and len(current_tags) == len(request_body['tags']):
        return (False,f"The current tags:{current_tags} and requested_tag: {request_body['tags']} for deletion are identical, cannot delete all tags related to the image")
    
    return (True,f"The current tags:{current_tags} and requested_tag: {request_body['tags']} for deletion are identical")
    
def run(event, _):
    """
    This function adds and removes tags for images
    """

    try:

        # user_id = event['requestContext']['authorizer']['claims']['cognito:username']
        user_id = "44d8f4a8-10d1-7091-d357-8b5442f9ce4e"
        
        # Fetching the request bidy
        request_body = eval(event['body'])
        message = ""
        result_message = ""
        if request_body['type'] == 1:
            # Updating the dynamodb 
            _, result_message = update_tag_by_thumbnail(user_id,request_body)
            message = result_message
        elif request_body['type'] == 0:
            # Updating the dynamodb 
            _, result_message= update_tag_by_thumbnail(user_id,request_body)
            message =result_message
        return send_response(200,message)
    except Exception as e:
        # Logging the error and returning the response
        print(f"Failed to add-remove tags for the image for the given thumbnail url: {e}")
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