import boto3
from boto3.dynamodb.conditions import Key

# DynamoDB boto3 client
ddb = boto3.resource('dynamodb')
ddb_subs_table_name = "usertagsubscription"
subs_table = ddb.Table(ddb_subs_table_name)

# SNS boto3 client
sns = boto3.client('sns')
topic_arn = "arn:aws:sns:us-east-1:327379801351:tag-email-notification"

# Cognito client
cognito_client = boto3.client('cognito-idp', region_name="us-east-1")
user_pool_id = "us-east-1_jcJBx2Erg"

def get_user_email_from_user_id(user_id):
    """
    Get user email from user id

    Parameters
    ----------
    :param user_id: user id

    Returns
    -------
    :return user email
    """
    
    response = cognito_client.admin_get_user(
            UserPoolId=user_pool_id,
            Username=user_id
    )
    for attribute in response['UserAttributes']:
        if attribute['Name'] == 'email':
            return attribute['Value']

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

def run(event, context):
    """
    Lambda function to detect changes in image's tags
    """
    
    subscription_arn = ""
    response_body = dict()
    response = dict()
    response["statusCode"] = 200

    try:
        
        print(event)
        event_name = event["Records"][0]["eventName"]
        user_id = event["Records"][0]["dynamodb"]["NewImage"]["user_id"]["S"]
        
        print(f"Get subscribed tags for given user: {user_id}")
        
        # Get subscribed tags for given user_id
        records = subs_table.query(
            KeyConditionExpression = Key('user_id').eq(user_id)
        )
        
        if len(records["Items"]) == 0:
            response_body["message"] = f"No tags subscribed for the given user_id: {user_id}"
            response["body"] = response_body.__str__()
            return response
    
        subscribed_tags = list(records["Items"][0]["subscribed_tags"])
        
        print("Get list of subscriptions for given SNS topic.")
        list_subs = sns.list_subscriptions_by_topic(TopicArn = topic_arn)
        
        if "Subscriptions" not in list_subs or len(list_subs["Subscriptions"]) == 0:
            response_body["message"] = f"No subscriptions found for given topic_arn."
            response["body"] = response_body.__str__()
            return response
            
        user_email = get_user_email_from_user_id(user_id)
        
        for subscription in list_subs["Subscriptions"]:
            if subscription["Endpoint"] == user_email:
                print(subscription)
                subscription_arn = subscription["SubscriptionArn"]
        
        if subscription_arn == "":
            print("No tags are subscribed for the current logged in user.")
            response_body["message"] = "No tags are subscribed for the current logged in user."
            response["body"] = response_body.__str__()
            return response
        
        if event_name == "INSERT":
            
            tags_list = list()
            new_image = event["Records"][0]["dynamodb"]["NewImage"]
            new_tags_raw = new_image["tags"]["SS"]
            
            for tag in new_tags_raw:
                tag_name, _ = resolve_tags(tag)
                if tag_name in subscribed_tags:
                    tags_list.append(tag_name)
            
            if len(tags_list) != 0:
                print("Publishing email for new image add.")
                tags_str = ", ".join(tags_list)
                img_url = event["Records"][0]["dynamodb"]["NewImage"]["image_url"]["S"]
                response = sns.publish(
                    TargetArn = topic_arn,
                    Message = f"Hello there! New image as been uploaded for the tags: {tags_str}. Image URL is: {img_url}",
                    Subject = f"New image added for {tags_str} tags",
                    MessageAttributes={
                        'email_id': {
                            'DataType': 'String',
                            'StringValue': user_email
                        }
                    }
                )
            
        elif event_name == "MODIFY":
        
            old_image = event["Records"][0]["dynamodb"]["OldImage"]
            new_image = event["Records"][0]["dynamodb"]["NewImage"]
            
            old_tags_raw = old_image["tags"]["SS"]
            new_tags_raw = new_image["tags"]["SS"]
        
            for new_tag in new_tags_raw:
                n_tag_name, n_tag_count = resolve_tags(new_tag)
                for old_tag in old_tags_raw:
                    o_tag_name, o_tag_count = resolve_tags(old_tag)
                    if n_tag_name == o_tag_name and n_tag_name in subscribed_tags:
                        tags_list.append(tag_name)
        
        response_body["message"] = f"Tag change detected successfully!"
        response["body"] = response_body.__str__()
        return response
        
    except Exception as e:
        print(f"Failed to detect changes in tags: {e}")
        response["statusCode"] = 500
        response_body["message"] = f"Exception: {e}"
        response["body"] = response_body.__str__()
    
    response_body["message"] = "No images available for given thumbnail url."
    response["body"] = response_body.__str__()

    return response