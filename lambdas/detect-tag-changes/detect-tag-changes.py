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
                    Message = f"Hello there! New image has been uploaded for the tags: {tags_str}. Image URL is: {img_url}",
                    Subject = f"New image added for {tags_str} tags",
                    MessageAttributes={
                        'email_id': {
                            'DataType': 'String',
                            'StringValue': user_email
                        }
                    }
                )
            
        elif event_name == "MODIFY":
        
            deleted_tags = list()
            updated_tags = list()
            old_image = event["Records"][0]["dynamodb"]["OldImage"]
            new_image = event["Records"][0]["dynamodb"]["NewImage"]
            
            old_tags_raw = old_image["tags"]["SS"]
            new_tags_raw = new_image["tags"]["SS"]
        
            deleted_tags_raw = list(set(old_tags_raw) - set(new_tags_raw))
            updated_tags_raw = list(set(new_tags_raw) - set(old_tags_raw))
        
            for d_tag in deleted_tags_raw:
                d_tag_name, d_tag_count = resolve_tags(d_tag)
                if d_tag_name in subscribed_tags:
                    deleted_tags.append(d_tag_name)
                    
            for u_tag in updated_tags_raw:
                u_tag_name, u_tag_count = resolve_tags(u_tag)
                if u_tag_name in subscribed_tags:
                    updated_tags.append(u_tag_name)
        
            updated_tags.extend(deleted_tags)
            changed_tags = list(set(updated_tags))
            
            if len(changed_tags) != 0:
                print("Publishing email for updated image add.")
                tags_str = ", ".join(changed_tags)
                img_url = event["Records"][0]["dynamodb"]["NewImage"]["image_url"]["S"]
                response = sns.publish(
                    TargetArn = topic_arn,
                    Message = f"Hello there! Image has been updated for the tags: {tags_str}. Image URL is: {img_url}",
                    Subject = f"Image updated for {tags_str} tags",
                    MessageAttributes={
                        'email_id': {
                            'DataType': 'String',
                            'StringValue': user_email
                        }
                    }
                )
        
        response_body["message"] = f"Tag change detected successfully!"
        response["body"] = response_body.__str__()
        return response
        
    except Exception as e:
        print(f"Failed to detect changes in tags: {e}")
        response["statusCode"] = 500
        response_body["message"] = f"Exception: {e}"
        response["body"] = response_body.__str__()
    
    response_body["message"] = "No tag changes detected for given thumbnail url."
    response["body"] = response_body.__str__()

    return response