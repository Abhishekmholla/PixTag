import boto3
from boto3.dynamodb.conditions import Key


# DynamoDB boto3 client
ddb = boto3.resource('dynamodb')
ddb_table_name = "images"
table = ddb.Table(ddb_table_name)

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

def run(event, _):
    """
    This function searches for images based on tags
    """

    empty_request = False
    response_body = dict()
    response = dict()
    response["statusCode"] = 200

    try: 

        user_id = event['requestContext']['authorizer']['claims']['cognito:username']
        request_body = eval(event['body'])
    
        if "thumbnail_url" not in request_body:
            response_body["message"] = "Key 'thumbnail_url' is missing in request."
            response["body"] = response_body.__str__()
            return response

        print(f"Searching by thumbnail url: {request_body['thumbnail_url']}")
        empty_request = request_body['thumbnail_url'].strip() == ""
    
        # Check for empty url in request
        if empty_request:
            response_body["message"] = "Invalid thumbnail url provided in request."
            response["body"] = response_body.__str__()
            return response
            
        # Get all images records for an user
        records = table.query(
            KeyConditionExpression = Key('user_id').eq(user_id) & Key('thumbnail_url').eq(request_body['thumbnail_url'])
        )
        print(f"Retrieved records: {records['Items']}")

        if records["Count"] != 0:
            image_url = records["Items"][0]["image_url"]
            print(f"Found image url: {image_url}")
            
            response_body["image_url"] = image_url
            response["body"] = response_body.__str__()
            return response
        else:
            response_body["message"] = f"No record found for given user_id: {user_id} and thumbnail_url: {request_body['thumbnail_url']}"
            response["body"] = response_body.__str__()
            return response
        
    except Exception as e:
        print(f"Failed to retrive images from given thumbnail url: {e}")
        response["statusCode"] = 500
        response_body["message"] = f"Exception: {e}"
        response["body"] = response_body.__str__()
    
    response_body["message"] = "No images available for given thumbnail url."
    response["body"] = response_body.__str__()

    return response
