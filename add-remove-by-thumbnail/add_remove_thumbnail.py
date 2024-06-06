import boto3
from boto3.dynamodb.conditions import Key


# DynamoDB boto3 client
ddb = boto3.resource('dynamodb')
ddb_table_name = "images"
table = ddb.Table(ddb_table_name)

def update_ddb(user_id, thumbnail_url, current_tags):
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

    return (True,f"Records updated successfully for the user with user_id {user_id} and thumbnail_url:{thumbnail_url}")
        
def get_records(user_id, thumbnail_url):
    records = table.query(
            KeyConditionExpression = Key('user_id').eq(user_id) & Key('thumbnail_url').eq(thumbnail_url)
        )
        
    return records

    
def update_tag_by_thumbnail(user_id, request_body):
    for thumbnail_url in request_body['url']:
      
        records = get_records(user_id, thumbnail_url)
        
        
        if records["Count"] == 0:
            return (False,f"No records found for the user with user_id: {user_id} and thumbnail url: {thumbnail_url}")
            
        current_tags = records['Items'][0]['tags'] 
        
        
        if request_body['type'] == 0 and not set(request_body['tags']).issubset(current_tags):
            return (False,f"Tag: {set(request_body['tags'])} requested for deletion not found for the thumbnail_url: {thumbnail_url}")
        
        validation_status = validate_request_for_deletion(request_body,current_tags)
        
        if not validation_status[0]:
            return validation_status
            
        if request_body['type'] == 1:
            print("UPDATING")
            current_tags.update(request_body['tags'])
        elif request_body['type'] == 0:
            for tag in request_body['tags']:
                current_tags.discard(tag)

                
        return update_ddb(user_id, thumbnail_url, current_tags)

def validate_request_for_deletion(request_body, current_tags):
    if (request_body['type'] == 0) and len(current_tags) == len(request_body['tags']):
        return (False,f"The current tags:{current_tags} and requested_tag: {request_body['tags']} for deletion are identical, cannot delete all tags related to the image")
    
    return (True,f"The current tags:{current_tags} and requested_tag: {request_body['tags']} for deletion are identical")
    
def run(event, _):
    """
    This function adds and removes tags searches for images based on tags
    """

    try:

        # user_id = event['requestContext']['authorizer']['claims']['cognito:username']
        user_id = "44d8f4a8-10d1-7091-d357-8b5442f9ce4e"
        request_body = eval(event['body'])
        message = ""
        result_message = ""
        if request_body['type'] == 1:
            result, result_message = update_tag_by_thumbnail(user_id,request_body)
            message = result_message
        elif request_body['type'] == 0:
            result, result_message= update_tag_by_thumbnail(user_id,request_body)
            message =result_message
        return send_response(200,message)

    except Exception as e:
        print(f"Failed to add-remove tags for the image for the given thumbnail url: {e}")
        return send_response(500,f"Exception: {e}")
    
    
def send_response(status_code, message):
    response_body = dict()
    response = dict()
    response_body["message"]  = message
    response["statusCode"] = status_code
    response["body"] = response_body.__str__()
    return response