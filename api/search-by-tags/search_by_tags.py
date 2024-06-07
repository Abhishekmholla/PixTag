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

    empty_tags = False
    image_urls = list()
    response_body = dict()
    response = dict()
    response["statusCode"] = 200

    try: 

        user_id = event['requestContext']['authorizer']['claims']['cognito:username']
        request_body = eval(event['body'])
    
        if "tags" not in request_body:
            response_body["message"] = "Key 'tags' is missing in request."
            response["body"] = response_body.__str__()
            return response
    
        print(f"Searching by tags: {request_body['tags']}")
        empty_tags = len(request_body['tags']) == 0
    
        # Check for empty tags in request
        count = 0
        for tag in request_body['tags']:
            if tag.strip() == "":
                count += 1
        
        if(count == len(request_body['tags'])):
            empty_tags = True
            
        if empty_tags:
            response_body["message"] = "List of request tags is empty."
            response["body"] = response_body.__str__()
            return response
            
        # Get all images records for an user
        records = table.query(
            KeyConditionExpression = Key('user_id').eq(user_id)
        )
    
        for record in records["Items"]:
            image_tags = list(record["tags"])
            for tag in image_tags:
                image_tag_name, image_tag_count = resolve_tags(tag)
                for request_tags in list(request_body["tags"]):
                    if request_tags.strip() != "":
                        request_tag_name, request_tag_count = resolve_tags(request_tags)
                        if (request_tag_name == image_tag_name) & (image_tag_count >= request_tag_count):
                            image_urls.append(record["thumbnail_url"])
        
        if len(image_urls) != 0: 
            response_body["links"] = image_urls
            response["body"] = response_body.__str__()
            return response
        
    except Exception as e:
        print(f"Failed to retrive images from given tags: {e}")
        response["statusCode"] = 500
        response_body["message"] = f"Exception: {e}"
        response["body"] = response_body.__str__()
    
    response_body["message"] = "No images available for given tags."
    response["body"] = response_body.__str__()

    return response